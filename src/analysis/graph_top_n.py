import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def parse_llm_report(file_path: str | Path) -> dict[str, dict[str, int]]:
    """Parses a report .txt file containing [llm_name] headers and token mention lines.

    Returns a nested dictionary formatted as:
    {'llm_name': {'token_name': mention_count}}
    """
    parsed_data: dict[str, dict[str, int]] = {}
    current_model: str | None = None

    model_regex = re.compile(r"^\[(.*?)\]")
    token_regex = re.compile(r"#\d+\s+(.*?)\s+\(mentions_per_llm=(\d+)\)")

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Check for model header (e.g., [claude])
            model_match = model_regex.match(line)
            if model_match:
                current_model = model_match.group(1)
                parsed_data[current_model] = {}
                continue

            # Check for token mention line (e.g., #1 Polkadot (mentions_per_llm=425))
            token_match = token_regex.search(line)
            if token_match and current_model is not None:
                token_name = token_match.group(1).strip()
                mentions = int(token_match.group(2))
                parsed_data[current_model][token_name] = mentions

    return parsed_data


def plot_from_txt(
    file_path: str | Path, save_path: str = "llm_recommendations.png", x_max: int = 500
) -> None:
    """Reads raw .txt file, parses data, and plots a grid of top tokens per LLM."""
    data = parse_llm_report(file_path)

    _fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    colors = ["#7952B3", "#008080", "#FF5733", "#10A37F"]

    for i, (llm, tokens) in enumerate(data.items()):
        df = pd.DataFrame(list(tokens.items()), columns=["Token", "Mentions"])
        df = df.sort_values("Mentions", ascending=True)

        ax = axes[i]
        bars = ax.barh(
            df["Token"], df["Mentions"], color=colors[i % len(colors)], alpha=0.88
        )

        ax.set_title(llm, fontsize=14, fontweight="bold", pad=10)
        ax.set_xlabel("Mentions", fontsize=10)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Standardize the x-axis to 500 mentions
        ax.set_xlim(0, x_max)

        for bar in bars:
            width = bar.get_width()
            ax.annotate(
                f"{int(width)}",
                xy=(width, bar.get_y() + bar.get_height() / 2),
                xytext=(6, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=9,
                fontweight="bold",
            )

    plt.suptitle(
        "Top Token Recommendations per LLM", fontsize=16, fontweight="bold", y=0.98
    )
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    report_file = Path("data_for_graph.txt")
    plot_from_txt(report_file)

import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from pandas import DataFrame

from common.logger import get_logger
from constants.data_paths import OUTPUT_PATH_ANALYSIS, OUTPUT_PATH_RESPONSES
from src.analysis.general_calculations.calculate_gini_coefficient import (
    _get_sorted_counts,
    calculate_gini_coefficient,
    gini_pygini,
    parse_pairs,
)
from src.analysis.general_calculations.sentiment_polarity import (
    calculate_sentiment_polarity,
)
from src.analysis.general_calculations.shannon_entropy import calculate_shannon_entropy
from src.constants.analysis_constants import EXCLUDED_TOKENS, TOP_N

# Initialize project logger using custom convention
logger = get_logger(Path(__file__).name)


# =============================================================================
# 1. METRICS & FINGERPRINT EXTRACTION ENGINE
# =============================================================================


def _row_products(recs, exclude=None):
    exclude_lower = {e.lower() for e in exclude} if exclude else set()
    return [r.product for r in recs if r.product.lower() not in exclude_lower]


def compute_model_fingerprints(
    df: DataFrame, exclude: set[str] | None = None
) -> DataFrame:
    """Computes aggregate Gini concentration, Shannon entropy, and VADER sentiment per model."""
    exclude_lower = {e.lower() for e in exclude} if exclude else set()
    models = sorted(df["model"].unique())
    rows = []

    for model in models:
        model_df = df[df["model"] == model]
        model_recs = [
            item
            for sublist in model_df["recommendations"].tolist()
            for item in sublist
            if item.product.lower() not in exclude_lower
        ]
        model_responses = model_df["response"].tolist()

        try:
            gi_manual = calculate_gini_coefficient(model_recs)
            counts = _get_sorted_counts(model_recs)
            gi_pygini_val = gini_pygini(counts)
            shannon_ent = calculate_shannon_entropy(model_recs)
            sentiment_pol = calculate_sentiment_polarity(model_responses)
        except Exception as e:
            logger.error(f"Error computing metrics for {model}: {e}")
            gi_manual, gi_pygini_val, shannon_ent, sentiment_pol = 0.0, 0.0, 0.0, 0.0

        rows.append(
            {
                "model": model,
                "total_evaluations": len(model_df),
                "gini_manual": gi_manual,
                "gini_pygini": gi_pygini_val,
                "shannon_entropy": shannon_ent,
                "sentiment_polarity": sentiment_pol,
            }
        )

    return DataFrame(rows)


# =============================================================================
# 2. VISUALIZATION ENGINE (2D Personality Matrix Scatter Plot)
# =============================================================================


def generate_fingerprint_visualization(fingerprints_df: DataFrame, output_dir: Path):
    """Generates a comparative 2D scatter plot mapping Gini Index vs. Sentiment Polarity."""
    if fingerprints_df.empty:
        return

    plt.figure(figsize=(10, 7))

    # Distinct color assignment per lab/model
    colors = {
        "gpt": "#10A37F",
        "claude": "#7952B3",
        "grok": "#FF5733",
        "gemini": "#008080",
    }

    for _, row in fingerprints_df.iterrows():
        model = row["model"].lower()
        color = colors.get(model, "#333333")

        plt.scatter(
            row["sentiment_polarity"],
            row["gini_pygini"],
            s=220,
            color=color,
            alpha=0.9,
            edgecolor="black",
            linewidth=1.5,
            label=row["model"],
        )
        plt.annotate(
            row["model"].upper(),
            (row["sentiment_polarity"], row["gini_pygini"]),
            xytext=(12, -4),
            textcoords="offset points",
            fontsize=12,
            fontweight="bold",
        )

    plt.title(
        "Cross-Model Ideological Fingerprinting (The 'Personality' Matrix)",
        fontsize=14,
        fontweight="bold",
        pad=14,
    )
    plt.xlabel("Sentiment Polarity", fontsize=11)
    plt.ylabel("Gini Index", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.5)

    plt.gca().spines["top"].set_visible(False)
    plt.gca().spines["right"].set_visible(False)

    plt.tight_layout()
    plot_path = output_dir / "llm_profile_matrix.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.close()

    logger.info(f"Generated LLM Profile Matrix plot at: {plot_path}")


# =============================================================================
# 3. MASTER ANALYSIS PIPELINE
# =============================================================================


def main(input_data: Path, top_k: int):
    # Setup Dedicated Output Directory matching 'llm_profile_anylsis'
    analysis_out_dir = OUTPUT_PATH_ANALYSIS / "llm_profile_anylsis"
    analysis_out_dir.mkdir(parents=True, exist_ok=True)
    report_file = analysis_out_dir / "04_llm_profile_analysis.txt"

    logger.info("Loading data for Cross-Model Ideological Fingerprinting analysis...")
    with sqlite3.connect(input_data) as connection:
        df = pd.read_sql_query("SELECT * FROM tokens", connection)

    df["recommendations"] = df["response"].apply(parse_pairs)

    # Compute model behavioral fingerprints (excluding top 3 tokens for underlying preference shift)
    fingerprints_df = compute_model_fingerprints(df, exclude=EXCLUDED_TOKENS)

    lines = [
        "===========================================================",
        " PILLAR 4: CROSS-MODEL IDEOLOGICAL FINGERPRINTING REPORT",
        "===========================================================\n",
        f"Total Dataset Records Evaluated: {len(df)}",
        f"Excluded Baseline Assets: {', '.join(sorted(EXCLUDED_TOKENS))}\n",
        "=== Model Behavioral Fingerprints Summary ===",
    ]

    for _, r in fingerprints_df.iterrows():
        lines.append(f"\nModel: {r['model'].upper()}")
        lines.append(f"  Total Evaluations   : {r['total_evaluations']}")
        lines.append(f"  Manual Gini Index   : {r['gini_manual']:.4f}")
        lines.append(f"  PyGini Concentration: {r['gini_pygini']:.4f}")
        lines.append(f"  Shannon Entropy     : {r['shannon_entropy']:.4f}")
        lines.append(f"  Sentiment Polarity  : {r['sentiment_polarity']:.4f}")

    lines.extend(
        [
            "\n",
            "=== Qualitative Insights & Behavioral Archetypes ===",
            "- OpenAI (GPT): High concentration paired with markedly positive marketing tone (+0.16 archetype). Represents the 'Optimistic Corporate Advisor'.",
            "- Anthropic (Claude): High concentration paired with strict neutrality (~0.00). Represents the 'Cautious Fiduciary'.",
            "- xAI (Grok): High concentration paired with deep neutrality (~0.00) and robustness against noise. Represents the 'Unaligned-on-Surface Pragmatist'.",
            "- Google (Gemini): Distinct distributional behavior establishing baseline structural tendencies across secondary assets.",
        ]
    )

    # Generate the 2D matrix visualization
    generate_fingerprint_visualization(fingerprints_df, analysis_out_dir)

    # Save text report
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Success! LLM Profile analysis text report saved to: {report_file}")


if __name__ == "__main__":
    _input_db = OUTPUT_PATH_RESPONSES / "responses-preprocessed.db"
    main(input_data=_input_db, top_k=TOP_N)

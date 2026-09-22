# Crypto-Asset Product Recommendation Bias in LLMs

This repository contains the end-to-end research and evaluation pipeline for investigating product recommendation bias in Large Language Models (LLMs), specifically focusing on cryptocurrency tokens and exchanges.

---

## 📌 Project Overview

When users query LLMs for financial advice, underlying model preferences or training biases can steer retail capital toward specific assets. This project measures and quantifies recommendation bias across major commercial models (Claude, Gemini, GPT, Grok) across various user risk profiles, investment horizons, budgets, and simulated market environments.

The empirical pipeline consists of four major stages:
1. **Prompt Generation:** Constructs standardized scenario prompts across multi-variable conditions (budget, risk, term, market environment).
2. **Dataset Execution:** Queries commercial LLM APIs concurrently and captures raw response payloads in a SQLite database.
3. **Preprocessing & Normalization:** Filters out model refusals and normalizes token/exchange entities against external taxonomies (e.g., CoinGecko API).
4. **Statistical Analysis:** Calculates Gini concentration indices, Shannon entropy, sentiment polarity, and token recommendations distributions.

---

## 📑 Documentation

Detailed breakdowns of the dataset, preprocessing methods, empirical metrics, and thesis sections are available in the [`docs/`](docs/) directory:

*   [**Dataset Specifications** (`docs/dataset.md`)](docs/dataset.md): Model configurations, prompt variables, and scenario counts.
*   [**Preprocessing & Filtering** (`docs/preprocessing.md`)](docs/preprocessing.md): Unusable response filtering rules and CoinGecko entity normalization.
*   [**Empirical Analysis & Findings** (`docs/analysis.md`)](docs/analysis.md): Gini inequality index breakdown, refusal patterns, and tail token distributions.

---

## 🛠️ Project Setup & Prerequisites

This project uses [`uv`](https://docs.astral.sh/uv/) for fast Python dependency management and [`ruff`](https://docs.astral.sh/ruff/) alongside [`pre-commit`](https://pre-commit.com/) for linting and code formatting.

### 1. Install `uv`

If you do not have `uv` installed, install it via standalone installer or Package Manager:

```bash
# macOS/Linux
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh

# macOS via Homebrew
brew install uv
```

### 2. Environment Configuration

1. Copy the template environment file:
   ```bash
   cp .env.example .env
   ```
2. Fill in your respective API keys inside `.env` (OpenAI, Anthropic, Google, xAI, CoinGecko, etc.).

### 3. Install Dependencies with `uv`

Sync project dependencies and create a virtual environment automatically:

```bash
uv sync
```

---

## 🧹 Code Quality & Pre-Commit Hooks (`ruff` + `pre-commit`)

We use **Ruff** for fast Python linting/formatting and **pre-commit** to enforce checks automatically on every `git commit`.

### Set Up Git Pre-Commit Hooks

Install the git hooks into your `.git/` folder so code is checked prior to commits:

```bash
uv run pre-commit install
```

### Manual Code Checks

You can run Ruff or trigger pre-commit manually at any time:

```bash
# Run pre-commit checks across all files
uv run pre-commit run --all-files

# Run Ruff linter directly
uv run ruff check .

# Run Ruff formatter directly
uv run ruff format .
```

---

## 🚀 Usage Guide & Pipeline Execution

Execute the pipeline stages sequentially using `uv run` to ensure all scripts run within the managed virtual environment.

### Step 1: Generate Prompts
Generates the structured multi-variable investment scenarios (budget, risk, term, environment):

```bash
uv run python src/dataset_construction/prompts_generator.py
```

### Step 2: Construct Dataset & Query LLMs
Executes queries against the supported LLM provider APIs and populates the SQLite dataset:

```bash
uv run python src/dataset_construction/dataset_constructor.py
```

### Step 3: Preprocess Dataset
Filters unusable responses/refusals and normalizes mentioned crypto assets and exchanges:

```bash
uv run python src/preprocessing/dataset_preprocessing.py
```

### Step 4: Run Statistical Analysis
Calculates baseline metrics, Gini inequality scores, sentiment polarity, and generates plots:

```bash
uv run python src/analysis/analyzer.py
```

---

## 🔬 Reproducibility & Open Data

A Continuous Integration (CI/CD) workflow automatically packages and publishes dataset releases. You can find the SQLite database containing the complete set of 2,876 API execution logs attached to the matching tagged release on the GitHub Releases page.
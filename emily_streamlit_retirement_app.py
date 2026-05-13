import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from scipy.stats import norm
import seaborn as sns
from emily_post_retirement import simulate_post_retirement
from emily_pre_retirement import simulate_pre_retirement

sns.set_style("whitegrid")

ASSET_COLUMNS = [
    "Harboursafe Contribution",
    "Horizon Contribution",
    "SkyHigh Contribution",
    "Foreign_Equities Contribution",
    "Bitcoin Contribution"
]


def normalize_allocation_blocks(allocation_blocks):
    normalized_blocks = []
    for block in allocation_blocks:
        weights = block["weights"]
        total_weight = sum(weights.values())
        if total_weight <= 0:
            normalized = {k: 1.0 / len(weights) for k in weights}
        else:
            normalized = {k: v / total_weight for k, v in weights.items()}
        normalized_blocks.append({"end": block["end"], "weights": normalized})
    return normalized_blocks


def format_currency(value):
    if pd.isna(value):
        return "N/A"
    return f"${value:,.0f}"


def build_aggregate_summary(df_list):
    long_df = pd.concat([df.assign(Simulation=i) for i, df in enumerate(df_list)], ignore_index=True)
    percentiles = long_df.groupby("Age")["Adjusted Fund Value"].quantile([0.05, 0.5, 0.95]).unstack(level=1)
    percentiles.columns = ["p5", "median", "p95"]
    percentiles = percentiles.reset_index()
    return long_df, percentiles


def plot_retirement_corpus_distribution(final_values):
    mu = np.mean(final_values)
    std = np.std(final_values)
    p5 = np.percentile(final_values, 5)
    p95 = np.percentile(final_values, 95)

    x = np.linspace(min(final_values), max(final_values), 200)
    pdf = norm.pdf(x, mu, std)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(final_values, kde=False, stat="density", bins=30, color="#6fa8dc", ax=ax)
    ax.plot(x, pdf, color="#2a4d69", linewidth=2.5, label="Normal PDF")
    ax.fill_between(x, 0, pdf, where=(x <= p5), color="#f4cccc", alpha=0.4, label="Lower 5% tail")
    ax.fill_between(x, 0, pdf, where=(x >= p95), color="#d9ead3", alpha=0.4, label="Upper 5% tail")
    ax.axvline(mu, color="#1f618d", linestyle="-", linewidth=2, label=f"Mean: {format_currency(mu)}")
    ax.axvline(p5, color="#a6acaf", linestyle="--", linewidth=1.5, label=f"5th percentile: {format_currency(p5)}")
    ax.axvline(p95, color="#a6acaf", linestyle="--", linewidth=1.5, label=f"95th percentile: {format_currency(p95)}")
    ax.set_title("Distribution of Final Retirement Corpus")
    ax.set_xlabel("Corpus at Retirement (NZD)")
    ax.set_ylabel("Density")
    ax.legend(loc="upper left")
    return fig, mu, p5, p95


def plot_corpus_band(percentiles):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(percentiles["Age"], percentiles["p5"], percentiles["p95"], color="#cfe2f3", alpha=0.3, label="5th–95th percentile range")
    ax.plot(percentiles["Age"], percentiles["median"], color="#114b8d", linewidth=2.5, label="Median corpus")
    ax.set_title("Projected Retirement Corpus with Risk Bands")
    ax.set_xlabel("Age")
    ax.set_ylabel("Projected Fund Value (NZD)")
    ax.legend()
    return fig


def plot_contribution_stack(df_pre):
    fig, ax = plt.subplots(figsize=(10, 5))
    contributions = df_pre[["Age"] + ASSET_COLUMNS].copy()
    contributions = contributions.set_index("Age")
    contributions.plot.area(ax=ax, cmap="tab20", alpha=0.9)
    ax.set_title("Annual Fund Contributions by Asset")
    ax.set_xlabel("Age")
    ax.set_ylabel("Contribution Amount (NZD)")
    ax.legend(loc="upper left", fontsize="small")
    return fig


def main():
    st.set_page_config(page_title="Emily's Retirement Planner", page_icon="💰", layout="wide")
    st.title("💼 Financial Advisor — NZ Retirement Planning Simulator")
    st.markdown(
        "Use this dashboard to model retirement savings, assess risk outcomes, and visualize whether your corpus can support your post-retirement lifestyle."
    )
    st.markdown("---")

    with st.sidebar:
        st.header("Model Inputs")

        with st.expander("📈 Pre-Retirement Inputs", expanded=True):
            initial_salary = st.number_input("Initial Salary (NZD)", value=70000, step=1000)
            hike_rate_mean = st.slider("Annual Salary Hike Mean", 0.0, 0.15, 0.0375, 0.0005)
            hike_rate_std = st.slider("Salary Hike Std Dev", 0.0, 0.10, 0.007, 0.001)
            contribution_start = st.slider("Starting Contribution %", 0.0, 0.20, 0.03, 0.01)
            contribution_max = st.slider("Max Contribution %", 0.0, 0.30, 0.12, 0.01)
            contribution_increase_years = st.number_input("Years to Increase Contribution", min_value=1, max_value=12, value=2, step=1)
            contribution_increase_amount = st.slider("Contribution Increase Amount %", 0.0, 0.10, 0.01, 0.005)
            lump_sum_amount = st.number_input("Lump Sum Top-up Every 5 Years", value=10000, step=500)
            marginal_tax_rate = st.slider("Marginal Tax Rate for FIF", 0.0, 0.5, 0.30, 0.01)
            partner_status = st.selectbox("Do you have a partner?", ["Yes", "No"], index=1)
            partner_contribution_perc = st.slider("Partner Contribution % of Salary", 0.0, 0.15, 0.03, 0.001)
            has_children = st.selectbox("Do you have children?", ["Yes", "No"], index=1)
            invested_real_estate = st.selectbox("Invested in Real Estate?", ["Yes", "No"], index=1)
            double_promotion_year = st.number_input("Double Promotion Year (optional)", min_value=0, max_value=70, value=10, step=1)
            double_promotion_year = None if double_promotion_year == 0 else double_promotion_year

        with st.expander("💸 Unforeseen Withdrawals", expanded=False):
            withdrawal_entries = {}
            add_more = True
            while add_more:
                year = st.number_input(
                    f"Withdrawal Year", min_value=1, max_value=35, step=1, key=f"withdraw_year_{len(withdrawal_entries)}"
                )
                amount = st.number_input(
                    f"Amount in Year {year}", min_value=0, max_value=100000, step=5000, key=f"withdraw_amt_{year}"
                )
                withdrawal_entries[year] = amount
                add_more = st.checkbox("Add another withdrawal?", key=f"add_withdraw_{year}")

        with st.expander("🧾 Post-Retirement Inputs", expanded=False):
            lifestyle_base_today = st.number_input("Current Lifestyle Spending (NZD)", value=70000, step=1000)
            lifestyle_improvement_pct = st.slider("Lifestyle Improvement %", 0.0, 1.0, 0.40, 0.01)
            nz_super_annuity = st.number_input("NZ Super Today (NZD)", value=23000, step=1000)
            return_mean = st.slider("Post-Retirement Return Mean", 0.0, 0.10, 0.04, 0.005)
            return_std = st.slider("Post-Retirement Return Std Dev", 0.0, 0.15, 0.02, 0.005)
            expected_life_expectancy = st.slider("Expected Life Expectancy", 75, 100, 90, 1)

        with st.expander("📊 Fund Allocation Settings", expanded=False):
            allocation_blocks = []
            for i, end_year in enumerate([5, 10, 15, 20, 25, 30, 35]):
                st.markdown(f"**Portfolio Weights for Year ≤ {end_year}**")
                allocation = {
                    "Harboursafe": st.slider(f"Harboursafe % ({end_year})", 0.0, 1.0, min(0.05 + 0.05 * i, 1.0), 0.05, key=f"hs_{i}"),
                    "Horizon": st.slider(f"Horizon % ({end_year})", 0.0, 1.0, min(0.05 + 0.05 * i, 1.0), 0.05, key=f"hz_{i}"),
                    "SkyHigh": st.slider(f"SkyHigh % ({end_year})", 0.0, 1.0, max(0.45 - 0.05 * i, 0.0), 0.05, key=f"sh_{i}"),
                    "Foreign_Equities": st.slider(f"Foreign Equities % ({end_year})", 0.0, 1.0, max(0.30 - 0.05 * i, 0.0), 0.05, key=f"fe_{i}"),
                    "Bitcoin": st.slider(f"Bitcoin % ({end_year})", 0.0, 1.0, max(0.15 - 0.025 * i, 0.0), 0.05, key=f"bt_{i}")
                }
                allocation_blocks.append({"end": end_year, "weights": allocation})
            st.caption("Weights are normalized automatically to model a valid allocation mix.")

    apply_clicked = st.button("🚀 Apply and Run Simulation")

    if apply_clicked:
        normalized_allocation_blocks = normalize_allocation_blocks(allocation_blocks)

        with st.spinner("Running retirement simulations..."):
            n_simulation = 1000
            df_list = []
            for _ in range(n_simulation):
                df_sim = simulate_pre_retirement(
                    initial_salary=initial_salary,
                    hike_rate_mean=hike_rate_mean,
                    hike_rate_std=hike_rate_std,
                    contribution_start=contribution_start,
                    contribution_increase_years=contribution_increase_years,
                    contribution_increase_amount=contribution_increase_amount,
                    contribution_max=contribution_max,
                    lump_sum_amount=lump_sum_amount,
                    lump_sum_frequency=5,
                    start_lump_sum_year=5,
                    years=36,
                    start_age=30,
                    acc_levy=0.0167,
                    inflation_rate=0.025,
                    marginal_tax_rate=marginal_tax_rate,
                    tax_brackets=[(0, 15600), (15601, 53500), (53501, 78100), (78101, 180000), (180001, float("inf"))],
                    growth_rates={
                        "Harboursafe": {"mean": 0.0375, "std": 0.05},
                        "Horizon": {"mean": 0.065, "std": 0.105},
                        "SkyHigh": {"mean": 0.1025, "std": 0.2075},
                        "Foreign_Equities": {"mean": 0.15, "std": np.sqrt(0.15**2 + 0.02**2)},
                        "Bitcoin": {"mean": 0.20, "std": 0.60}
                    },
                    allocation_blocks=normalized_allocation_blocks,
                    has_partner=partner_status,
                    partner_contribution_perc=partner_contribution_perc,
                    has_children=has_children,
                    invested_real_estate=invested_real_estate,
                    double_promotion_year=double_promotion_year,
                    unforeseen_withdrawal_years=withdrawal_entries,
                )
                df_list.append(df_sim)

        df_pre = df_list[0]
        long_df, corpus_percentiles = build_aggregate_summary(df_list)

        total_contributions = long_df.groupby("Simulation")["Total Contribution"].sum().mean()
        final_corpuses = [df["Adjusted Fund Value"].iloc[-1] for df in df_list]
        mean_corpus = np.mean(final_corpuses)
        median_corpus = np.median(final_corpuses)
        p5 = np.percentile(final_corpuses, 5)
        p95 = np.percentile(final_corpuses, 95)

        retirement_corpus_mean = corpus_percentiles.loc[corpus_percentiles["Age"] == 65, "median"].squeeze()
        corpus_at_retirement = retirement_corpus_mean if pd.notna(retirement_corpus_mean) else mean_corpus
        total_profit = corpus_at_retirement - total_contributions if pd.notna(corpus_at_retirement) else np.nan

        df_post = simulate_post_retirement(
            corpus=corpus_at_retirement,
            start_age=66,
            years=expected_life_expectancy - 65,
            return_mean=return_mean,
            return_std=return_std,
            inflation=0.025,
            lifestyle_base_today=lifestyle_base_today,
            lifestyle_improvement_pct=lifestyle_improvement_pct,
            nz_super_annuity=nz_super_annuity,
            accumulation_years=35,
        )

        total_fund_withdrawal = df_post["Withdrawal from Fund"].sum()
        shortfall_probability = np.mean(np.array(final_corpuses) < total_fund_withdrawal) * 100
        sufficiency_score = int(min(100, 100 * corpus_at_retirement / total_fund_withdrawal)) if total_fund_withdrawal > 0 else 100
        funding_status = "Sufficient" if corpus_at_retirement >= total_fund_withdrawal else "At Risk"

        st.subheader("📊 Retirement Summary")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Mean Corpus at 65", format_currency(mean_corpus))
        m2.metric("Median Corpus at 65", format_currency(median_corpus))
        m3.metric("5th Percentile Corpus", format_currency(p5))
        m4.metric("95th Percentile Corpus", format_currency(p95))
        m5.metric("Funding Status", funding_status)

        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("Estimated Total Contributions", format_currency(total_contributions))
        c2.metric("Expected Corpus at Retirement", format_currency(corpus_at_retirement))
        c3.metric("Retirement Sufficiency", f"{sufficiency_score}%")

        if total_fund_withdrawal > 0:
            st.markdown(
                f"""
- **Expected fund withdrawal need:** {format_currency(total_fund_withdrawal)}  
- **Shortfall probability:** {shortfall_probability:.1f}%  
- **Recommended action:** increase savings or lower spending if your sufficiency score is below 80%.
"""
            )
        else:
            st.markdown("- **The retirement funding analysis indicates the simulated fund outflow is zero or not meaningful. Review lifestyle assumptions.**")

        st.markdown("---")
        fig_corpus_band = plot_corpus_band(corpus_percentiles)
        st.pyplot(fig_corpus_band)

        fig_dist, _, _, _ = plot_retirement_corpus_distribution(final_corpuses)
        st.pyplot(fig_dist)

        fig_stack = plot_contribution_stack(df_pre)
        st.pyplot(fig_stack)

        st.subheader("📉 Post-Retirement Drawdown")
        fig_drawdown, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df_post["Age"], df_post["Remaining Corpus"], color="#d1495b", linewidth=2.5)
        ax.fill_between(df_post["Age"], df_post["Remaining Corpus"], 0, where=df_post["Remaining Corpus"] >= 0, color="#f7cac9", alpha=0.4)
        ax.fill_between(df_post["Age"], df_post["Remaining Corpus"], 0, where=df_post["Remaining Corpus"] < 0, color="#c1121f", alpha=0.4)
        ax.set_title("Post-Retirement Corpus Drawdown")
        ax.set_xlabel("Age")
        ax.set_ylabel("Remaining Corpus (NZD)")
        ax.grid(True)
        st.pyplot(fig_drawdown)

        st.subheader("📈 Fund Returns Distribution")
        return_columns = [col for col in df_pre.columns if "Return" in col and "FIF" not in col and "Return Rate" not in col]
        fig_returns, ax_returns = plt.subplots(figsize=(10, 5))
        sns.boxplot(data=df_pre[return_columns], ax=ax_returns, palette="Set3")
        ax_returns.set_title("Annual Fund Return Distribution")
        ax_returns.set_ylabel("Return (NZD)")
        ax_returns.set_xticklabels(ax_returns.get_xticklabels(), rotation=30, ha="right")
        st.pyplot(fig_returns)

        with st.expander("📋 Detailed Pre-Retirement Summary", expanded=False):
            st.dataframe(df_pre.reset_index(drop=True))

        with st.expander("📋 Detailed Post-Retirement Summary", expanded=False):
            st.dataframe(df_post.reset_index(drop=True))

        with st.expander("📊 Aggregate Simulation Summary", expanded=False):
            st.dataframe(corpus_percentiles)


if __name__ == "__main__":
    main()

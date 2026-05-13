import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.ticker import FuncFormatter
from scipy.stats import norm
import seaborn as sns
from post_retirement import simulate_post_retirement
from pre_retirement import simulate_pre_retirement

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


def million_formatter(x, pos):
    if x >= 1e6:
        return f"{x/1e6:.1f}M"
    if x >= 1e3:
        return f"{x/1e3:.0f}K"
    return f"{x:.0f}"


def plot_retirement_corpus_distribution(final_values):
    mu = np.mean(final_values)
    p5 = np.percentile(final_values, 5)
    p95 = np.percentile(final_values, 95)

    x = np.linspace(min(final_values), max(final_values), 200)
    pdf = norm.pdf(x, mu, np.std(final_values))

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(final_values, kde=False, stat="density", bins=30, color="#6fa8dc", ax=ax)
    ax.plot(x, pdf, color="#2a4d69", linewidth=2.5, label="Normal PDF")
    ax.fill_between(x, 0, pdf, where=(x <= p5), color="#f4cccc", alpha=0.4, label="Lower 5% tail")
    ax.fill_between(x, 0, pdf, where=(x >= p95), color="#d9ead3", alpha=0.4, label="Upper 5% tail")
    ax.axvline(mu, color="#1f618d", linestyle="-", linewidth=2, label=f"Mean: {format_currency(mu)}")
    ax.axvline(p5, color="#a6acaf", linestyle="--", linewidth=1.5, label=f"5th percentile: {format_currency(p5)}")
    ax.axvline(p95, color="#a6acaf", linestyle="--", linewidth=1.5, label=f"95th percentile: {format_currency(p95)}")
    ax.set_title("Distribution of Final Retirement Corpus")
    ax.set_xlabel("Corpus at Retirement (Millions NZD)")
    ax.set_ylabel("Density")
    ax.xaxis.set_major_formatter(FuncFormatter(million_formatter))
    ax.legend(loc="upper right", frameon=False)
    return fig, mu, p5, p95


def plot_corpus_band(percentiles):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(percentiles["Age"], percentiles["p5"], percentiles["p95"], color="#cfe2f3", alpha=0.3, label="5th–95th percentile range")
    ax.plot(percentiles["Age"], percentiles["median"], color="#114b8d", linewidth=2.5, label="Median corpus")
    ax.set_title("Projected Retirement Corpus with Risk Bands")
    ax.set_xlabel("Age")
    ax.set_ylabel("Projected Fund Value (Millions NZD)")
    ax.yaxis.set_major_formatter(FuncFormatter(million_formatter))
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


def plot_cashflow(df_pre):
    df = df_pre.copy()
    expense_cols = ["Rent", "Groceries", "Travel", "Utilities", "Insurance", "Leisure", "Misc"]
    df["Total Expenses"] = df[expense_cols].sum(axis=1)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["Age"], df["Net Salary"], label="Net Salary", color="#2a6f97", linewidth=2)
    ax.plot(df["Age"], df["Total Contribution"], label="Total Contribution", color="#ff8c42", linewidth=2)
    ax.plot(df["Age"], df["Total Expenses"], label="Total Expenses", color="#8c2d04", linewidth=2)
    ax.plot(df["Age"], df["Adjusted Fund Value"], label="Portfolio Value", color="#1b4f72", linewidth=2, linestyle="--")
    ax.set_title("Net Cashflow, Savings, Expenses and Portfolio Value")
    ax.set_xlabel("Age")
    ax.set_ylabel("NZD")
    ax.legend()
    ax.yaxis.set_major_formatter(FuncFormatter(million_formatter))
    return fig


def plot_funding_gauge(score, corpus, required):
    fig, ax = plt.subplots(figsize=(4, 2.2))
    fig.subplots_adjust(top=0.85, bottom=0.12, left=0.05, right=0.98)
    ax.axis("off")

    segments = [
        (108, 180, "#d9534f"),  # 0-60%
        (36, 108, "#f0ad4e"),   # 60-80%
        (0, 36, "#5cb85c"),     # 80-100%
    ]
    for start, end, color in segments:
        wedge = patches.Wedge((0, 0), 1.0, start, end, width=0.18, facecolor=color, edgecolor="none")
        ax.add_patch(wedge)

    outer = patches.Wedge((0, 0), 1.0, 180, 0, width=0.03, facecolor="none", edgecolor="#666", linewidth=1.5)
    ax.add_patch(outer)

    score_theta = 180 - np.clip(score, 0, 100) / 100 * 180
    x = np.cos(np.radians(score_theta)) * 0.82
    y = np.sin(np.radians(score_theta)) * 0.82
    needle_color = "#d9534f" if score < 60 else "#f0ad4e" if score < 80 else "#5cb85c"
    ax.plot([0, x], [0, y], color=needle_color, linewidth=4, zorder=5)
    hub = patches.Circle((0, 0), 0.06, facecolor=needle_color, edgecolor="#ffffff", linewidth=2, zorder=6)
    ax.add_patch(hub)

    for pct in range(0, 101, 20):
        angle = 180 - pct / 100 * 180
        x0 = np.cos(np.radians(angle)) * 0.92
        y0 = np.sin(np.radians(angle)) * 0.92
        x1 = np.cos(np.radians(angle)) * 1.0
        y1 = np.sin(np.radians(angle)) * 1.0
        ax.plot([x0, x1], [y0, y1], color="#333", linewidth=2)
        xl = np.cos(np.radians(angle)) * 1.12
        yl = np.sin(np.radians(angle)) * 1.12
        ax.text(xl, yl, f"{pct}%", ha="center", va="center", fontsize=9, color="#333")

    ax.text(0, -0.18, f"Funding sufficiency", ha="center", fontsize=12, fontweight="bold")
    ax.text(0, -0.34, f"{score:.0f}% funded", ha="center", fontsize=11, color="#333")
    ax.text(0, -0.52, f"{format_currency(corpus)} / {format_currency(required)}", ha="center", fontsize=9, color="#555")

    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.7, 1.05)
    return fig


def plot_allocation_evolution(normalized_blocks):
    data = {"Age": [block["end"] for block in normalized_blocks]}
    assets = list(normalized_blocks[0]["weights"].keys())
    for asset in assets:
        data[asset] = [block["weights"][asset] for block in normalized_blocks]
    df = pd.DataFrame(data)

    fig, ax = plt.subplots(figsize=(10, 4))
    palette = ["#1b4f72", "#117a65", "#d35400", "#6c3483", "#1f618d"]
    for asset, color in zip(assets, palette):
        ax.plot(df["Age"], df[asset], marker="o", linewidth=2, label=asset, color=color)
    ax.set_title("Selected Portfolio Allocation Over Time")
    ax.set_xlabel("Year End")
    ax.set_ylabel("Allocation Weight")
    ax.set_ylim(0, 1)
    ax.legend(loc="upper left", fontsize="small")
    return fig


def main():
    st.set_page_config(page_title="Retirement Planner", page_icon="💰", layout="wide")
    st.title("💼 Financial Advisor — NZ Retirement Planning Simulator")
    st.markdown(
        "This interactive planner evaluates your savings path and retirement funding using realistic salary growth, contributions, investment allocation, and NZ Super support. It helps you understand how robust your corpus is against downside risk."
    )
    st.markdown("---")
    st.markdown(
        """
### What this dashboard shows
- **Projected retirement corpus:** how much retirement savings you may build by age 65.
- **Risk bands & distribution:** the range of possible outcomes from conservative to optimistic.
- **Post-retirement drawdown:** whether your savings can cover lifestyle spending plus NZ Super.
- **Cost and cashflow view:** salary, expenses, and savings behavior across your working life.
"""
    )
    st.markdown(
        """
### How to use the inputs
- Increase **Starting Contribution %** and **Max Contribution %** to grow your corpus faster.
- Adjust **Salary Hike** assumptions to reflect your career progression.
- Use **Unforeseen Withdrawals** for planned home upgrades, education, or unexpected costs.
- Set **Lifestyle Spending** and **NZ Super** to test whether retirement income covers your desired standard of living.
"""
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
        funding_status = "Sufficient" if sufficiency_score >= 80 and df_post["Remaining Corpus"].min() >= 0 else "At Risk"

        required_fund = total_fund_withdrawal
        st.subheader("📊 Retirement Summary")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Mean Corpus at 65", format_currency(mean_corpus))
        c2.metric("Median Corpus at 65", format_currency(median_corpus))
        c3.metric("Required Retirement Fund", format_currency(required_fund))
        c4.metric("Funding Status", funding_status)
        c5.metric("Retirement Sufficiency", f"{sufficiency_score}%")

        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Estimated Total Contributions", format_currency(total_contributions))
        c2.metric("Expected Corpus at Retirement", format_currency(corpus_at_retirement))
        c3.metric("Required Fund", format_currency(required_fund))
        c4.metric("Shortfall Probability", f"{shortfall_probability:.1f}%")

        if total_fund_withdrawal > 0:
            st.markdown(
                f"""
- **Expected fund withdrawal need:** {format_currency(total_fund_withdrawal)}  
- **5th percentile corpus:** {format_currency(p5)}  
- **95th percentile corpus:** {format_currency(p95)}  
- **Shortfall probability:** {shortfall_probability:.1f}%  
- **Recommended action:** increase savings or lower spending if your sufficiency score is below 80% or if the retirement corpus runs out after age 65.
"""
            )
        else:
            st.markdown("- **The retirement funding analysis indicates the simulated fund outflow is zero or not meaningful. Review lifestyle assumptions.**")

        gauge_fig = plot_funding_gauge(sufficiency_score, corpus_at_retirement, required_fund)
        st.pyplot(gauge_fig)

        st.markdown("---")
        st.markdown(
            "### What the charts are telling you"
            "\n- The median path shows the most typical corpus build-up by age 65."
            "\n- The shaded risk band shows downside and upside outcomes across 1,000 simulations."
            "\n- Retirement Sufficiency measures whether the age-65 corpus can support the modeled retirement withdrawal profile, not just whether the year-65 balance equals that year’s annual spending."
            "\n- Wide return distributions imply higher volatility, while narrow boxes suggest more stable funds."
        )

        fig_corpus_band = plot_corpus_band(corpus_percentiles)
        fig_dist, _, _, _ = plot_retirement_corpus_distribution(final_corpuses)
        fig_alloc = plot_allocation_evolution(normalized_allocation_blocks)
        fig_cashflow = plot_cashflow(df_pre)

        top_left, top_right = st.columns(2)
        with top_left:
            st.subheader("📈 Retirement Corpus Risk Bands")
            st.pyplot(fig_corpus_band)
            st.markdown(
                "This chart shows the expected range of fund values at each age. The dark line is the median scenario, while the shaded area captures the most likely downside and upside paths."
            )
        with top_right:
            st.subheader("📊 Outcome Distribution")
            st.pyplot(fig_dist)
            st.markdown(
                "The histogram shows the probability of different final corpus outcomes at retirement. A left-skewed tail means downside risk is possible, while the peak shows the most probable corpus range."
            )

        mid_left, mid_right = st.columns(2)
        with mid_left:
            st.subheader("📐 Portfolio Allocation Over Time")
            st.pyplot(fig_alloc)
            st.markdown(
                "This plot shows how asset allocation weights evolve over the selected years. Use it to verify your risk posture and ensure the mix matches your retirement horizon."
            )
        with mid_right:
            st.subheader("💰 Cashflow and Savings Insight")
            st.pyplot(fig_cashflow)
            st.markdown(
                "Compare net salary, total contributions, portfolio value, and total expenses. The portfolio value line shows how invested capital grows compared to spending. "
                "Note: this expense line is an annual spending requirement, while portfolio value is the total accumulated balance. A year where expenses appear higher than portfolio value is a warning sign, not a direct one-to-one comparison, because retirement income also depends on NZ Super and future returns. "
                "It is possible under aggressive inflation and lifestyle assumptions for age-65 annual spending to reach several million NZD, even though the retirement corpus at 65 may be lower. The key question is whether that corpus can sustain the modeled withdrawal path."
            )

        bottom_left, bottom_right = st.columns(2)
        with bottom_left:
            st.subheader("📉 Post-Retirement Drawdown")
            fig_drawdown, ax = plt.subplots(figsize=(10, 4))
            ax.plot(df_post["Age"], df_post["Remaining Corpus"], color="#d1495b", linewidth=2.5)
            ax.fill_between(df_post["Age"], df_post["Remaining Corpus"], 0, where=df_post["Remaining Corpus"] >= 0, color="#f7cac9", alpha=0.4)
            ax.fill_between(df_post["Age"], df_post["Remaining Corpus"], 0, where=df_post["Remaining Corpus"] < 0, color="#c1121f", alpha=0.4)
            ax.set_title("Post-Retirement Corpus Drawdown")
            ax.set_xlabel("Age")
            ax.set_ylabel("Remaining Corpus (NZD)")
            ax.grid(True)
            st.pyplot(fig_drawdown)
            st.markdown(
                "This chart shows how your retirement corpus moves after age 65. If the line crosses below zero, the assumed lifestyle spending exceeds available savings."
            )
        with bottom_right:
            st.subheader("📈 Fund Return Volatility")
            return_columns = [col for col in df_pre.columns if "Return" in col and "FIF" not in col and "Return Rate" not in col]
            fig_returns, ax_returns = plt.subplots(figsize=(10, 4))
            sns.boxplot(data=df_pre[return_columns], ax=ax_returns, palette="Set3")
            ax_returns.set_title("Annual Fund Return Distribution")
            ax_returns.set_ylabel("Return (NZD)")
            ax_returns.set_xticklabels(ax_returns.get_xticklabels(), rotation=30, ha="right")
            st.pyplot(fig_returns)
            st.markdown(
                "Asset boxes with greater height represent more volatile returns. Choose more stable funds if you need a smoother outcome, or more aggressive funds if you can tolerate higher risk."
            )

        st.markdown("---")
        st.subheader("Pre-Retirement Summary")
        pre_comments = []
        home_purchase = df_pre.loc[df_pre["Owns Home"] & ~df_pre["Owns Home"].shift(fill_value=False)]
        if not home_purchase.empty:
            home_age = int(home_purchase["Age"].iloc[0])
            pre_comments.append(f"Home purchase transitions at age {home_age}, which may increase expenses and reduce your available savings capacity.")
        if (df_pre["Total Spent"] > df_pre["Total Contribution"]).any():
            years_over = df_pre.loc[df_pre["Total Spent"] > df_pre["Total Contribution"], "Age"].tolist()
            pre_comments.append(
                f"Expenses exceed contributions in {len(years_over)} year(s); this suggests you should either raise contributions or lower lifestyle costs."
            )
        expense_jump_idx = df_pre["Total Spent"].diff().idxmax()
        expense_jump_age = int(df_pre.loc[expense_jump_idx, "Age"])
        pre_comments.append(
            f"The largest step-up in total spending occurs around age {expense_jump_age}. Review large financial commitments at that stage."
        )
        if not pre_comments:
            pre_comments.append("Pre-retirement cashflow remains balanced, but keep monitoring contribution and expense growth.")
        for comment in pre_comments:
            st.markdown(f"- {comment}")

        st.subheader("Post-Retirement Summary")
        if df_post["Remaining Corpus"].min() < 0:
            runout_age = int(df_post.loc[df_post["Remaining Corpus"] < 0, "Age"].iloc[0])
            st.markdown(
                f"- The retirement corpus falls below zero by age {runout_age}, indicating a funding gap in this plan."
            )
            st.markdown(
                "- Consider increasing pre-retirement savings, lowering post-retirement lifestyle spending, or improving assumed portfolio returns."
            )
        else:
            st.markdown(
                "- The corpus remains positive through the selected life expectancy, meaning the current plan is sufficient under modeled assumptions."
            )
        if total_fund_withdrawal > corpus_at_retirement:
            st.markdown(
                "- The required withdrawal amount exceeds expected corpus, so the plan is at risk and should be adjusted."
            )

        st.markdown("---")
        with st.expander("📋 Detailed Pre-Retirement Summary", expanded=False):
            st.dataframe(df_pre.reset_index(drop=True))

        with st.expander("📋 Detailed Post-Retirement Summary", expanded=False):
            st.dataframe(df_post.reset_index(drop=True))

        with st.expander("📊 Aggregate Simulation Summary", expanded=False):
            st.dataframe(corpus_percentiles)


if __name__ == "__main__":
    main()

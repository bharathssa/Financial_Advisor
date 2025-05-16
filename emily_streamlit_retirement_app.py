import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from scipy.stats import norm
import seaborn as sns
from emily_post_retirement import simulate_post_retirement
from emily_pre_retirement import simulate_pre_retirement


def main():

    st.set_page_config(page_title="Emily's Retirement Planner", layout="wide")

    st.title("\U0001F4BC Superannuation Fund & Retirement Planner")
    st.markdown("""
    This app simulates the accumulation and drawdown of superannuation for retirement planning. Adjust the settings below to customize the forecast.
    """)

    with st.sidebar:
        with st.expander("\U0001F4CA Pre-Retirement Inputs", expanded=False):
            initial_salary = st.number_input("Initial Salary", value=70000, step=1000)
            hike_rate_mean = st.slider("Annual Hike Mean", 0.000, 0.1000, 0.0375, 0.0005)
            hike_rate_std = st.slider("Hike Std Dev", 0.0, 0.05, 0.007, 0.001)
            contribution_start = st.slider("Starting Contribution %", 0.0, 0.20, 0.03, 0.01)
            contribution_max = st.slider("Max Contribution %", 0.0, 0.30, 0.12, 0.01)
            contribution_increase_years = st.number_input("Years to Increase Contribution", min_value=1, max_value=12, value=2, step=1)
            contribution_increase_amount = st.slider("Increase Amount %", 0.0, 0.05, 0.01, 0.005)
            lump_sum_amount = st.number_input("Lump Sum Every 5 Years", value=10000, step=500)
            marginal_tax_rate = st.slider("Marginal Tax Rate for FIF", 0.0, 0.5, 0.30, 0.01)
            partner_status = st.selectbox("Do you have a partner?", ["Yes", "No"], index=1)
            partner_contribution_perc = st.slider("How much partner can contribute", 0.01, 0.1,0.03,0.001)
            has_children = st.selectbox("Do you have Children?", ["Yes", "No"], index=1)
            invested_real_estate = st.selectbox("Have you invested in Real Estate?", ["Yes", "No"], index=1)
            double_promotion_year = st.number_input("Double Promotion Year (optional)", min_value=0, max_value=70, value=10, step=1)
            double_promotion_year = None if double_promotion_year == 0 else double_promotion_year

        with st.expander("\U0001F4B8 Unforeseen Withdrawals", expanded=False):
            withdrawal_entries = {}
            add_more = True
            while add_more:
                year = st.number_input(f"Withdrawal Year", min_value=1, max_value=35, step=1, key=f"withdraw_year_{len(withdrawal_entries)}")
                amount = st.number_input(f"Amount in Year {year}", min_value=0, max_value=100000, step=5000, key=f"withdraw_amt_{year}")
                withdrawal_entries[year] = amount
                add_more = st.checkbox("Add Another Withdrawal?", key=f"add_withdraw_{year}")

        with st.expander("\U0001F4C9 Post-Retirement Inputs", expanded=False):
            lifestyle_base_today = st.number_input("Current Lifestyle Spending", value=70000, step=1000)
            lifestyle_improvement_pct = st.slider("Lifestyle Improvement %", 0.0, 1.0, 0.40, 0.01)
            nz_super_annuity = st.number_input("NZ Super (Today)", value=23000, step=1000)
            return_mean = st.slider("Post-Retirement Return Mean", 0.0, 0.1, 0.04, 0.005)
            return_std = st.slider("Post-Retirement Return Std Dev", 0.0, 0.1, 0.02, 0.005)
            expected_life_expectancy = st.slider("Expected Life Expectancy", 75, 100, 90, 1)

        with st.expander("\U0001F4E6 Fund Allocation Settings", expanded=False):
            allocation_blocks = []
            for i, end_year in enumerate([5, 10, 15, 20, 25, 30, 35]):
                st.markdown(f"**Allocation for Year ≤ {end_year}**")
                allocation = {
                    "Harboursafe": st.slider(f"Harboursafe % ({end_year})", 0.0, 1.0, 0.05 + 0.05*i, 0.05, key=f"hs_{i}"),
                    "Horizon": st.slider(f"Horizon % ({end_year})", 0.0, 1.0, 0.05 + 0.05*i, 0.05, key=f"hz_{i}"),
                    "SkyHigh": st.slider(f"SkyHigh % ({end_year})", 0.0, 1.0, 0.45 - 0.05*i, 0.05, key=f"sh_{i}"),
                    "Foreign_Equities": st.slider(f"Foreign_Equities % ({end_year})", 0.0, 1.0, 0.30 - 0.05*i, 0.05, key=f"fe_{i}"),
                    "Bitcoin": st.slider(f"Bitcoin % ({end_year})", 0.0, 1.0, 0.15 - 0.025*i, 0.05, key=f"bt_{i}")
                }
                allocation_blocks.append({"end": end_year, "weights": allocation})

    apply_clicked = st.button("\U0001F680 Apply and Run Simulation")
    
# Pre retirement simulation

    if apply_clicked:
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
                tax_brackets=[(0, 15600), (15601, 53500), (53501, 78100), (78101, 180000), (180001, float('inf'))],
                growth_rates={
                    "Harboursafe": {"mean": 0.0375, "std": 0.05},
                    "Horizon": {"mean": 0.065, "std": 0.105},
                    "SkyHigh": {"mean": 0.1025, "std": 0.2075},
                    "Foreign_Equities": {"mean": 0.15, "std": np.sqrt(0.15**2 + 0.02**2)},
                    "Bitcoin": {"mean": 0.20, "std": 0.60}
                },
                allocation_blocks=allocation_blocks,
                has_partner=partner_status,
                partner_contribution_perc = partner_contribution_perc,
                has_children=has_children,
                invested_real_estate=invested_real_estate,
                double_promotion_year=double_promotion_year,
                unforeseen_withdrawal_years=withdrawal_entries
            )
            df_list.append(df_sim)

        # Use the first simulation for visuals and post-retirement logic
        df_pre = df_list[0]    

        # Generate summary across simulations (exclude age 30)
                
        long_df = pd.concat([df.assign(Simulation=i) for i, df in enumerate(df_list)], ignore_index=True)
        
        numerical_columns = [
            "Gross Salary", "Salary Hike Value", "Salary Hike %", "Income Tax", "ACC Levy", "Net Salary",
            "Employee Contribution Rate %", "Employer Contribution Rate %", "Employee Contribution",
            "Employer Contribution", "Total Contribution", "Lump Sum Added", "Foreign Corpus", "Foreign Return Rate",
            "FIF Tax (NZD)", "FIF Tax % of Foreign Value", "Harboursafe Contribution", "Horizon Contribution",
            "SkyHigh Contribution", "Foreign_Equities Contribution", "Bitcoin Contribution", "Harboursafe Return",
            "Horizon Return", "SkyHigh Return", "Foreign_Equities Return", "Bitcoin Return", "Rent", "Groceries",
            "Travel", "Utilities", "Insurance", "Leisure", "Misc", "Total Spent", "Unforeseen Withdrawal",
            "Requested Withdrawal", "Withdrawal Shortfall", "Adjusted Fund Value"
        ]

        summary_stats = []
        for col in numerical_columns:
            grouped = long_df.groupby("Age")[col].agg(
                mean="mean"
                # ,std="std",
                # p5=lambda x: x.quantile(0.05),
                # p95=lambda x: x.quantile(0.95)
            ).rename(columns={"mean": f"{col} - Mean"
                            #   , "std": f"{col} - Std Dev",
                            #   "p5": f"{col} - 5th Percentile", "p95": f"{col} - 95th Percentile"
                              })
            summary_stats.append(grouped)

        combined_summary = pd.concat(summary_stats, axis=1).reset_index()

        # Ensure Age 30 and 65 are included if missing (fill with NaNs)
        all_ages = pd.DataFrame({"Age": list(range(30, 66))})
        combined_summary = all_ages.merge(combined_summary, on="Age", how="left")

        

        # Use full data to calculate total contribution mean across all ages
        total_contributions = long_df.groupby("Simulation")["Total Contribution"].sum().mean()
        last_row = combined_summary[combined_summary["Age"] == 65]
        corpus_at_retirement = last_row["Adjusted Fund Value - Mean"].values[0] if not last_row.empty else np.nan
        total_profit = corpus_at_retirement - total_contributions if not np.isnan(corpus_at_retirement) else np.nan
        



#Post retirement simulation
        df_post = simulate_post_retirement(
            corpus=corpus_at_retirement,
            start_age=65,
            years= expected_life_expectancy-65,
            return_mean=return_mean,
            return_std=return_std,
            inflation=0.025,
            lifestyle_base_today=lifestyle_base_today,
            lifestyle_improvement_pct=lifestyle_improvement_pct,
            nz_super_annuity=nz_super_annuity,
            accumulation_years=35
        )

        total_exp_corpus_neg = df_post.loc[df_post["Remaining Corpus"] < 0, "Remaining Corpus"].abs().sum()
        total_exp_corpus = corpus_at_retirement + total_exp_corpus_neg

        Decision_Status_YesorNo = "yes" if corpus_at_retirement >= total_exp_corpus else "No"

# Metrics
        # Summary metrics
        st.subheader("\U0001F4CA Summary Metrics")
        col1, col2, col3,col4, col5 = st.columns(5)
        col1.metric("Total Investment", f"${total_contributions:,.0f}" if not np.isnan(total_contributions) else "N/A")
        col2.metric("Total Profit", f"${total_profit:,.0f}" if not np.isnan(total_profit) else "N/A")
        col3.metric("Corpus at Retirement", f"${corpus_at_retirement:,.0f}" if not np.isnan(corpus_at_retirement) else "N/A")
        col4.metric("Total Expected corpus", f"${total_exp_corpus : ,.0f}")
        col5.metric("Decision Status", f"{Decision_Status_YesorNo}")

 # ------------------- Normal Distribution of Corpus ------------------- #
        st.subheader("📈 Simulated Distribution of Corpus at Retirement")

        # Get the final corpus from each simulation
        final_corpus_values = [df["Adjusted Fund Value"].iloc[-1] for df in df_list]

        # Calculate statistics
        mu = np.mean(final_corpus_values)
        std = np.std(final_corpus_values)
        p5 = np.percentile(final_corpus_values, 5)
        p95 = np.percentile(final_corpus_values, 95)

        # Simulate distribution
        x = np.linspace(min(final_corpus_values), max(final_corpus_values), 100)
        pdf = norm.pdf(x, mu, std)

        # Plot
        fig_dist, ax_dist = plt.subplots(figsize=(10, 5))
        sns.histplot(final_corpus_values, kde=False, stat="density", bins=30, color="skyblue", ax=ax_dist)
        ax_dist.plot(x, pdf, 'r-', label='Normal PDF')

        # Vertical lines
        ax_dist.axvline(mu, color='green', linestyle='-', linewidth=2, label=f"Mean: ${mu:,.0f}")
        ax_dist.axvline(p5, color='gray', linestyle='--', linewidth=1.5, label=f"5th Percentile: ${p5:,.0f}")
        ax_dist.axvline(p95, color='gray', linestyle='--', linewidth=1.5, label=f"95th Percentile: ${p95:,.0f}")

        # Text annotations
        # Text annotations (VERTICAL)
        ax_dist.annotate(f"Mean:\n${mu:,.0f}", xy=(mu, max(pdf)*0.8), xytext=(mu, max(pdf)*1.05),
                        arrowprops=dict( color='green'), ha='center', color='green')

        ax_dist.annotate(f"5th %:\n${p5:,.0f}", xy=(p5, max(pdf)*0.4), xytext=(p5, max(pdf)*0.8),
                        arrowprops=dict(color='gray'), ha='center', color='gray')

        ax_dist.annotate(f"95th %:\n${p95:,.0f}", xy=(p95, max(pdf)*0.4), xytext=(p95, max(pdf)*0.8),
                        arrowprops=dict(color='gray'), ha='center', color='gray')


        # Final plot formatting
        ax_dist.set_title("Normal Distribution of Final Retirement Corpus")
        ax_dist.set_xlabel("Corpus at Retirement (NZD)")
        ax_dist.set_ylabel("Density")
        ax_dist.legend()
        ax_dist.grid(True)

        st.pyplot(fig_dist)



# Fund Growth Visualization
        st.subheader("\U0001F4C8 Pre-Retirement Fund Growth")
        fig1, ax1 = plt.subplots(figsize=(10, 4))
        ax1.plot(df_pre['Age'], df_pre['Adjusted Fund Value'], label='Total Corpus')
        ax1.set_xlabel("Age")
        ax1.set_ylabel("Fund Value")
        ax1.set_title("Fund Growth Over Time")
        ax1.legend()
        ax1.grid(True)
        st.pyplot(fig1)

        # Post-Retirement Corpus Drawdown
        st.subheader("\U0001F4C9 Post-Retirement Corpus Drawdown")
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        ax2.plot(df_post['Age'], df_post['Remaining Corpus'], label='Remaining Corpus', color='tab:red')
        ax2.set_xlabel("Age")
        ax2.set_ylabel("NZD")
        ax2.set_title("Post-Retirement Corpus Depletion")
        ax2.legend()
        ax2.grid(True)
        st.pyplot(fig2)


        # Fund Returns Distribution
        st.subheader("\U0001F4CA Fund Returns Distribution")
        fig3, ax3 = plt.subplots(figsize=(10, 5))
        returns_data = df_pre[[col for col in df_pre.columns if 'Return' in col and 'FIF' not in col and 'Return Rate' not in col]]
        sns.boxplot(data=returns_data, ax=ax3)
        ax3.set_title("Boxplot of Annual Returns Across Funds")
        ax3.set_ylabel("Annual Return (NZD)")
        plt.xticks(rotation=30)
        st.pyplot(fig3)

# Summary Statistics Across All Simulations
        st.subheader("\U0001F4C8 Summary Statistics Across All Simulations")
        st.dataframe(combined_summary)

# Pre and Post Retirement Tables
        st.subheader("\U0001F4CB Detailed Pre-Retirement Summary")
        st.dataframe(df_pre.reset_index(drop=True))

        st.subheader("\U0001F4CB Post-Retirement Summary")
        st.dataframe(df_post.reset_index(drop=True))


if __name__ == "__main__":
    main()

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



    # --- STREAMLIT UI START ---
    st.title("💼 Emily's Superannuation Fund & Retirement Planner")
    st.markdown("""
    This app simulates the accumulation and drawdown of superannuation for retirement planning. Adjust the settings below to customize the forecast.
    """)

    with st.sidebar:
                
        with st.expander("📊 Pre-Retirement Inputs", expanded=False):
            initial_salary = st.number_input("Initial Salary", value=70000, step=1000)
            hike_rate_mean = st.slider("Annual Hike Mean", 0.0, 0.1, 0.05, 0.005)
            hike_rate_std = st.slider("Hike Std Dev", 0.0, 0.05, 0.007, 0.001)
            contribution_start = st.slider("Starting Contribution %", 0.0, 0.20, 0.06, 0.01)
            contribution_max = st.slider("Max Contribution %", 0.0, 0.30, 0.15, 0.01)
            contribution_increase_years = st.number_input("Years to Increase Contribution", 1, 10, 3)
            contribution_increase_amount = st.slider("Increase Amount %", 0.0, 0.05, 0.01, 0.005)
            lump_sum_amount = st.number_input("Lump Sum Every 5 Years", value=10000, step=500)
            marginal_tax_rate = st.slider("Marginal Tax Rate for FIF", 0.0, 0.5, 0.30, 0.01)
            partner_status = st.selectbox("Do you have a partner?", ["Yes", "No"], index=1)
            has_children = st.selectbox("Do you have Children?", ["Yes", "No"], index=1)
            invested_real_estate = st.selectbox("Have you invested in Real Estate?", ["Yes", "No"], index=1)
            double_promotion_year = st.number_input("Double Promotion Year (optional)", min_value=0, max_value=70, value=0, step=1)
            double_promotion_year = None if double_promotion_year == 0 else double_promotion_year
        with st.expander("💸 Unforeseen Withdrawals", expanded=False):
            withdrawal_entries = {}
            add_more = True
            while add_more:
                year = st.number_input(f"Withdrawal Year", min_value=1, max_value=35, step=1, key=f"withdraw_year_{len(withdrawal_entries)}")
                amount = st.number_input(f"Amount in Year {year}", min_value=0, max_value=100000, step=5000, key=f"withdraw_amt_{year}")
                withdrawal_entries[year] = amount
                add_more = st.checkbox("Add Another Withdrawal?", key=f"add_withdraw_{year}")

        with st.expander("📉 Post-Retirement Inputs", expanded=False):
            lifestyle_base_today = st.number_input("Current Lifestyle Spending", value=70000, step=1000)
            lifestyle_improvement_pct = st.slider("Lifestyle Improvement %", 0.0, 1.0, 0.40, 0.05)
            nz_super_annuity = st.number_input("NZ Super (Today)", value=23000, step=1000)
            return_mean = st.slider("Post-Retirement Return Mean", 0.0, 0.1, 0.05, 0.005)
            return_std = st.slider("Post-Retirement Return Std Dev", 0.0, 0.1, 0.02, 0.005)

        allocation_blocks = []
        for i, end_year in enumerate([5, 10, 15, 20, 25, 30, 35]):
            with st.expander(f"📦 Allocation for Year ≤ {end_year}", expanded=False):
                allocation = {
                    "Harboursafe": st.slider(f"Harboursafe % ({end_year})", 0.0, 1.0, 0.05 + 0.05*i, 0.05, key=f"hs_{i}"),
                    "Horizon": st.slider(f"Horizon % ({end_year})", 0.0, 1.0, 0.05 + 0.05*i, 0.05, key=f"hz_{i}"),
                    "SkyHigh": st.slider(f"SkyHigh % ({end_year})", 0.0, 1.0, 0.45 - 0.05*i, 0.05, key=f"sh_{i}"),
                    "Foreign_Equities": st.slider(f"Foreign_Equities % ({end_year})", 0.0, 1.0, 0.30 - 0.05*i, 0.05, key=f"fe_{i}"),
                    "Bitcoin": st.slider(f"Bitcoin % ({end_year})", 0.0, 1.0, 0.15 - 0.025*i, 0.05, key=f"bt_{i}")
                }
                allocation_blocks.append({"end": end_year, "weights": allocation})

    apply_clicked = st.button("🚀 Apply and Run Simulation")
        


    if apply_clicked:
        # Run Simulations - Pre retirement
        n_simulation =1000
        
        for _ in range(n_simulation):
            df_pre = simulate_pre_retirement(
                initial_salary=70000,
                hike_rate_mean=0.05,
                hike_rate_std=0.007,
                contribution_start=0.06,
                contribution_increase_years=3,
                contribution_increase_amount=0.01,
                contribution_max=0.15,
                lump_sum_amount=10000,
                lump_sum_frequency=5,
                start_lump_sum_year=5,
                years=35,
                start_age=30,
                acc_levy=0.0167,
                inflation_rate=0.025,
                marginal_tax_rate=0.30,
                tax_brackets=[(0, 15600), (15601, 53500), (53501, 78100), (78101, 180000), (180001, float('inf'))],
                growth_rates={
                    "Harboursafe": {"mean": 0.0375, "std": 0.05},
                    "Horizon": {"mean": 0.065, "std": 0.105},
                    "SkyHigh": {"mean": 0.1025, "std": 0.2075},
                    "Foreign_Equities": {"mean": 0.15, "std": np.sqrt(0.15**2 + 0.02**2)},
                    "Bitcoin": {"mean": 0.20, "std": 0.60}
                },
                allocation_blocks=[
                    {"end": 5, "weights": {"Harboursafe": 0.05, "Horizon": 0.05, "SkyHigh": 0.45, "Foreign_Equities": 0.30, "Bitcoin": 0.15}},
                    {"end": 10, "weights": {"Harboursafe": 0.10, "Horizon": 0.10, "SkyHigh": 0.50, "Foreign_Equities": 0.20, "Bitcoin": 0.10}},
                    {"end": 15, "weights": {"Harboursafe": 0.20, "Horizon": 0.15, "SkyHigh": 0.45, "Foreign_Equities": 0.15, "Bitcoin": 0.05}},
                    {"end": 20, "weights": {"Harboursafe": 0.30, "Horizon": 0.20, "SkyHigh": 0.30, "Foreign_Equities": 0.15}},
                    {"end": 25, "weights": {"Harboursafe": 0.45, "Horizon": 0.25, "SkyHigh": 0.20, "Foreign_Equities": 0.10}},
                    {"end": 30, "weights": {"Harboursafe": 0.60, "Horizon": 0.25, "SkyHigh": 0.10, "Foreign_Equities": 0.05}},
                    {"end": 35, "weights": {"Harboursafe": 0.70, "Horizon": 0.20, "SkyHigh": 0.10}}
                ],
                has_partner="No",
                has_children="No",
                invested_real_estate="No",
                double_promotion_year=None,
                unforeseen_withdrawal_years=withdrawal_entries
            )

        shortfall_years = df_pre[df_pre["Withdrawal Shortfall"] > 0]

        if not shortfall_years.empty:
            st.warning("⚠️ Some withdrawals were capped due to insufficient corpus.")
            st.dataframe(shortfall_years[["Year", "Requested Withdrawal", "Unforeseen Withdrawal", "Withdrawal Shortfall"]])


        if st.button("🧹 Reset All Inputs"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.experimental_rerun()





        corpus_at_retirement = df_pre["Adjusted Fund Value"].iloc[-1]
        st.success(f"Simulation complete! Final corpus: ${corpus_at_retirement:,.2f}")
        

        df_post = simulate_post_retirement(
            corpus=corpus_at_retirement,               # from simulate_pre_retirement output
            start_age=30,                              # Emily's starting age
            years=25,                                  # Retirement years
            return_mean=0.05,                          # Average annual return post-retirement
            return_std=0.02,                           # Standard deviation of returns
            inflation=0.025,                           # Inflation rate
            lifestyle_base_today=70000,                # Lifestyle spending in today's terms
            lifestyle_improvement_pct=0.40,            # 40% increase in lifestyle post-retirement
            nz_super_annuity=23000,                    # Government pension in today’s dollars
            accumulation_years=35                      # Number of working years before retirement
        )

        

        # Metrics
        st.subheader("📊 Summary Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Investment", f"${df_pre['Total Contribution'].sum():,.0f}")
        col2.metric("Total Profit", f"${corpus_at_retirement - df_pre['Total Contribution'].sum():,.0f}")
        col3.metric("Corpus at Retirement", f"${corpus_at_retirement:,.0f}")


        
        # Generate a normal distribution around the final corpus value
        mu = corpus_at_retirement
        std = df_pre["Adjusted Fund Value"].std()
        n_simulated = 1000

        simulated_corpus = np.random.normal(mu, std, n_simulated)

        # Plot histogram with normal fit
        import scipy.stats as stats
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.histplot(simulated_corpus, kde=False, stat="density", bins=30, color="skyblue", ax=ax)

        # Add normal distribution line
        x = np.linspace(min(simulated_corpus), max(simulated_corpus), 100)
        p = stats.norm.pdf(x, mu, std)
        ax.plot(x, p, 'r', linewidth=2, label='Normal Fit')

        # Percentiles
        p5, p95 = np.percentile(simulated_corpus, [5, 95])

        # Draw vertical lines for mean, 5th, 95th
        ax.axvline(mu, color='green', linestyle='-', label=f'Mean: ${mu:,.0f}')
        ax.axvline(p5, color='gray', linestyle='--', label=f'5th Percentile: ${p5:,.0f}')
        ax.axvline(p95, color='gray', linestyle='--', label=f'95th Percentile: ${p95:,.0f}')

        # Title and labels
        ax.set_title("📈 Simulated Distribution of Corpus at Retirement")
        ax.set_xlabel("Corpus Value (NZD)")
        ax.set_ylabel("Density")
        ax.legend()
        ax.grid(True)

        # Streamlit display
        st.subheader("📈 Simulated Distribution of Final Corpus")
        st.pyplot(fig)




        # Visualizations
        st.subheader("📈 Pre-Retirement Fund Growth")
        fig1, ax1 = plt.subplots(figsize=(10, 4))
        ax1.plot(df_pre['Age'], df_pre['Adjusted Fund Value'], label='Total Corpus')
        ax1.set_xlabel("Age")
        ax1.set_ylabel("Fund Value")
        ax1.set_title("Fund Growth Over Time")
        ax1.legend()
        ax1.grid(True)
        plt.tight_layout()
        st.pyplot(fig1)

        st.subheader("📉 Post-Retirement Corpus Drawdown")
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.plot(df_post['Age'], df_post['Remaining Corpus'], label='Remaining Corpus', color='tab:red')
        ax2.set_xlabel("Age")
        ax2.set_ylabel("NZD")
        ax2.set_title("Post-Retirement Corpus Depletion")
        ax2.legend()
        ax2.grid(True)
        plt.tight_layout()
        st.pyplot(fig2)

        st.subheader("📊 Fund Returns Distribution")
        fig3, ax3 = plt.subplots(figsize=(10, 5))
        returns_data = df_pre[[col for col in df_pre.columns if 'Return' in col and 'FIF' not in col and 'Return Rate' not in col]]
        sns.boxplot(data=returns_data, ax=ax3)
        ax3.set_title("Boxplot of Annual Returns Across Funds")
        ax3.set_ylabel("Annual Return (NZD)")
        plt.xticks(rotation=30)
        plt.tight_layout()
        st.pyplot(fig3)



        # Tables
        st.subheader("📋 Detailed Pre-Retirement Summary")
        st.dataframe(df_pre.reset_index(drop=True))

        st.subheader("📋 Post-Retirement Summary")
        st.dataframe(df_post.reset_index(drop=True))


if __name__ == "__main__":
    main()

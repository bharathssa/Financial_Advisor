#Pre Retirement Code
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
import openpyxl

# Streamlit (used only when building web app)
import streamlit as st
# These are used in Jupyter Notebook environments
import ipykernel
import notebook
import jupyterlab

st.set_page_config(page_title="Emily's Retirement Planner", layout="wide")

# Parameters
initial_salary = 70000
hike_rate_mean = 0.05
hike_rate_std = 0.007
contribution_start = 0.06
contribution_increase_years = 3
contribution_increase_amount = 0.01
contribution_max = 0.15
lump_sum_amount = 10000
lump_sum_frequency = 5
start_lump_sum_year = 5
years = 35
start_age = 30
acc_levy = 0.0167
inflation_rate = 0.025
marginal_tax_rate = 0.30  # For FIF

# NZ tax brackets
nz_tax_brackets = [
    (0, 15600), (15601, 53500), (53501, 78100), (78101, 180000), (180001, float('inf'))
]
tax_rates = [0.105, 0.175, 0.30, 0.33, 0.39]

# Fund parameters
growth_rates = {
    "Harboursafe": {"mean": 0.0375, "std": 0.05},
    "Horizon": {"mean": 0.065, "std": 0.105},
    "SkyHigh": {"mean": 0.1025, "std": 0.2075},
    "Foreign_Equities": {"mean": 0.15, "std": np.sqrt(0.15**2 + 0.02**2)},
    "Bitcoin": {"mean": 0.20, "std": 0.60},
}

# Allocation strategy
# Updated dynamic allocation strategy with more aggressive early years
# and more conservative late-stage weights (horizontal format)

def get_allocation(year):
    if year <= 5: return {"Harboursafe": 0.05, "Horizon": 0.05, "SkyHigh": 0.45, "Foreign_Equities": 0.30, "Bitcoin": 0.15}
    elif year <= 10: return {"Harboursafe": 0.10, "Horizon": 0.10, "SkyHigh": 0.50, "Foreign_Equities": 0.20, "Bitcoin": 0.10}
    elif year <= 15: return {"Harboursafe": 0.20, "Horizon": 0.15, "SkyHigh": 0.45, "Foreign_Equities": 0.15, "Bitcoin": 0.05}
    elif year <= 20: return {"Harboursafe": 0.30, "Horizon": 0.20, "SkyHigh": 0.30, "Foreign_Equities": 0.15}
    elif year <= 25: return {"Harboursafe": 0.45, "Horizon": 0.25, "SkyHigh": 0.20, "Foreign_Equities": 0.10}
    elif year <= 30: return {"Harboursafe": 0.60, "Horizon": 0.25, "SkyHigh": 0.10, "Foreign_Equities": 0.05}
    else: return {"Harboursafe": 0.70, "Horizon": 0.20, "SkyHigh": 0.10}

# Tax calculation
def calculate_tax(salary, brackets, year, inflation=0.025):
    adjusted = [(b[0]*(1+inflation)**(year-1), b[1]*(1+inflation)**(year-1), r)
                for b, r in zip(brackets, tax_rates)]
    tax = 0
    for low, high, rate in adjusted:
        if salary > low:
            taxable = min(salary, high) - low
            tax += taxable * rate
        else:
            break
    return tax

# Simulation
records = []
salary = initial_salary
corpus = 0
prev_salary = None
foreign_corpus = 0

for year in range(1, years + 1):
    age = start_age + year - 1
    tax = calculate_tax(salary, nz_tax_brackets, year, inflation_rate)
    acc = acc_levy * salary
    net_salary = salary - tax - acc

    contrib_rate = min(contribution_start + ((year - 1) // contribution_increase_years) * contribution_increase_amount, contribution_max)
    emp_contrib = net_salary * contrib_rate
    employer_contrib = min(0.03, contrib_rate) * net_salary
    total_contrib = emp_contrib + employer_contrib

    lump_sum = 0
    if year >= start_lump_sum_year and (year - start_lump_sum_year + 1) % lump_sum_frequency == 0:
        lump_sum = lump_sum_amount
        total_contrib += lump_sum

    allocation = get_allocation(year)
    total_growth = 0
    fund_returns = {}
    fund_contributions = {}
    foreign_weight = allocation.get("Foreign_Equities", 0)
    foreign_contrib = total_contrib * foreign_weight

    # Foreign return calculation
    base_g = np.random.normal(0.12, 0.15)
    currency_g = np.random.normal(0.03, 0.02)
    foreign_return_rate = (1 + base_g) * (1 + currency_g) - 1
    foreign_return = foreign_corpus * foreign_return_rate
    foreign_corpus += foreign_contrib + foreign_return

    for fund, weight in allocation.items():
        g = np.random.normal(growth_rates[fund]["mean"], growth_rates[fund]["std"])
        if fund == "Foreign_Equities":
            g = foreign_return_rate
        contrib_val = total_contrib * weight
        fund_contributions[f"{fund} Contribution"] = round(contrib_val, 2)
        r = corpus * weight * g + contrib_val * 0.5
        total_growth += r
        fund_returns[f"{fund} Return"] = round(r, 2)

    fif_tax = foreign_corpus * 0.05 * marginal_tax_rate if foreign_corpus > 50000 else 0
    fif_tax_percent = (fif_tax / foreign_corpus * 100) if foreign_corpus > 0 else 0
    corpus = corpus + total_contrib + total_growth - fif_tax

    salary_change_value = salary - prev_salary if prev_salary is not None else 0
    salary_change_percent = (salary_change_value / prev_salary * 100) if prev_salary else 0
    prev_salary = salary

    records.append({
    "Year": year,
    "Age": age,

    # Salary & Deductions
    "Gross Salary": round(salary, 2),
    "Salary Hike Value": round(salary_change_value, 2),
    "Salary Hike %": round(salary_change_percent, 2),
    "Income Tax": round(tax, 2),
    "ACC Levy": round(acc, 2),
    "Net Salary": round(net_salary, 2),

    # Contributions
    "Employee Contribution Rate %": round(contrib_rate * 100, 2),
    "Employer Contribution Rate %": round(min(0.03, contrib_rate) * 100, 2),
    "Employee Contribution": round(emp_contrib, 2),
    "Employer Contribution": round(employer_contrib, 2),
    "Total Contribution": round(total_contrib, 2),
    "Lump Sum Added": round(lump_sum, 2),

    # Foreign Investment & Tax
    "Foreign Corpus": round(foreign_corpus, 2),
    "Foreign Return Rate": round(foreign_return_rate * 100, 2),
    "FIF Tax (NZD)": round(fif_tax, 2),
    "FIF Tax % of Foreign Value": round(fif_tax_percent, 2),

    # Fund-wise Contributions
    **fund_contributions,

    # Fund-wise Returns
    **fund_returns,

    # Final Portfolio Value
    "Adjusted Fund Value": round(corpus, 2)
})


    salary *= (1 + np.random.normal(hike_rate_mean, hike_rate_std))

# Final DataFrame
df_detailed = pd.DataFrame(records)

# Display
pd.set_option("display.float_format", lambda x: f"{x:,.2f}")
print("🔹 Detailed Yearly Summary with FIF Tax Applied:")
st.dataframe(df_detailed)



# --- POST-RETIREMENT WITHDRAWAL SIMULATION FUNCTION ---
def simulate_post_retirement(
    corpus,
    start_age,
    years,
    return_mean,
    return_std,
    inflation,
    lifestyle_base_today,
    lifestyle_improvement_pct,
    nz_super_annuity,
    accumulation_years
):
    data = []

    # Adjust lifestyle for improvement (e.g., 40% more than current)
    adjusted_lifestyle_today = lifestyle_base_today * (1 + lifestyle_improvement_pct)
    lifestyle_2060 = adjusted_lifestyle_today * ((1 + inflation) ** accumulation_years)

    # Adjust NZ Super to future nominal value
    nz_super_2060 = nz_super_annuity * ((1 + inflation) ** accumulation_years)

    # Simulate post-retirement drawdown
    for i in range(1, years + 1):
        year = accumulation_years + i
        age = start_age + year - 1

        # Lifestyle withdrawal adjusted for inflation annually
        desired_withdrawal = lifestyle_2060 * ((1 + inflation) ** (i - 1))
        govt_support = nz_super_2060 * ((1 + inflation) ** (i - 1))
        withdrawal = desired_withdrawal - govt_support  # net from corpus

        ret_rate = np.random.normal(return_mean, return_std)
        growth = corpus * ret_rate
        corpus = corpus + growth - withdrawal

        data.append({
            "Post-Retirement Year": year,
            "Age": age,
            "Target Lifestyle Spending": round(desired_withdrawal, 2),
            "Target Spending % of Corpus": round((desired_withdrawal / corpus) * 100, 2) if corpus > 0 else 0,
            "Govt Support (NZ Super)": round(govt_support, 2),
            "Withdrawal from Fund": round(withdrawal, 2),
            "Withdrawal % of Corpus": round((withdrawal / corpus) * 100, 2) if corpus > 0 else 0,
            "Annual Return Rate (%)": round(ret_rate * 100, 2),
            "Growth (NZD)": round(growth, 2),
            "Remaining Corpus": round(corpus, 2)
        })

    return pd.DataFrame(data)

# Example usage:
retirement_years = 25
inflation_rate = 0.025
lifestyle_base_today = 70000
lifestyle_improvement_pct = 0.40  # 40% improved lifestyle
return_mean = 0.05
return_std = 0.02
accumulation_years = 35
nz_super_annuity = 23000  # updated to reflect current approximate NZ Super for singles

df_post_retirement = simulate_post_retirement(
    corpus=corpus,
    start_age=start_age,
    years=retirement_years,
    return_mean=return_mean,
    return_std=return_std,
    inflation=inflation_rate,
    lifestyle_base_today=lifestyle_base_today,
    lifestyle_improvement_pct=lifestyle_improvement_pct,
    nz_super_annuity=nz_super_annuity,
    accumulation_years=accumulation_years
)

# Display the DataFrame
print("🔹 Post-Retirement Corpus Drawdown Summary:")
pd.set_option("display.float_format", lambda x: f"{x:,.2f}")
st.dataframe(df_post_retirement)


#Streamlit for Visuals
# === SECTION: STREAMLIT CONFIGURATION ===

def main():
    
    st.title("💼 Emily's Superannuation Fund & Retirement Planner")

    with st.sidebar:
        st.header("Adjust Pre-Retirement Parameters")
        initial_salary = st.number_input("Initial Salary (NZD)", value=70000, step=1000)
        hike_rate_mean = st.slider("Salary Hike Rate (Mean)", 0.0, 0.1, 0.05, 0.005)
        hike_rate_std = st.slider("Salary Hike Std Dev", 0.0, 0.05, 0.007, 0.001)

        contribution_start = st.slider("Starting Contribution Rate", 0.0, 0.2, 0.06, 0.01)
        contribution_max = st.slider("Max Contribution Rate", 0.0, 0.3, 0.15, 0.01)

        lump_sum_amount = st.number_input("Lump Sum Amount (Every 5 Years)", value=10000, step=500)

        st.divider()
        st.header("Adjust Post-Retirement Parameters")
        lifestyle_base_today = st.number_input("Current Lifestyle Spending (NZD)", value=70000, step=1000)
        lifestyle_improvement_pct = st.slider("Lifestyle Improvement %", 0.0, 1.0, 0.4, 0.05)
        nz_super_annuity = st.number_input("NZ Superannuation Today (NZD)", value=23000, step=1000)
        return_mean = st.slider("Post-Retirement Return (Mean)", 0.0, 0.1, 0.05, 0.005)
        return_std = st.slider("Return Std Dev", 0.0, 0.1, 0.02, 0.005)

    st.subheader("🔍 Simulation Overview")
    st.write("Your settings above define Emily's financial life from age 30 to 90.")
    st.markdown("""
    This dashboard is under development to include:
    - 📈 Pre-retirement corpus growth
    - 📉 Post-retirement drawdown
    - 🧾 Year-wise breakdown of salary, contributions, returns, and withdrawals
    - 💡 Insights: how long the corpus lasts, spending sustainability

    👉 Run your existing notebook code with the same parameters, then visualize the output here.
    """)
    st.info("To enable full interactivity, integrate your simulation results (dataframes) below.")

# This ensures that Streamlit runs properly as an app
if __name__ == '__main__':
    main()

# 💼 Financial Advisor — Retirement Planning Simulator

Financial Advisor is an interactive retirement planning dashboard built for New Zealand individuals and families. The app models your pre-retirement accumulation, fund allocation, and post-retirement drawdown with NZ Super support.

![Financial Advisor Screenshot](https://github.com/bharathssa/Financial_Advisor/blob/main/images/dasboard%20table%20view.png?raw=true)

---

## 🚀 Why this project

This repo helps you:

- Model salary growth, contributions, and living costs over a long accumulation horizon.
- Compare outcomes across Monte Carlo simulations to understand retirement risk.
- Visualize portfolio growth, asset allocation, and retirement drawdown.
- Estimate whether your retirement corpus is sufficient to support your lifestyle goals.

---

## ✨ What’s included

- `emily_streamlit_retirement_app.py` — interactive Streamlit dashboard
- `emily_pre_retirement.py` — pre-retirement accumulation engine
- `emily_post_retirement.py` — post-retirement drawdown engine
- `CSV Files/` — sample data storage
- `images/` — illustration screenshots used in README
- `requirements.txt` — Python dependencies

---

## 🔧 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/bharathssa/Financial_Advisor.git
   cd Financial_Advisor
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the Streamlit app:
   ```bash
   streamlit run emily_streamlit_retirement_app.py
   ```

---

## ✅ Key features

- Monte Carlo simulation of retirement corpus with 1,000 scenarios
- Pre-retirement salary, contributions, withdrawals, and fund allocation modeling
- Post-retirement drawdown evaluation with NZ Super support
- Risk analysis using 5th and 95th percentiles and funding sufficiency metrics
- Visual dashboards for corpus growth, outcome distribution, and fund returns

---

## 🎯 Recommended use

1. Adjust salary, contribution, and investment settings on the left sidebar.
2. Review the projected corpus distribution and retirement risk metrics.
3. Tweak lifestyle or contribution assumptions to improve retirement sustainability.

---

## 📘 How to interpret the visualizations

- The **corpus risk band** chart shows the median retirement balance plus the range of likely outcomes.
- The **distribution chart** explains how likely different final corpus values are, with the left tail showing the downside risk.
- The **cashflow view** compares salary, contribution, and spending trends over your working years.
- The **drawdown chart** shows whether your savings last through retirement and where shortfalls may appear.

---

## 🧩 Project structure

- `emily_pre_retirement.py` — simulates 36 years of income, expenses, contributions, and portfolio returns.
- `emily_post_retirement.py` — simulates retirement drawdown from age 66 to life expectancy.
- `emily_streamlit_retirement_app.py` — builds the Streamlit interface and visual summaries.

---

## 📌 Notes

- Allocation weights are normalized in the app to preserve a valid portfolio mix.
- The simulation uses randomized returns and expense behavior to surface risk outcomes.
- Use the dashboard to compare conservative vs. aggressive retirement plans.

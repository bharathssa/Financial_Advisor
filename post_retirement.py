import pandas as pd
import numpy as np
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
    accumulation_years,
    lifestyle_at_retirement=None,
    spending_basis="Manual lifestyle input"
):
    data = []

    if lifestyle_at_retirement is None:
        adjusted_lifestyle_today = lifestyle_base_today * (1 + lifestyle_improvement_pct)
        lifestyle_start = adjusted_lifestyle_today * ((1 + inflation) ** accumulation_years)
    else:
        lifestyle_start = lifestyle_at_retirement

    nz_super_2060 = nz_super_annuity * ((1 + inflation) ** accumulation_years)

    for i in range(1, years + 1):
        age = start_age + i - 1
        opening_corpus = corpus

        desired_withdrawal = lifestyle_start * ((1 + inflation) ** (i - 1))
        govt_support = nz_super_2060 * ((1 + inflation) ** (i - 1))
        withdrawal = max(0, desired_withdrawal - govt_support)
        income_surplus = max(0, govt_support - desired_withdrawal)

        ret_rate = np.random.normal(return_mean, return_std)
        growth = opening_corpus * ret_rate
        corpus = corpus + growth - withdrawal

        data.append({
            "Post-Retirement Year": i,
            "Age": age,
            "Opening Corpus": round(opening_corpus, 2),
            "Target Lifestyle Spending": round(desired_withdrawal, 2),
            "Target Spending % of Corpus": round((desired_withdrawal / opening_corpus) * 100, 2) if opening_corpus > 0 else 0,
            "Govt Support (NZ Super)": round(govt_support, 2),
            "Withdrawal from Fund": round(withdrawal, 2),
            "Withdrawal % of Corpus": round((withdrawal / opening_corpus) * 100, 2) if opening_corpus > 0 else 0,
            "Income Surplus": round(income_surplus, 2),
            "Annual Return Rate (%)": round(ret_rate * 100, 2),
            "Growth (NZD)": round(growth, 2),
            "Remaining Corpus": round(corpus, 2),
            "Spending Basis": spending_basis
        })

    return pd.DataFrame(data)

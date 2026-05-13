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
    accumulation_years
):
    data = []

    adjusted_lifestyle_today = lifestyle_base_today * (1 + lifestyle_improvement_pct)
    lifestyle_2060 = adjusted_lifestyle_today * ((1 + inflation) ** accumulation_years)
    nz_super_2060 = nz_super_annuity * ((1 + inflation) ** accumulation_years)

    for i in range(1, years + 1):
        age = start_age + i - 1  # ✅ Correct age progression

        desired_withdrawal = lifestyle_2060 * ((1 + inflation) ** (i - 1))
        govt_support = nz_super_2060 * ((1 + inflation) ** (i - 1))
        withdrawal = desired_withdrawal - govt_support

        ret_rate = np.random.normal(return_mean, return_std)
        growth = corpus * ret_rate
        corpus = corpus + growth - withdrawal

        data.append({
            "Post-Retirement Year": i,
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

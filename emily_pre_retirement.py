import pandas as pd
import numpy as np
import random

# --- SUPPORTING FUNCTIONS ---
def get_allocation(year, allocation_blocks):
    for block in allocation_blocks:
        if year <= block['end']:
            return block['weights']
    return allocation_blocks[-1]['weights']

def calculate_tax(salary, brackets, year, inflation=0.025):
    tax_rates = [0.105, 0.175, 0.30, 0.33, 0.39]
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

def simulate_pre_retirement(initial_salary, hike_rate_mean, hike_rate_std, contribution_start,
                                   contribution_increase_years, contribution_increase_amount, contribution_max,
                                   lump_sum_amount, lump_sum_frequency, start_lump_sum_year, years,
                                   start_age, acc_levy, inflation_rate, marginal_tax_rate, tax_brackets, growth_rates,
                                   allocation_blocks, has_partner='Auto', partner_contribution_perc = 'Auto', has_children='Auto', invested_real_estate='Auto',
                                   double_promotion_year=None, unforeseen_withdrawal_years=None):

    # --- Handle user-specified or probabilistic life events ---
    if has_partner == 'Auto':
        partner_year = None
        for y in range(1, 6):
            if random.random() < 0.4:
                partner_year = y
                break
        if partner_year is None:
            partner_year = 5
    else:
        partner_year = 1 if has_partner == "Yes" else years + 1

    if has_children == 'Auto':
        child_year = partner_year + 1
    else:
        child_year = 1 if has_children == "Yes" else years + 1

    if invested_real_estate == 'Auto':
        home_buy_year = random.randint(6, 11)
    else:
        home_buy_year = 10 if invested_real_estate == "Yes" else years + 1

    partner_status = ["Yes" if year >= partner_year else "No" for year in range(1, years + 1)]
    partner_contribution_perc = partner_contribution_perc
    child_status = ["Yes" if year >= child_year else "No" for year in range(1, years + 1)]

    rent_base = 0.25
    groceries_base = 0.15
    travel_base = 0.10
    utilities_base = 0.05
    insurance_base = 0.05
    leisure_base = 0.10
    misc_base = 0.05

    rent_upgrade_2y = 0.10
    rent_upgrade_5y = 0.15
    lifestyle_upgrade = 0.12

    salary = initial_salary
    corpus = 0
    foreign_corpus = 0
    prev_salary = None
    owns_home = False

    child_start_age = child_year
    child_duration = 18
    base_child_cost = 12000
    child_expenses = []

    records = []

    for year in range(1, years + 1):
        current_record_withdrawal = 0
        requested_withdrawal = 0  # Always reset each year
        current_record_withdrawal = 0

        age = start_age + year - 1
        tax = calculate_tax(salary, tax_brackets, year, inflation_rate)
        acc = acc_levy * salary
        net_salary = salary - tax - acc

        contrib_rate = min(contribution_start + ((year - 1) // contribution_increase_years) * contribution_increase_amount, contribution_max)
        emp_contrib = net_salary * contrib_rate
        employer_contrib = min(0.03, contrib_rate) * net_salary
        total_contrib = emp_contrib + employer_contrib

        if child_start_age <= age < child_start_age + child_duration:
            inflation_factor = (1 + inflation_rate) ** (age - child_start_age)
            child_expense = base_child_cost * inflation_factor
        else:
            child_expense = 0
        child_expenses.append(child_expense)

        lump_sum = 0
        if year >= start_lump_sum_year and (year - start_lump_sum_year+1) % lump_sum_frequency == 0:
            lump_sum = lump_sum_amount
            total_contrib += lump_sum

        if partner_status[year - 1] == "Yes":
            partner_contrib = salary * partner_contribution_perc
            total_contrib += partner_contrib

        if child_status[year - 1] == "Yes":
            child_cost = np.random.poisson(1500)
            net_salary -= child_cost
            total_contrib = max(0, total_contrib - child_cost * 0.1)

        if year == home_buy_year:
            corpus -= 60000  # downpayment
            owns_home = True

        if double_promotion_year is not None and year == double_promotion_year:
            salary *= 2
            lump_sum += 10000

        if unforeseen_withdrawal_years and year in unforeseen_withdrawal_years:
            if isinstance(unforeseen_withdrawal_years, dict):
                requested_withdrawal = unforeseen_withdrawal_years.get(year, np.random.randint(10000, 20000))
            else:
                requested_withdrawal = np.random.randint(10000, 20000)

            withdrawal = min(requested_withdrawal, corpus)
            corpus -= withdrawal
            current_record_withdrawal = withdrawal

        allocation = get_allocation(year, allocation_blocks)
        total_growth = 0
        fund_returns = {}
        fund_contributions = {}
        foreign_weight = allocation.get("Foreign_Equities", 0)
        foreign_contrib = total_contrib * foreign_weight

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
        corpus = corpus + total_contrib + total_growth - fif_tax - current_record_withdrawal

        salary_change_value = salary - prev_salary if prev_salary is not None else 0
        salary_change_percent = (salary_change_value / prev_salary * 100) if prev_salary else 0
        prev_salary = salary

        inflation_factor = (1 + inflation_rate) ** (year - 1)

        if not owns_home:
            if year % 2 == 0:
                rent_base *= (1 + rent_upgrade_2y)
            if year % 5 == 0:
                rent_base *= (1 + rent_upgrade_5y)

        if year % 5 == 0:
            groceries_base *= (1 + lifestyle_upgrade)
            travel_base *= (1 + lifestyle_upgrade)
            utilities_base *= (1 + lifestyle_upgrade)
            insurance_base *= (1 + lifestyle_upgrade)
            leisure_base *= (1 + lifestyle_upgrade)
            misc_base *= (1 + lifestyle_upgrade)

        rent = 0 if owns_home else net_salary * rent_base * inflation_factor
        groceries = net_salary * groceries_base * inflation_factor
        travel = net_salary * travel_base * inflation_factor
        utilities = net_salary * utilities_base * inflation_factor
        insurance = net_salary * insurance_base * inflation_factor
        leisure = net_salary * leisure_base * inflation_factor
        misc = net_salary * misc_base * inflation_factor

        child_exp = child_expenses[year - 1] if (year - 1) < len(child_expenses) else 0

        total_spent = rent + groceries + travel + utilities + insurance + leisure + misc + child_exp


        records.append({
            
            "Year": year,
            "Age": age,
            "Gross Salary": round(salary, 2),
            "Salary Hike Value": round(salary_change_value, 2),
            "Salary Hike %": round(salary_change_percent, 2),
            "Income Tax": round(tax, 2),
            "ACC Levy": round(acc, 2),
            "Net Salary": round(net_salary, 2),
            "Employee Contribution Rate %": round(contrib_rate * 100, 2),
            "Employer Contribution Rate %": round(min(0.03, contrib_rate) * 100, 2),
            "Employee Contribution": round(emp_contrib, 2),
            "Employer Contribution": round(employer_contrib, 2),
            "Total Contribution": round(total_contrib, 2),
            "Lump Sum Added": round(lump_sum, 2),
            "Foreign Corpus": round(foreign_corpus, 2),
            "Foreign Return Rate": round(foreign_return_rate * 100, 2),
            "FIF Tax (NZD)": round(fif_tax, 2),
            "FIF Tax % of Foreign Value": round(fif_tax_percent, 2),
            **fund_contributions,
            **fund_returns,
            "Rent": round(rent, 2),
            "Groceries": round(groceries, 2),
            "Travel": round(travel, 2),
            "Utilities": round(utilities, 2),
            "Insurance": round(insurance, 2),
            "Leisure": round(leisure, 2),
            "Misc": round(misc, 2),
            "Total Spent": round(total_spent, 2),
            "Partner Status": partner_status[year - 1],
            "Children Status": child_status[year - 1],
            "Owns Home": owns_home,
            "Unforeseen Withdrawal": round(current_record_withdrawal, 2) if 'current_record_withdrawal' in locals() else 0,
            "Requested Withdrawal": round(requested_withdrawal, 2) if 'requested_withdrawal' in locals() else 0,
            "Withdrawal Shortfall": round(requested_withdrawal - current_record_withdrawal, 2) if 'requested_withdrawal' in locals() else 0,
            "Adjusted Fund Value": round(corpus, 2)
        })

        salary *= (1 + np.random.normal(hike_rate_mean, hike_rate_std))

    return pd.DataFrame(records)

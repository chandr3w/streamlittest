#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Atas VC Portfolio Simulation Model", layout="wide")
sns.set(style="whitegrid")

st.title("Atas VC Portfolio Simulation Model")

# Fund parameters
st.sidebar.header("Fund Parameters")
fund_size = st.sidebar.number_input("Total Fund Size ($MM)", min_value=1, value=10, step=1) * 1e6
num_simulations = st.sidebar.slider("Number of Simulations", 10, 50, 20, step=5)

# Recycling
max_recycling_dollars = st.sidebar.number_input("Max Recycling ($MM)", min_value=0.0, max_value=5.0, value=2.0, step=0.1) * 1e6

# Investment Settings
st.sidebar.header("Seed Investment Settings")
seed_valuation_range = st.sidebar.slider("Seed Entry Valuation Range ($MM)", 10, 25, (8, 15), step=1)
seed_check_range = st.sidebar.slider("Seed Check Size Range ($K)", 250, 1000, (400, 600), step=25)
seed_dilution = st.sidebar.slider("Seed Dilution per Round (%)", 15, 35, 20)
seed_rounds_range = st.sidebar.slider("Seed Financing Rounds", 1, 10, (2, 5))

st.sidebar.header("Pre-Seed Investment Settings")
preseed_valuation_range = st.sidebar.slider("Pre-Seed Entry Valuation Range ($MM)", 2, 10, (6, 8), step=1)
preseed_check_range = st.sidebar.slider("Pre-Seed Check Size Range ($K)", 100, 400, (150, 300), step=25)
preseed_dilution = st.sidebar.slider("Pre-Seed Dilution per Round (%)", 15, 35, 20)
preseed_rounds_range = st.sidebar.slider("Pre-Seed Financing Rounds", 0, 10, (2, 6))
# Adjustable sliders for probabilities
small_exit_probability = st.sidebar.slider("Probability of Small Exit (%)", 20, 80, 50)
large_exit_probability = st.sidebar.slider("Probability of Large Exit (%)", 5, 30, 10)
medium_exit_probability = 100 - small_exit_probability - large_exit_probability
st.sidebar.write(f"Probability of Medium Exit (%): {medium_exit_probability}")

# Validate probability range
if medium_exit_probability < 0:
    st.sidebar.error("Probabilities exceed 100%. Adjust sliders.")

# Sliders for outcome sizes
small_exit_range = st.sidebar.slider("Small Exit Size ($MM)", 0, 10, (1, 2))
medium_exit_range = st.sidebar.slider("Medium Exit Size ($MM)", 10, 200, (20, 50))
large_exit_range = st.sidebar.slider("Large Exit Size ($B)", 1.0, 3.0, (1.0, 2.0), step=0.1)
# Function to run simulations
def run_simulation():
    avg_check_size = np.mean([seed_check_range[1]*1e3, preseed_check_range[1]*1e3])
    num_investments = int(fund_size / avg_check_size)

    investment_types = np.random.choice(['Seed', 'Pre-Seed'], num_investments, p=[0.6, 0.4])

    check_sizes = np.where(investment_types == 'Seed',
                           np.random.uniform(seed_check_range[0]*1e3, seed_check_range[1]*1e3, num_investments),
                           np.random.uniform(preseed_check_range[0]*1e3, preseed_check_range[1]*1e3, num_investments))

    entry_valuations = np.where(investment_types == 'Seed',
                                np.random.uniform(seed_valuation_range[0]*1e6, seed_valuation_range[1]*1e6, num_investments),
                                np.random.uniform(preseed_valuation_range[0]*1e6, preseed_valuation_range[1]*1e6, num_investments))

    future_rounds = np.where(investment_types == 'Seed',
                             np.random.randint(seed_rounds_range[0], seed_rounds_range[1]+1, num_investments),
                             np.random.randint(preseed_rounds_range[0], preseed_rounds_range[1]+1, num_investments))

    dilutions = np.where(investment_types == 'Seed', seed_dilution, preseed_dilution)

    big_exit_seed = np.random.rand(num_investments) < 1/10
    big_exit_preseed = np.random.rand(num_investments) < 1/10

    random_vals = np.random.rand(num_investments)
    exit_valuations = np.where(
        random_vals < small_exit_probability / 100,
        entry_valuations * np.random.uniform(1, 2, num_investments),
        np.where(
            random_vals < (small_exit_probability + medium_exit_probability) / 100,
            np.random.uniform(medium_exit_range[0]*1e6, medium_exit_range[1]*1e6, num_investments),
            np.random.uniform(large_exit_range[0]*1e9, large_exit_range[1]*1e9, num_investments)
        )
    )

    exit_times = future_rounds + 1 + np.where((big_exit_seed | big_exit_preseed), 2, 0)
    future_rounds += np.where((big_exit_seed | big_exit_preseed), 1, 0)

    ownership_entry = check_sizes / entry_valuations * 100
    ownership_exit = ownership_entry * ((100 - dilutions)/100)**future_rounds
    expected_exit = ownership_exit / 100 * exit_valuations

    recycled_amount = min(expected_exit.sum() * 0.2, max_recycling_dollars)
    total_paid_in = fund_size + recycled_amount

    moic = expected_exit.sum() / total_paid_in
    irr = ((moic ** (1 / np.mean(exit_times))) - 1) * 100

    return total_paid_in, expected_exit.sum(), moic, irr, num_investments, expected_exit, check_sizes

# Run multiple simulations
results = [run_simulation() for _ in range(num_simulations)]
paid_in_capitals, distributions, moics, irrs, num_investments_list, _, _ = zip(*results)

# Single sample for detailed visualization
_, _, _, _, _, sample_exits, sample_checks = run_simulation()

# Calculate summary stats
avg_paid_in = np.mean(paid_in_capitals)
avg_distributions = np.mean(distributions)
avg_moic = np.mean(moics)
avg_irr = np.mean(irrs)
avg_num_investments = np.mean(num_investments_list)

# Display summary statistics
st.subheader("Simulation Summary Statistics")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Avg. Paid-in Capital", f"${avg_paid_in:,.0f}")
col2.metric("Avg. Total Distributed", f"${avg_distributions:,.0f}")
col3.metric("Avg. Aggregate MOIC", f"{avg_moic:.2f}")
col4.metric("Avg. Aggregate IRR", f"{avg_irr:.2f}%")
col5.metric("Avg. Number of Investments", f"{avg_num_investments:.1f}")

# Visualization of simulation outcomes
st.subheader("Distribution of Simulation Outcomes")
fig, ax = plt.subplots(figsize=(8,4), dpi=100)
sns.histplot(moics, bins=15, kde=True, color='skyblue', ax=ax)
ax.set_xlabel('Fund Multiple (MOIC)')
ax.set_title('Distribution of Fund Multiples Across Simulations')
st.pyplot(fig)

# Visualization of single sample simulation (multiples)
st.subheader("Single Sample Simulation Results (Exit Multiples)")
fig, ax = plt.subplots(figsize=(8,4), dpi=100)
sns.barplot(x=np.arange(len(sample_exits)), y=sample_exits/sample_checks, palette="coolwarm", ax=ax)
ax.set_xlabel('Investment Number')
ax.set_ylabel('Exit Multiple')
ax.set_title('Exit Multiples for Individual Investments in a Single Simulation')
st.pyplot(fig)

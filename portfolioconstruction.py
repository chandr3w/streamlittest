#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="VC Portfolio Simulation Model", layout="wide")
sns.set(style="whitegrid")

st.title("📈 Enhanced VC Portfolio Simulation Model")

# Fund parameters
st.sidebar.header("Fund Parameters")
fund_size = st.sidebar.number_input("Total Fund Size ($MM)", min_value=1, value=10, step=1) * 1e6
num_simulations = st.sidebar.slider("Number of Simulations", 10, 50, 20, step=5)

# Recycling
max_recycling_dollars = st.sidebar.number_input("Max Recycling ($MM)", min_value=0.0, max_value=5.0, value=2.0, step=0.1) * 1e6

# Investment Settings
st.sidebar.header("Seed Investment Settings")
seed_valuation_range = st.sidebar.slider("Seed Entry Valuation Range ($MM)", 10, 50, (15, 25), step=1)
seed_check_range = st.sidebar.slider("Seed Check Size Range ($K)", 250, 1000, (400, 600), step=25)
seed_dilution = st.sidebar.slider("Seed Dilution per Round (%)", 15, 35, 25)
seed_rounds_range = st.sidebar.slider("Seed Financing Rounds", 1, 6, (2, 4))

st.sidebar.header("Pre-Seed Investment Settings")
preseed_valuation_range = st.sidebar.slider("Pre-Seed Entry Valuation Range ($MM)", 2, 10, (4, 6), step=1)
preseed_check_range = st.sidebar.slider("Pre-Seed Check Size Range ($K)", 100, 400, (150, 300), step=25)
preseed_dilution = st.sidebar.slider("Pre-Seed Dilution per Round (%)", 10, 25, 15)
preseed_rounds_range = st.sidebar.slider("Pre-Seed Financing Rounds", 2, 7, (3, 5))

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

    big_exit_seed = np.random.rand(num_investments) < 1/8
    big_exit_preseed = np.random.rand(num_investments) < 1/10

    exit_valuations = np.where(
        (investment_types == 'Seed') & big_exit_seed, np.random.uniform(1e9, 2e9, num_investments),
        np.where((investment_types == 'Pre-Seed') & big_exit_preseed, np.random.uniform(1e9, 2e9, num_investments), np.random.uniform(20e6, 300e6, num_investments))
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

    return total_paid_in, expected_exit.sum(), moic, irr, num_investments

# Run multiple simulations
results = [run_simulation() for _ in range(num_simulations)]
paid_in_capitals, distributions, moics, irrs, num_investments_list = zip(*results)

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

# Visualization (smaller figure)
st.subheader("Distribution of Simulation Outcomes")
fig, ax = plt.subplots(figsize=(8,4), dpi=100)
sns.histplot(moics, bins=15, kde=True, color='skyblue', ax=ax)
ax.set_xlabel('Fund Multiple (MOIC)')
ax.set_title('Distribution of Fund Multiples Across Simulations')
st.pyplot(fig)


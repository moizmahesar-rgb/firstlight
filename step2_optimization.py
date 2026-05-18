"""
Pumped Hydro Optimization - Dynamic Programming
June 24, 2025 | 1000 MW, 8000 MWh, 75% efficiency

Storage is tracked in deliverable MWh. Pumping adds 750 MWh and 
generation removes 1,000 MWh, reflecting 75% round-trip efficiency.
"""
import pandas as pd
from functools import lru_cache
from config import ASSET

pricing = pd.read_csv('pricing_data.csv')
assert len(pricing) == 24, "Expected 24 hourly records."

MW = ASSET["capacity_mw"]
EFF = ASSET["round_trip_efficiency"]
MAX_STORAGE = ASSET["storage_capacity_mwh"]

PUMP_ADDITION = MW * EFF          # 750 MWh added to storage
GEN_REQUIREMENT = MW              # 1000 MWh removed from storage

print("\n" + "="*80)
print("PUMPED HYDRO OPTIMIZATION - DYNAMIC PROGRAMMING")
print("="*80)

# Validate data
required_cols = ['da_lmp', 'rt_lmp', 'tmnsr_price', 'strike_price']
if pricing[required_cols].isna().any().any():
    raise ValueError("Missing pricing data. Check pricing_data.csv.")

action_taken = {}

@lru_cache(None)
def solve(hour, storage_mwh):
    """
    DP: maximum revenue from hour onwards, starting with given storage.
    """
    if hour == 24:
        return 0

    da_price = pricing.iloc[hour]['da_lmp']
    rt_lmp = pricing.iloc[hour]['rt_lmp']
    tmnsr_price = pricing.iloc[hour]['tmnsr_price']
    strike_price = pricing.iloc[hour]['strike_price']

    closeout_charge = rt_lmp - strike_price
    net_tmnsr_price = max(tmnsr_price - closeout_charge, 0)
    tmnsr_revenue = MW * net_tmnsr_price

    options = []

    # IDLE
    options.append((
        solve(hour + 1, storage_mwh),
        'IDLE',
        storage_mwh
    ))

    # TMNSR
    options.append((
        tmnsr_revenue + solve(hour + 1, storage_mwh),
        'TMNSR',
        storage_mwh
    ))

    # PUMP
    if storage_mwh + PUMP_ADDITION <= MAX_STORAGE:
        pump_cost = MW * da_price
        next_storage = storage_mwh + PUMP_ADDITION
        options.append((
            -pump_cost + solve(hour + 1, next_storage),
            'PUMP',
            next_storage
        ))

    # GENERATE
    if storage_mwh >= GEN_REQUIREMENT:
        gen_revenue = MW * da_price
        next_storage = storage_mwh - GEN_REQUIREMENT
        options.append((
            gen_revenue + solve(hour + 1, next_storage),
            'GENERATE',
            next_storage
        ))

    best_revenue, best_action, best_next_storage = max(options, key=lambda x: x[0])
    action_taken[(hour, storage_mwh)] = (best_action, best_next_storage)

    return best_revenue

optimal_revenue = solve(0, 0)
print(f"\nOptimal revenue: ${optimal_revenue:,.0f}")

dispatch = []
storage_mwh = 0
total_energy = 0
total_tmnsr = 0

print("\n" + "="*80)
print("HOURLY DISPATCH")
print("="*80 + "\n")

for hour in range(24):
    starting_storage = storage_mwh
    action, ending_storage = action_taken[(hour, storage_mwh)]

    da_price = pricing.iloc[hour]['da_lmp']
    rt_lmp = pricing.iloc[hour]['rt_lmp']
    tmnsr_price = pricing.iloc[hour]['tmnsr_price']
    strike_price = pricing.iloc[hour]['strike_price']

    closeout_charge = rt_lmp - strike_price
    net_tmnsr_price = max(tmnsr_price - closeout_charge, 0)

    energy_revenue = 0
    tmnsr_revenue = 0

    if action == 'PUMP':
        energy_revenue = -MW * da_price
    elif action == 'GENERATE':
        energy_revenue = MW * da_price
    elif action == 'TMNSR':
        tmnsr_revenue = MW * net_tmnsr_price

    hourly_revenue = energy_revenue + tmnsr_revenue
    total_energy += energy_revenue
    total_tmnsr += tmnsr_revenue

    dispatch.append({
        'hour': hour + 1,
        'action': action,
        'starting_storage_mwh': starting_storage,
        'ending_storage_mwh': ending_storage,
        'da_lmp': da_price,
        'rt_lmp': rt_lmp,
        'tmnsr_price': tmnsr_price,
        'strike_price': strike_price,
        'closeout_charge': closeout_charge,
        'net_tmnsr_price': net_tmnsr_price,
        'energy_revenue': energy_revenue,
        'tmnsr_revenue': tmnsr_revenue,
        'hourly_revenue': hourly_revenue
    })

    print(
        f"Hour {hour+1:2d}: {action:8s} | "
        f"Revenue: ${hourly_revenue:>11,.0f} | "
        f"Storage: {starting_storage:>7.0f} → {ending_storage:>7.0f} MWh"
    )

    storage_mwh = ending_storage

results_df = pd.DataFrame(dispatch)
results_df.to_csv('dispatch_results.csv', index=False)

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Energy Arbitrage:  ${total_energy:>15,.0f}")
print(f"TMNSR Reserves:    ${total_tmnsr:>15,.0f}")
print(f"{'-'*50}")
print(f"TOTAL REVENUE:     ${optimal_revenue:>15,.0f}")
print(f"Final Storage:     {storage_mwh:>15,.0f} MWh")
print("\n✓ dispatch_results.csv saved\n")
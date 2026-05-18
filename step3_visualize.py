import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

results = pd.read_csv('dispatch_results.csv')
pricing = pd.read_csv('pricing_data.csv')

hours = results['hour'].values
actions = results['action'].values
storage = results['ending_storage_mwh'].values
revenues = results['hourly_revenue'].values
da_prices = pricing['da_lmp'].values

hours_plot = np.array([0] + list(hours))
storage_plot = [0] + list(storage)
cum_revenue = np.cumsum([0] + list(revenues))

colors = {'PUMP': '#d62728', 'GENERATE': '#2ca02c', 'TMNSR': '#ff7f0e', 'IDLE': '#cccccc'}

fig, ax = plt.subplots(2, 2, figsize=(16, 10))
fig.suptitle('Pumped Hydro Optimization - June 24, 2025',
             fontsize=16, fontweight='bold')

ax[0,0].plot(hours, da_prices, 'b-', linewidth=2.5)
for h, a in zip(hours, actions):
    if a != 'IDLE':
        ax[0,0].scatter(h, da_prices[h-1], s=150, color=colors[a], edgecolor='black', linewidth=1.5)
ax[0,0].set_title('Prices with Dispatch', fontsize=12, fontweight='bold')
ax[0,0].set_ylabel('Price ($/MWh)')
ax[0,0].grid(True, alpha=0.3)

ax[0,1].fill_between(hours_plot, storage_plot, alpha=0.3, color='steelblue')
ax[0,1].plot(hours_plot, storage_plot, 'b-', linewidth=2.5)
ax[0,1].axhline(y=8000, color='r', linestyle='--', linewidth=1.5, alpha=0.7)
ax[0,1].set_title('Storage Level', fontsize=12, fontweight='bold')
ax[0,1].set_ylabel('MWh')
ax[0,1].grid(True, alpha=0.3)

colors_list = [colors[a] for a in actions]
ax[1,0].bar(hours, revenues, color=colors_list, edgecolor='black', linewidth=0.8)
ax[1,0].axhline(y=0, color='black', linewidth=1)
ax[1,0].set_title('Hourly Revenue', fontsize=12, fontweight='bold')
ax[1,0].set_ylabel('Revenue ($)')
ax[1,0].grid(True, alpha=0.3, axis='y')

ax[1,1].fill_between(hours_plot, cum_revenue, alpha=0.3, color='green')
ax[1,1].plot(hours_plot, cum_revenue, 'g-', linewidth=2.5)
ax[1,1].set_title('Cumulative Revenue', fontsize=12, fontweight='bold')
ax[1,1].set_ylabel('Revenue ($)')
ax[1,1].grid(True, alpha=0.3)
final = cum_revenue[-1]
ax[1,1].text(16, final * 0.75, f'Total: ${final:,.0f}', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

plt.tight_layout()
plt.savefig('dispatch_analysis.png', dpi=150)
print("✓ dispatch_analysis.png saved")
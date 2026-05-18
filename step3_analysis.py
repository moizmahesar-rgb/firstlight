import pandas as pd
import matplotlib.pyplot as plt

class DispatchAnalyzer:
    """
    Makes charts showing what the optimizer decided to do.
    """
    
    def __init__(self, results_csv="dispatch_results.csv"):
        self.results = pd.read_csv(results_csv)
    
    def create_charts(self):
        """
        Makes 4 charts:
        1. Prices with dispatch decisions overlaid
        2. Storage level throughout the day
        3. Revenue breakdown by hour
        4. Cumulative revenue
        """
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Pumped Hydro Optimization - June 24, 2025', fontsize=14)
        
        hours = self.results['hour']
        
        # Chart 1: Prices with dispatch
        ax1 = axes[0, 0]
        ax1.plot(hours, self.results['da_lmp'], 'b-', linewidth=2, label='DA Price')
        
        # Color code by action
        colors = {'PUMP': 'red', 'GENERATE': 'green', 'TMNSR': 'orange', 'IDLE': 'gray'}
        for action in ['PUMP', 'GENERATE', 'TMNSR', 'IDLE']:
            mask = self.results['action'] == action
            if mask.any():
                ax1.scatter(hours[mask], self.results.loc[mask, 'da_lmp'], 
                           s=80, alpha=0.6, color=colors[action], label=action)
        
        ax1.set_xlabel('Hour')
        ax1.set_ylabel('Price ($/MWh)')
        ax1.set_title('Prices with Dispatch Decisions')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Chart 2: Storage level
        ax2 = axes[0, 1]
        ax2.fill_between(hours, self.results['storage_mwh'], alpha=0.3, color='blue')
        ax2.plot(hours, self.results['storage_mwh'], 'b-', linewidth=2)
        ax2.axhline(y=8000, color='r', linestyle='--', label='Max (8000 MWh)')
        ax2.set_xlabel('Hour')
        ax2.set_ylabel('Storage (MWh)')
        ax2.set_title('Storage Level Throughout Day')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Chart 3: Hourly revenue
        ax3 = axes[1, 0]
        colors_revenue = [colors.get(action, 'gray') for action in self.results['action']]
        ax3.bar(hours, self.results['revenue'], color=colors_revenue, alpha=0.7)
        ax3.set_xlabel('Hour')
        ax3.set_ylabel('Revenue ($)')
        ax3.set_title('Hourly Revenue by Action')
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Chart 4: Cumulative revenue
        ax4 = axes[1, 1]
        cumulative = self.results['revenue'].cumsum()
        ax4.plot(hours, cumulative, 'g-', linewidth=2.5, marker='o')
        ax4.fill_between(hours, cumulative, alpha=0.2, color='green')
        ax4.set_xlabel('Hour')
        ax4.set_ylabel('Cumulative Revenue ($)')
        ax4.set_title('Cumulative Daily Revenue')
        ax4.grid(True, alpha=0.3)
        
        total = cumulative.iloc[-1]
        ax4.text(0.98, 0.05, f'Total: ${total:,.0f}', 
                transform=ax4.transAxes, fontsize=11, fontweight='bold',
                ha='right', va='bottom',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        plt.tight_layout()
        plt.savefig('dispatch_analysis.png', dpi=150, bbox_inches='tight')
        print("✓ Chart saved to dispatch_analysis.png\n")
        plt.show()
    
    def print_summary(self):
        """Print text summary of the results."""
        
        print("\n" + "="*70)
        print("ANALYSIS SUMMARY")
        print("="*70 + "\n")
        
        # Breakdown by action
        pump_hours = len(self.results[self.results['action'] == 'PUMP'])
        gen_hours = len(self.results[self.results['action'] == 'GENERATE'])
        tmnsr_hours = len(self.results[self.results['action'] == 'TMNSR'])
        idle_hours = len(self.results[self.results['action'] == 'IDLE'])
        
        print("DISPATCH BREAKDOWN:")
        print(f"  Pump hours:         {pump_hours}")
        print(f"  Generate hours:     {gen_hours}")
        print(f"  TMNSR hours:        {tmnsr_hours}")
        print(f"  Idle hours:         {idle_hours}")
        
        # Revenue breakdown
        energy_rev = self.results[self.results['action'].isin(['PUMP', 'GENERATE'])]['revenue'].sum()
        reserve_rev = self.results[self.results['action'] == 'TMNSR']['revenue'].sum()
        total = self.results['revenue'].sum()
        
        print("\nREVENUE:")
        print(f"  Energy arbitrage:   ${energy_rev:>12,.0f}")
        print(f"  Reserves (TMNSR):   ${reserve_rev:>12,.0f}")
        print(f"  {'─'*40}")
        print(f"  TOTAL:              ${total:>12,.0f}")
        
        # Price stats
        print("\nPRICE STATISTICS:")
        print(f"  Min price:          ${self.results['da_lmp'].min():>12.2f}/MWh")
        print(f"  Max price:          ${self.results['da_lmp'].max():>12.2f}/MWh")
        print(f"  Avg price:          ${self.results['da_lmp'].mean():>12.2f}/MWh")
        
        # Storage stats
        print("\nSTORAGE:")
        print(f"  Peak storage:       {self.results['storage_mwh'].max():>12.1f} MWh")
        print(f"  Final storage:      {self.results['storage_mwh'].iloc[-1]:>12.1f} MWh")
        
        print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    try:
        analyzer = DispatchAnalyzer("dispatch_results.csv")
        analyzer.print_summary()
        analyzer.create_charts()
    except FileNotFoundError:
        print("Error: dispatch_results.csv not found")
        print("Run step 2 first: python3 step2_optimization.py")
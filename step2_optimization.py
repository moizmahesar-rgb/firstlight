import pandas as pd
from config import *

class PumpedHydroOptimizer:
    """
    Optimizes dispatch for a 1000 MW pumped hydro asset on June 24, 2025.
    
    The basic idea: buy electricity when it's cheap, store it, sell it when 
    it's expensive. Also get paid for providing reserve capacity when we're 
    not doing anything else.
    
    How it works:
    
    Step 1: Look at all 24 hours of prices. Find every hour where we could 
    pump cheap electricity into storage, then later discharge it at a higher 
    price and make money. Account for the fact that we lose 25% of the energy 
    (75% efficient round trip).
    
    Step 2: Rank these pump-discharge pairs by how much money they make. Do 
    the most profitable ones first, until we run out of storage space or 
    good trades.
    
    Step 3: Any hour we're not using for energy trading, check if we can make 
    money offering reserve capacity (TMNSR). If the payment is high enough, 
    offer it.
    
    Why this approach works:
    - For a single day where we know all the prices, doing the highest-profit 
      trades first is optimal
    - We respect the physical constraints (can't store more than 8000 MWh, 
      can't output more than 1000 MW)
    - The logic is simple enough to explain
    
    Where this falls short in the real world:
    - We're pretending we know all tomorrow's prices perfectly. Actually you 
      forecast, and you're usually wrong.
    - We assume we can ramp up or down instantly. Real turbines take time to 
      spin up.
    - TMNSR in real life is more complex - you commit to it in a forward 
      market, then it gets co-optimized in real-time dispatch.
    - We're not modeling ramp rates, maintenance windows, environmental 
      releases, any of that.
    - We're assuming everything executes perfectly.
    
    But for this assignment, it shows the key concepts: arbitrage on spread, 
    efficiency loss matters, reserves are secondary revenue.
    """
    
    def __init__(self, pricing_data):
        self.pricing = pricing_data.reset_index(drop=True)
        self.capacity = ASSET["capacity_mw"]
        self.storage_cap = ASSET["storage_capacity_mwh"]
        self.efficiency = ASSET["round_trip_efficiency"]
        
        self.storage = ASSET["initial_storage_mwh"]
        self.results = []
        self.committed_pairs = []
    
    def calculate_tmnsr_revenue(self, mw, tmnsr_price, rt_lmp, strike_price):
        """
        Figure out how much money we make on a TMNSR (reserve) position.
        
        ISO-NE pays us a price to sit around with generation ready to go.
        But if electricity prices spike in real-time, we have to back down 
        and we lose money.
        
        Formula: Revenue = MW * MAX(TMNSR Price - Closeout, 0)
        Closeout = max(0, Real-Time Price - Strike Price)
        
        Example:
        We get paid $10/MW to provide reserves.
        The strike price they set is $50/MWh.
        Real-time price ends up at $65/MWh.
        So we lose $65-50 = $15 on the closeout.
        Net: $10 - $15 = -$5. We lose money.
        
        That's why we only take TMNSR if the payment is high enough to cover 
        the downside risk.
        """
        closeout = max(0, rt_lmp - strike_price)
        net_revenue = mw * max(tmnsr_price - closeout, 0)
        return net_revenue
    
    def phase1_identify_opportunities(self):
        """
        Find all the pump-to-discharge trades that would make money.
        
        For each hour, look ahead. If we pump now at price X, and later 
        discharge at price Y, do we make money after accounting for the 
        25% efficiency loss?
        
        Keep only the trades where profit is positive.
        """
        opportunities = []
        
        for pump_hour in range(len(self.pricing)):
            pump_price = self.pricing.iloc[pump_hour]['da_lmp']
            
            for gen_hour in range(pump_hour + 1, len(self.pricing)):
                gen_price = self.pricing.iloc[gen_hour]['da_lmp']
                
                # The math: we pay pump_price to store energy. 
                # We sell at gen_price but only get 75% of it back.
                # Profit = (gen_price * 0.75) - pump_price
                profit_per_mwh = (gen_price * self.efficiency) - pump_price
                
                if profit_per_mwh > 0:
                    total_profit = profit_per_mwh * self.capacity
                    
                    opportunities.append({
                        'pump_h': pump_hour,
                        'gen_h': gen_hour,
                        'pump_price': pump_price,
                        'gen_price': gen_price,
                        'spread': gen_price - pump_price,
                        'profit_per_mwh': profit_per_mwh,
                        'total_profit': total_profit,
                    })
        
        # Sort biggest money makers first
        opportunities.sort(key=lambda x: x['total_profit'], reverse=True)
        return opportunities
    
    def phase2_execute_trades(self, opportunities):
        """
        Do the most profitable trades first. Stop when we run out of storage 
        space or good trades.
        
        This is greedy - we take the best trades in order. In a world with 
        uncertainty, you'd use dynamic programming or stochastic optimization 
        to think about future opportunities. But with perfect hindsight, greedy 
        is fine.
        """
        for opp in opportunities:
            pump_h = opp['pump_h']
            gen_h = opp['gen_h']
            
            # Pumping 1000 MW for 1 hour = 1000 MWh of storage needed
            mwh_to_pump = self.capacity * 1
            
            available_storage = self.storage_cap - self.storage
            
            if mwh_to_pump <= available_storage:
                self.committed_pairs.append(opp)
                self.storage += mwh_to_pump
    
    def optimize(self):
        """
        Run the full optimization and build the dispatch schedule.
        """
        
        print("\n" + "="*70)
        print("OPTIMIZATION")
        print("="*70 + "\n")
        
        # Step 1: Find all profitable trades
        print("Step 1: Finding all profitable pump-discharge pairs...\n")
        
        opportunities = self.phase1_identify_opportunities()
        
        print(f"Found {len(opportunities)} profitable pairs\n")
        
        if len(opportunities) > 0:
            print("Top 5 by profit:")
            for i, opp in enumerate(opportunities[:5]):
                print(f"  {i+1}. Hour {opp['pump_h']+1} (${opp['pump_price']:6.2f}) "
                      f"→ Hour {opp['gen_h']+1} (${opp['gen_price']:6.2f}) | "
                      f"Profit: ${opp['total_profit']:>10,.0f}")
        
        # Step 2: Execute trades
        print("\n" + "="*70)
        print("Step 2: Executing trades (biggest profit first)\n")
        
        self.phase2_execute_trades(opportunities)
        
        print(f"Executed {len(self.committed_pairs)} trades:\n")
        
        # Set up dispatch schedule
        dispatch = []
        for hour in range(24):
            dispatch.append({
                'hour': hour + 1,
                'action': 'IDLE',
                'mw': 0,
                'revenue': 0,
                'da_lmp': self.pricing.iloc[hour]['da_lmp'],
                'rt_lmp': self.pricing.iloc[hour]['rt_lmp'],
                'tmnsr_price': self.pricing.iloc[hour]['tmnsr_price'],
                'strike_price': self.pricing.iloc[hour]['strike_price'],
                'storage_mwh': 0,
            })
        
        # Mark the pump and discharge hours
        for i, pair in enumerate(self.committed_pairs):
            pump_h = pair['pump_h']
            gen_h = pair['gen_h']
            pump_price = pair['pump_price']
            gen_price = pair['gen_price']
            profit = pair['total_profit']
            
            dispatch[pump_h]['action'] = 'PUMP'
            dispatch[pump_h]['mw'] = self.capacity
            dispatch[pump_h]['revenue'] = -pump_price * self.capacity
            
            dispatch[gen_h]['action'] = 'GENERATE'
            dispatch[gen_h]['mw'] = self.capacity
            dispatch[gen_h]['revenue'] = gen_price * self.capacity * self.efficiency
            
            print(f"  Trade {i+1}: Hour {pump_h+1} PUMP @ ${pump_price:6.2f} "
                  f"→ Hour {gen_h+1} GEN @ ${gen_price:6.2f} | "
                  f"${profit:>10,.0f}")
        
        # Step 3: Fill idle hours with TMNSR if profitable
        print("\n" + "="*70)
        print("Step 3: Offering reserves (TMNSR) for idle hours\n")
        
        tmnsr_allocated = 0
        tmnsr_revenue_total = 0
        
        for hour in range(24):
            if dispatch[hour]['action'] == 'IDLE':
                tmnsr_price = dispatch[hour]['tmnsr_price']
                rt_lmp = dispatch[hour]['rt_lmp']
                strike = dispatch[hour]['strike_price']
                
                rev = self.calculate_tmnsr_revenue(
                    self.capacity, tmnsr_price, rt_lmp, strike
                )
                
                if rev > 0:
                    dispatch[hour]['action'] = 'TMNSR'
                    dispatch[hour]['mw'] = self.capacity
                    dispatch[hour]['revenue'] = rev
                    tmnsr_allocated += 1
                    tmnsr_revenue_total += rev
        
        print(f"Allocated {tmnsr_allocated} hours to TMNSR reserves")
        if tmnsr_allocated > 0:
            print(f"Total TMNSR revenue: ${tmnsr_revenue_total:,.0f}")
        
        # Build the final schedule with storage tracking
        print("\n" + "="*70)
        print("HOURLY DISPATCH")
        print("="*70 + "\n")
        
        self.storage = ASSET["initial_storage_mwh"]
        
        for hour in range(24):
            action = dispatch[hour]['action']
            mw = dispatch[hour]['mw']
            
            if action == 'PUMP':
                # Add energy to storage
                self.storage += mw * 1
                self.storage = min(self.storage, self.storage_cap)
            elif action == 'GENERATE':
                # Remove energy from storage (takes more than we get back)
                self.storage -= mw * 1 / self.efficiency
                self.storage = max(self.storage, 0)
            
            dispatch[hour]['storage_mwh'] = self.storage
            
            da_lmp = dispatch[hour]['da_lmp']
            revenue = dispatch[hour]['revenue']
            revenue_str = f"${revenue:>9,.0f}"
            
            print(f"Hour {hour+1:2d}: {action:8s} | "
                  f"Price: ${da_lmp:6.2f}/MWh | "
                  f"Revenue: {revenue_str} | "
                  f"Storage: {self.storage:7.1f} MWh")
        
        self.results = dispatch
        return pd.DataFrame(dispatch)
    
    def print_summary(self):
        """Print out the total revenue and where it came from."""
        df = pd.DataFrame(self.results)
        
        total = df['revenue'].sum()
        energy_mask = df['action'].isin(['PUMP', 'GENERATE'])
        energy_revenue = df[energy_mask]['revenue'].sum()
        
        reserve_mask = df['action'] == 'TMNSR'
        reserve_revenue = df[reserve_mask]['revenue'].sum()
        
        print("\n" + "="*70)
        print("REVENUE SUMMARY")
        print("="*70)
        print(f"Energy Arbitrage:              ${energy_revenue:>12,.0f}")
        print(f"Reserves (TMNSR):              ${reserve_revenue:>12,.0f}")
        print(f"{'─' * 50}")
        print(f"TOTAL:                         ${total:>12,.0f}")
        print("="*70 + "\n")
        
        return total
    
    def save_results(self, filename="dispatch_results.csv"):
        """Save the dispatch schedule to a CSV file."""
        df = pd.DataFrame(self.results)
        df.to_csv(filename, index=False)
        print(f"Saved results to {filename}")
        return df


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PUMPED HYDRO OPTIMIZATION")
    print("June 24, 2025 | 1000 MW | 8000 MWh storage | 75% efficiency")
    print("="*70)
    
    try:
        pricing = pd.read_csv("pricing_data.csv")
        print(f"\nLoaded {len(pricing)} hours of pricing data\n")
        
        optimizer = PumpedHydroOptimizer(pricing)
        results = optimizer.optimize()
        
        optimizer.print_summary()
        optimizer.save_results()
        
    except FileNotFoundError:
        print("\nError: pricing_data.csv not found")
        print("Run step 1 first: python3 step1_data_collection.py")
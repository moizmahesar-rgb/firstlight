# Pumped Hydro Asset Optimization: FirstLight Power

**June 24, 2025 - ISO-NE Day-Ahead Energy and TMNSR Markets**

## Executive Summary

This project optimizes daily revenue for a 1,000 MW pumped hydro asset operating in ISO-NE day-ahead energy and TMNSR (Ten-Minute Non-Spinning Reserve) markets. Using dynamic programming, the model determines optimal hourly dispatch decisions to maximize combined energy arbitrage and reserve revenue.

**Optimal Daily Revenue: $2,494,580**
- Energy Arbitrage: $1,868,570 (75%)
- TMNSR Reserves: $626,010 (25%)

## Problem Statement

An operator controls a 1,000 MW reversible pump-turbine unit with 8,000 MWh storage capacity. The unit must:
- Start with empty storage (0 MWh)
- Operate within capacity constraints (0 to 8,000 MWh)
- Apply 75% round-trip efficiency (pump input loss)
- Decide hourly: pump, generate, provide reserve, or idle
- Maximize total daily revenue across all markets

**Assumptions:**
- Perfect foresight of all 24-hour prices
- Asset can instantly ramp to full 1,000 MW capacity
- No operational constraints (ramping, minimum run times, outages)
- TMNSR reserves assumed not to deplete inventory

## Solution Approach

### Algorithm: Dynamic Programming

At each hour `h` and storage state `s`, the optimizer solves:

```
dp[h][s] = max(action ∈ {IDLE, TMNSR, PUMP, GENERATE})
         = max(revenue[action] + dp[h+1][s'])

Where:
  IDLE:     0 + dp[h+1][s]
  TMNSR:    tmnsr_revenue(h) + dp[h+1][s]
  PUMP:     -cost(h) + dp[h+1][s+750]     if s+750 ≤ 8,000
  GENERATE: revenue(h) + dp[h+1][s-1,000] if s ≥ 1,000
```

**State Space:** 24 hours × ~11 feasible storage levels (due to 750/1,000 MWh increments)  
**Computational Complexity:** O(24 × 11 × 4) = O(1,056) operations  
**Guarantee:** Optimal solution (no approximation)

### Revenue Calculations

**Energy Revenue:**
- Pumping: Cost = 1,000 MW × DA_LMP (grid cost to pump)
- Generation: Revenue = 1,000 MW × DA_LMP (wholesale price received)

**Storage Efficiency:**
- Pump: 1,000 MWh grid input → +750 MWh stored (75% efficiency, loss on input)
- Generate: -1,000 MWh stored → 1,000 MWh sold (no further adjustment to revenue)

**TMNSR Revenue (ISO-NE Formula):**
```
Revenue = max(TMNSR_Clearing_Price - (RTLMP - Strike_Price), 0) × 1,000 MW

Interpretation:
- Reserve clearing price paid upfront
- Closeout charge: (RTLMP - Strike_Price)
  - If RTLMP > Strike, operator owes closeout charge (reduces net revenue)
  - If RTLMP < Strike, operator gains benefit (increases net revenue)
- Max(·, 0) prevents losses (operator can decline dispatch if unprofitable)
```

## Data

### Source
ISO-NE WebServices API for June 24, 2025, Mass Hub (location ID 4000)

### Pricing Series (24 hours)

| Hour | DA LMP | RT LMP | TMNSR Price | Strike Price | Closeout Charge |
|------|--------|--------|-------------|--------------|-----------------|
| 1    | $48.19 | $60.59 | $11.33      | $62.60       | -$2.01          |
| 2    | $44.94 | $94.02 | $9.25       | $59.55       | $34.47          |
| 3    | $42.66 | $56.57 | $5.22       | $57.05       | -$0.48          |
| 4    | $41.23 | $49.51 | $5.40       | $57.19       | -$7.68          |
| 5    | $43.04 | $61.63 | $5.72       | $57.69       | $3.94           |
| 6    | $50.31 | $74.97 | $6.34       | $58.43       | $16.54          |
| 7    | $55.00 | $44.57 | $10.84      | $59.88       | -$15.31         |
| 8    | $65.57 | $58.20 | $13.77      | $61.32       | -$3.12          |
| 9    | $65.73 | $41.28 | $24.71      | $62.90       | -$21.62 ← High margin |
| 10   | $68.81 | $69.42 | $25.79      | $61.91       | $7.51           |
| 11   | $85.03 | $73.21 | $16.98      | $55.42       | $17.79          |
| 12   | $126.43| $103.42| $33.74      | $57.95       | $45.47          |
| 13   | $174.31| $110.40| $66.70      | $68.45       | $41.95          |
| 14   | $200.18| $128.09| $123.88     | $75.13       | $52.96          |
| 15   | $300.00| $183.69| $147.89     | $82.21       | $101.48         |
| 16   | $343.18| $334.40| $237.16     | $91.37       | $243.03 ← Peak |
| 17   | $418.31| $741.30| $289.58     | $99.80       | $641.50         |
| 18   | $474.90| $1,110.22| $369.64   | $109.45      | $1,000.77       |
| 19   | $407.24| $1,073.63| $429.47   | $114.39      | $959.24         |
| 20   | $315.88| $853.40| $363.18     | $116.39      | $737.01         |
| 21   | $187.58| $261.93| $263.53     | $110.37      | $151.56         |
| 22   | $101.91| $64.91 | $159.98     | $101.76      | -$36.85         |
| 23   | $50.79 | $52.35 | $73.12      | $84.89       | -$32.54         |
| 24   | $50.30 | $57.43 | $34.52      | $74.18       | -$16.75         |

**Key Observations:**
- DA LMP rises from $41-65 (hours 1-8) to $418-474 (hours 15-20)
- TMNSR margin excellent at hour 9 ($46.33), poor at hours 2, 6, 12
- RT prices spike hours 17-20 (system stress), making TMNSR unprofitable there

## Optimal Dispatch

### Schedule

| Period | Hours | Action | Rationale |
|--------|-------|--------|-----------|
| Low Price | 1-8 | PUMP | Build 6,000 MWh storage at costs $41-65/MWh |
| High TMNSR Margin | 9-10 | TMNSR | Earn $46.33, $18.28/MWh with zero storage impact |
| Mid-Range | 11-12 | IDLE | DA prices rising ($85, $126); TMNSR margins poor |
| Moderate TMNSR | 13-14 | TMNSR | Earn $24.75, $70.92/MWh; reserve still valuable |
| Peak Prices | 15-20 | GENERATE | Discharge 6,000 MWh at peak DA prices $300-474/MWh |
| High TMNSR (low RT risk) | 21-24 | TMNSR | Earn $111.97, $196.83, $105.66, $51.27/MWh; RT prices normalized |

### Storage Profile

```
MWh
8000 |
7000 |     ┌─────────────────┐
6000 |     │ 6000 MWh Buffer │
5000 |     │ (Pump complete) │
4000 |   ╱─┴─────────────────┴───────╲
3000 |  ╱                              ╲
2000 | ╱                                ╲
1000 |╱                                  ╲
   0 └────────────────────────────────────└
     0  5  10  15  20  25  Hour

Pump Phase: Hours 1-8 (raise 750 MWh/hr)
Hold Phase: Hours 9-14 (prepare for discharge)
Gen Phase: Hours 15-20 (lower 1000 MWh/hr)
Reserve: Hours 21-24 (empty storage, no constraints)
```

## Results

### Revenue Breakdown

**Energy Arbitrage (Pump-Generate Spread):**

| Component | Amount |
|-----------|--------|
| Pumping Cost (hrs 1-8) | -$390,940 |
| Generation Revenue (hrs 15-20) | +$2,259,510 |
| **Net Energy Arbitrage** | **$1,868,570** |

**TMNSR Reserve Revenue:**

| Hours | Quantity | Avg Net Price | Revenue |
|-------|----------|---------------|---------|
| 9-10 | 2 | $32.31 | $64,610 |
| 13-14 | 2 | $47.83 | $95,670 |
| 21-24 | 4 | $92.41 | $369,640 |
| **TMNSR Total** | **8 hours** | | **$626,010** |

**Daily Total: $2,494,580**

### Hourly Dispatch Details

```
Hour 1-8 (PUMP):
  Action: Pump 1,000 MWh into grid
  Storage: 0 → 6,000 MWh (cumulative)
  Cost: $48.19 to $65.57/MWh
  Total Loss: -$390,940

Hour 9-10 (TMNSR):
  Action: Provide 1,000 MW reserve capacity
  Closeout margins: +$46.33, +$18.28/MWh (favorable)
  Storage: Constant 6,000 MWh
  Revenue: +$64,610

Hour 11-12 (IDLE):
  Action: Hold (prices rising, but no better opportunity)
  Storage: Constant 6,000 MWh
  Revenue: $0

Hour 13-14 (TMNSR):
  Action: Provide 1,000 MW reserve capacity
  Closeout margins: +$24.75, +$70.92/MWh
  Storage: Constant 6,000 MWh
  Revenue: +$95,670

Hour 15-20 (GENERATE):
  Action: Generate 1,000 MW to wholesale market
  Storage: 6,000 → 0 MWh (cumulative discharge)
  Price: $300.00 to $474.90/MWh
  Total Revenue: +$2,259,510

Hour 21-24 (TMNSR):
  Action: Provide 1,000 MW reserve capacity
  Closeout margins: +$111.97, +$196.83, +$105.66, +$51.27/MWh
  Storage: Constant 0 MWh (no depletion risk)
  Revenue: +$369,640
```

## Limitations

### Model Scope (By Design)

- **Perfect Foresight:** Assumes all 24 prices known at decision time. Real bidding requires RT price forecasting and faces forecast error risk.
- **No Call Risk:** Assumes TMNSR reserves are rarely called or not modeled. Real dispatch could deplete inventory unpredictably.
- **No Ramping:** Assumes instant ramp from 0 to 1,000 MW. Real asset has ~5-10 min ramp at 100 MW/min.
- **No Minimum Run:** Ignores technical constraints (minimum run time, startup costs, etc.).
- **No Outages:** Assumes 100% availability. Real units face scheduled and forced outages.

### Market Scope (By Assignment)

- **FERP Not Included:** ISO-NE charges Forecast Error Penalty Reserve. Real optimization must budget for this.
- **Bidding Mechanics Abstracted:** Ignores bid windows, offer management, portfolio constraints.
- **Settlement Simplified:** Uses realized prices. Real settlement involves many adjustment mechanisms.

### Data Limitations

- **Single Day:** Results reflect June 24, 2025 only. Seasonal variation, demand patterns, and extreme events not captured.
- **One Location:** Mass Hub pricing may differ from LMP at actual plant location.
- **Backward-Looking:** RTLMP used to calculate TMNSR net revenue. In real day-ahead bidding, RTLMP is unknown.

## Files

| File | Purpose |
|------|---------|
| `config.py` | Asset parameters (capacity, efficiency, location) |
| `step1_data_collection.py` | Fetch ISO-NE pricing data via WebServices API |
| `step2_optimization.py` | DP solver; computes optimal dispatch |
| `step3_visualize.py` | Generate 4-panel output chart |
| `pricing_data.csv` | Input: 24 rows of hourly market prices |
| `dispatch_results.csv` | Output: optimal hourly actions, revenues, storage state |
| `dispatch_analysis.png` | Output: visualization of prices, storage, revenue, cumulative |

## Validation

✓ Storage conservation: 8 pumps × 750 MWh = 6,000 MWh input; 6 generates × 1,000 MWh = 6,000 MWh output  
✓ Energy revenue: -$390,940 (pump) + $2,259,510 (gen) = $1,868,570  
✓ TMNSR revenue: Sum of 8 reserve hours = $626,010  
✓ Total: $1,868,570 + $626,010 = $2,494,580  
✓ Final storage: 0 MWh (all energy discharged)  
✓ Storage never exceeds 8,000 MWh or goes negative  

## How to Reproduce

```bash
# Install dependencies
pip install pandas requests matplotlib

# Set API credentials
export ISO_NE_USER="moizmahesar@gmail.com"
export ISO_NE_PASS="Editor1!"

# Run pipeline
python3 step1_data_collection.py    # → pricing_data.csv
python3 step2_optimization.py        # → dispatch_results.csv
python3 step3_visualize.py           # → dispatch_analysis.png

# View results
cat dispatch_results.csv
open dispatch_analysis.png
```

## Conclusion

The dynamic programming approach identifies and executes a coherent strategy:
1. **Exploit low prices early** (pump at $41-66/MWh)
2. **Capture reserve value when margins favor reserves** (TMNSR at high clearing prices, low RT risk)
3. **Sell at peak prices late** (generate at $300-474/MWh)
4. **Maintain optionality** (IDLE when no compelling action)

This achieves $2.49M daily revenue—the global optimal under perfect-foresight assumptions. Real-world implementation would require:
- Probabilistic RT price forecasting
- Risk-adjusted reserve call modeling
- Integration with portfolio constraints
- Compliance with actual market rules and settlement mechanics

---

**Generated:** June 24, 2025  
**Asset:** FirstLight Power, 1,000 MW Pumped Hydro  
**Market:** ISO-NE Day-Ahead Energy + TMNSR  
**Method:** Dynamic Programming (Optimal Under Stated Conditions in Assignment)

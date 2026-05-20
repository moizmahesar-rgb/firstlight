# FirstLight Pumped Hydro Dispatch Optimization

**Analysis date:** June 24, 2025  
**Market:** ISO-NE Day-Ahead Energy and Ten-Minute Non-Spinning Reserve  
**Location:** Mass Hub, Location ID `4000`  
**Method:** Dynamic programming optimization in Python

## Executive Summary

This project models the daily dispatch of a 1,000 MW pumped hydro storage asset across two ISO-NE market opportunities:

1. Day-ahead energy arbitrage
2. Ten-Minute Non-Spinning Reserve, or TMNSR

The model chooses one action for each hour of the day:

- Pump
- Generate
- Clear TMNSR
- Remain idle

The objective is to maximize total daily revenue while respecting storage capacity, initial storage, pumping efficiency, and hourly operating constraints.

## Current Results

The optimized dispatch produces the following daily revenue under the assessment assumptions:

| Revenue Source | Amount |
|---|---:|
| Energy Arbitrage | $1,868,570 |
| TMNSR Reserves | $518,250 |
| **Total Revenue** | **$2,386,820** |

The model pumps during lower-priced early hours, preserves storage when reserve value is attractive, generates during the highest day-ahead price hours, and clears TMNSR during hours where reserve value is favorable.

## Assignment Requirements Covered

This repository completes the requested analysis by:

- Pulling hourly Day-Ahead LMPs at Mass Hub
- Pulling hourly Real-Time LMPs at Mass Hub
- Pulling TMNSR prices
- Pulling Day-Ahead Ancillary Services strike prices
- Optimizing a 1,000 MW pumped hydro asset across day-ahead energy and TMNSR
- Producing an hourly dispatch schedule
- Calculating hourly and total revenue
- Saving results in CSV format
- Creating a visualization of dispatch and revenue

## Data

The input data comes from the ISO-NE WebServices API for June 24, 2025.

The model uses the following price series:

| Field | Meaning |
|---|---|
| `da_lmp` | Day-Ahead Locational Marginal Price at Mass Hub |
| `rt_lmp` | Real-Time Locational Marginal Price at Mass Hub |
| `tmnsr_price` | Ten-Minute Non-Spinning Reserve clearing price |
| `strike_price` | Day-Ahead Ancillary Services strike price |

The cleaned pricing data is saved in:

```text
pricing_data.csv
```

## Asset Assumptions

| Parameter | Value |
|---|---:|
| Maximum pumping capacity | 1,000 MW |
| Maximum generation capacity | 1,000 MW |
| Storage capacity | 8,000 MWh |
| Initial storage | 0 MWh |
| Round-trip efficiency | 75% |

In the model, storage is tracked as usable stored energy.

A one-hour pump action consumes 1,000 MWh from the grid and adds 750 MWh to storage:

```text
Storage added from pumping = 1,000 MWh × 75% = 750 MWh
```

A one-hour generation action removes 1,000 MWh from storage and sells 1,000 MWh into the day-ahead energy market.

## Market Logic

### Day-Ahead Energy

For energy, the asset either pumps or generates at the day-ahead LMP.

When pumping:

```text
Energy revenue = -1,000 MW × DA LMP
```

When generating:

```text
Energy revenue = 1,000 MW × DA LMP
```

### TMNSR

TMNSR revenue is modeled using the corrected settlement structure:

```text
Closeout Charge = max(RT LMP - Strike Price, 0)

Net TMNSR Price = TMNSR Price - Closeout Charge

TMNSR Revenue = Cleared MW × Net TMNSR Price
```

The closeout charge cannot be negative. TMNSR revenue itself can be negative if the closeout charge is larger than the TMNSR clearing price.

The model assumes a full 1,000 MW TMNSR position when TMNSR is selected.

The model also follows the assessment assumption that TMNSR participation does not deplete storage inventory.

## Optimization Method

The problem is solved using dynamic programming.

This is appropriate because the value of each hourly decision depends on the storage level carried into later hours. Pumping in one hour can create value several hours later, so the model needs to evaluate the full day rather than choose actions greedily hour by hour.

At each hour and storage state, the model evaluates feasible actions:

```text
IDLE:
    Revenue = 0
    Storage unchanged

TMNSR:
    Revenue = 1,000 MW × Net TMNSR Price
    Storage unchanged

PUMP:
    Revenue = -1,000 MW × DA LMP
    Storage increases by 750 MWh
    Feasible only if storage remains at or below 8,000 MWh

GENERATE:
    Revenue = 1,000 MW × DA LMP
    Storage decreases by 1,000 MWh
    Feasible only if storage is at least 1,000 MWh
```

The model recursively finds the highest-revenue path from hour 1 through hour 24.

## Dispatch Summary

The optimized schedule follows this general pattern:

| Hours | Action | Explanation |
|---:|---|---|
| 1-8 | Pump | Day-ahead prices are relatively low, so the model builds storage |
| 9-10 | TMNSR | Reserve value is attractive and does not reduce storage |
| 11-12 | Idle | The model preserves storage for higher-value future hours |
| 13-14 | TMNSR | Reserve value is attractive relative to other available actions |
| 15-20 | Generate | Day-ahead prices are highest, so stored energy is discharged |
| 21-24 | TMNSR | Reserve value is favorable after the main generation window |

## Revenue Breakdown

### Energy Arbitrage

| Component | Amount |
|---|---:|
| Pumping cost | -$390,940 |
| Generation revenue | $2,259,510 |
| **Net energy arbitrage** | **$1,868,570** |

### TMNSR Revenue

| Period | Hours | Revenue |
|---|---:|---:|
| Early reserve period | 9-10 | $64,610 |
| Midday reserve period | 13-14 | $95,670 |
| Late reserve period | 21-24 | $357,970 |
| **Total TMNSR** | **8 hours** | **$518,250** |

### Total

```text
Total revenue = Energy arbitrage revenue + TMNSR revenue
Total revenue = $1,868,570 + $518,250
Total revenue = $2,386,820
```

## Output Files

| File | Purpose |
|---|---|
| `config.py` | Stores asset assumptions, location ID, date, and configuration values |
| `step1_data_collection.py` | Fetches ISO-NE pricing data |
| `step2_optimization.py` | Runs the dynamic programming dispatch optimization |
| `step3_visualize.py` | Creates the dispatch visualization |
| `pricing_data.csv` | Cleaned hourly price data |
| `dispatch_results.csv` | Hourly dispatch, revenue, and storage results |
| `dispatch_analysis.png` | Visualization of prices, storage, dispatch, and revenue |

## How to Run

Install dependencies:

```bash
pip3 install pandas requests matplotlib
```

Set ISO-NE credentials as environment variables:

```bash
export ISO_NE_USER="your_username_here"
export ISO_NE_PASS="your_password_here"
```

Run the full pipeline:

```bash
python3 step1_data_collection.py
python3 step2_optimization.py
python3 step3_visualize.py
```

View the results:

```bash
cat dispatch_results.csv
open dispatch_analysis.png
```

Do not commit real ISO-NE credentials to GitHub.

## Validation Checks

The model output satisfies the core constraints:

- The asset starts with 0 MWh in storage
- Storage never falls below 0 MWh
- Storage never exceeds 8,000 MWh
- Pumping adds 750 MWh to usable storage
- Generation removes 1,000 MWh from storage
- TMNSR does not change storage
- Hourly revenue is split between energy revenue and TMNSR revenue
- Total revenue equals the sum of hourly revenue
- Final storage returns to 0 MWh in the optimized dispatch

## Limitations

This is a simplified model built for the technical assessment. It is not a full production-grade market bidding model.

Key limitations include:

- The model assumes perfect foresight of all day-ahead and real-time prices
- Real-time prices are not known when day-ahead or reserve positions are submitted
- The model does not optimize real-time energy dispatch
- The model assumes the asset can move immediately between operating modes
- Ramping limits are ignored
- Minimum run times and startup costs are ignored
- Unit availability and outage risk are ignored
- Reserve call risk is not modeled
- TMNSR is assumed not to deplete inventory, following the assessment instruction
- Forecast Energy Reserve Price, or FERP, is ignored as instructed
- Transmission constraints and plant-specific nodal basis are not modeled
- The analysis covers one day only and should not be interpreted as a long-term revenue forecast

## Interview Discussion Points

A few important points to understand and be ready to discuss:

1. Dynamic programming was used because storage creates intertemporal tradeoffs. Pumping now affects what the asset can do later.

2. The model is optimal only under the simplified assumptions. A real implementation would need price forecasting, risk limits, bidding rules, reserve call modeling, and operational constraints.

3. TMNSR can be valuable because it earns reserve revenue without using stored energy in this simplified setup.

4. TMNSR can also be risky because the closeout charge depends on real-time prices. If real-time prices rise far above the strike price, net TMNSR revenue can become negative.

5. The dispatch strategy is intuitive because it buys energy during low-price hours, sells during high-price hours, and uses TMNSR when reserve compensation is favorable.

## Conclusion

The dynamic programming model produces a clear and defensible dispatch strategy for the assessment.

The optimized result is driven by three main decisions:

- Pump during lower-priced hours to build storage
- Generate during the highest day-ahead price hours
- Clear TMNSR when reserve value is favorable and does not interfere with later generation

Under the stated assumptions, the model produces total daily revenue of:

```text
$2,386,820
```

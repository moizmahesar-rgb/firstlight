ISO_NE_BASE_URL = "https://webservices.iso-ne.com/api/v1.1"
MASS_HUB_ID = 4000
ANALYSIS_DATE = "20250624"

ENDPOINTS = {
    "da_lmp": "/hourlylmp/da/final/day/{}/location/{}/",
    "rt_lmp": "/hourlylmp/rt/final/day/{}/location/{}/",
    "tmnsr": "/daasreservedata/day/{}/",
    "da_as_strike": "/daasstrikeprices/day/{}/",
}

ASSET = {
    "capacity_mw": 1000,
    "storage_capacity_mwh": 8000,
    "round_trip_efficiency": 0.75,
    "initial_storage_mwh": 0,
}
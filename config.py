"""
Configuration for FirstLight Pumped Hydro Analysis
June 24, 2025 - Non-secret constants only
"""

ISO_NE_BASE_URL = "https://webservices.iso-ne.com/api/v1.1"
MASS_HUB_ID = 4000
ANALYSIS_DATE = "20250624"

ASSET = {
    "capacity_mw": 1000,
    "storage_capacity_mwh": 8000,
    "round_trip_efficiency": 0.75,
}
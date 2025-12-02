"""Constants for the Dominion Energy integration."""

DOMAIN = "dominion_energy"

# Configuration keys
CONF_ACCOUNT_NUMBER = "account_number"

# API URLs
LOGIN_URL = "https://login.dominionenergy.com/CommonLogin"
API_BASE_URL = "https://prodsvc-dominioncip.smartcmobile.com/Service/api/1"
BILL_FORECAST_ENDPOINT = "/bill/billForecast"
USAGE_HISTORY_ENDPOINT = "/usage/usageHistory"
BILL_HISTORY_ENDPOINT = "/bill/billHistory"

# API Constants
ACTION_CODE = "4"
DEFAULT_HEADERS = {
    "uid": "1",
    "pt": "1",
    "channel": "WEB",
    "Origin": "https://myaccount.dominionenergy.com",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# Update intervals (in seconds)
SCAN_INTERVAL = 43200  # 12 hours - Dominion updates data once daily

# Sensor types
SENSOR_GRID_CONSUMPTION = "grid_consumption"
SENSOR_GRID_RETURN = "grid_return"
SENSOR_CURRENT_BILL = "current_bill"
SENSOR_BILLING_PERIOD_START = "billing_period_start"
SENSOR_BILLING_PERIOD_END = "billing_period_end"
SENSOR_CURRENT_RATE = "current_rate"
SENSOR_DAILY_COST = "daily_cost"
SENSOR_MONTHLY_USAGE = "monthly_usage"

# Attribution
ATTRIBUTION = "Data provided by Dominion Energy"

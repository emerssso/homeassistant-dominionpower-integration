"""API client for Dominion Energy."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import aiohttp

from .const import (
    ACTION_CODE,
    API_BASE_URL,
    BILL_FORECAST_ENDPOINT,
    BILL_HISTORY_ENDPOINT,
    DEFAULT_HEADERS,
    LOGIN_URL,
    USAGE_HISTORY_ENDPOINT,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class DominionEnergyData:
    """Data class for Dominion Energy usage data."""

    # Energy data (kWh)
    grid_consumption: float | None = None
    grid_return: float | None = None
    monthly_usage: float | None = None

    # Billing data
    current_bill: float | None = None
    billing_period_start: datetime | None = None
    billing_period_end: datetime | None = None

    # Rate data
    current_rate: float | None = None
    daily_cost: float | None = None

    # Usage history for statistics
    daily_usage: list[dict[str, Any]] | None = None
    daily_return: list[dict[str, Any]] | None = None


class DominionEnergyApiError(Exception):
    """Exception for Dominion Energy API errors."""


class DominionEnergyAuthError(DominionEnergyApiError):
    """Exception for authentication errors."""


class DominionEnergyApi:
    """API client for Dominion Energy."""

    def __init__(
        self,
        username: str,
        password: str,
        account_number: str,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize the API client."""
        self._username = username
        self._password = password
        self._account_number = account_number
        self._session = session
        self._token: str | None = None
        self._own_session = False

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._own_session = True
        return self._session

    async def close(self) -> None:
        """Close the session if we own it."""
        if self._own_session and self._session:
            await self._session.close()
            self._session = None

    async def authenticate(self) -> bool:
        """Authenticate with Dominion Energy and get bearer token.
        
        This method attempts to authenticate using the OAuth flow.
        Returns True if successful, raises DominionEnergyAuthError on failure.
        """
        session = await self._get_session()

        # Step 1: Get the login page to extract any CSRF tokens or form data
        try:
            # The Dominion Energy login uses OAuth2 - we need to:
            # 1. Navigate to the login URL
            # 2. Submit credentials
            # 3. Extract the bearer token from the redirect or response

            login_params = {"SelectedAppName": "Electric"}
            
            async with session.get(LOGIN_URL, params=login_params) as response:
                if response.status != 200:
                    raise DominionEnergyAuthError(
                        f"Failed to access login page: {response.status}"
                    )
                login_html = await response.text()
                _LOGGER.debug("Got login page")

            # Parse the login form to find the action URL and any hidden fields
            # The actual OAuth implementation depends on the specific flow Dominion uses
            
            # Try to find the OAuth authorize endpoint
            auth_data = {
                "username": self._username,
                "password": self._password,
                "client_id": "CustomerPortal",
                "grant_type": "password",
                "scope": "openid profile email",
            }

            # Try the token endpoint directly
            token_url = "https://login.dominionenergy.com/oauth2/token"
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "User-Agent": DEFAULT_HEADERS["User-Agent"],
            }

            async with session.post(
                token_url, data=auth_data, headers=headers
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self._token = token_data.get("access_token")
                    if self._token:
                        _LOGGER.info("Successfully authenticated with Dominion Energy")
                        return True

            # If direct OAuth didn't work, try form-based login
            # This is a fallback approach
            login_data = {
                "Email": self._username,
                "Password": self._password,
            }

            # Find and submit to the actual login endpoint
            login_submit_url = "https://login.dominionenergy.com/api/v1/authn"
            
            async with session.post(
                login_submit_url,
                json=login_data,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            ) as response:
                if response.status == 200:
                    auth_response = await response.json()
                    session_token = auth_response.get("sessionToken")
                    if session_token:
                        # Exchange session token for bearer token
                        self._token = f"Bearer {session_token}"
                        _LOGGER.info("Successfully authenticated via session token")
                        return True

            raise DominionEnergyAuthError(
                "Failed to authenticate - please check your credentials"
            )

        except aiohttp.ClientError as err:
            raise DominionEnergyAuthError(f"Network error during authentication: {err}")

    def set_token(self, token: str) -> None:
        """Set the bearer token directly (for long-lived tokens)."""
        if not token.startswith("Bearer "):
            token = f"Bearer {token}"
        self._token = token

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        headers = DEFAULT_HEADERS.copy()
        if self._token:
            headers["Authorization"] = self._token
        return headers

    async def _api_request(
        self, endpoint: str, params: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Make an API request."""
        if not self._token:
            raise DominionEnergyApiError("Not authenticated - call authenticate() first")

        session = await self._get_session()
        url = f"{API_BASE_URL}{endpoint}"
        
        default_params = {
            "accountNumber": self._account_number,
            "actionCode": ACTION_CODE,
        }
        if params:
            default_params.update(params)

        try:
            async with session.get(
                url, headers=self._get_headers(), params=default_params
            ) as response:
                if response.status == 401:
                    raise DominionEnergyAuthError("Token expired or invalid")
                if response.status != 200:
                    raise DominionEnergyApiError(
                        f"API request failed with status {response.status}"
                    )
                
                data = await response.json()
                
                # Check for API-level errors
                status = data.get("status", {})
                status_code = status.get("code")
                if status_code and int(status_code) != 200:
                    raise DominionEnergyApiError(
                        f"API error: {status.get('message', 'Unknown error')}"
                    )
                
                return data

        except aiohttp.ClientError as err:
            raise DominionEnergyApiError(f"Network error: {err}")

    async def get_bill_forecast(self) -> dict[str, Any]:
        """Get bill forecast data including current usage."""
        return await self._api_request(BILL_FORECAST_ENDPOINT)

    async def get_usage_history(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> dict[str, Any]:
        """Get usage history data.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        """
        params = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        return await self._api_request(USAGE_HISTORY_ENDPOINT, params)

    async def get_bill_history(self) -> dict[str, Any]:
        """Get billing history data."""
        return await self._api_request(BILL_HISTORY_ENDPOINT)

    async def get_all_data(self) -> DominionEnergyData:
        """Fetch all available data from the API."""
        data = DominionEnergyData()

        try:
            # Get bill forecast (main source of current data)
            bill_forecast = await self.get_bill_forecast()
            forecast_data = bill_forecast.get("data", {})
            
            # Current usage
            data.monthly_usage = forecast_data.get("currentUsageKwh")
            data.grid_consumption = data.monthly_usage  # Alias for energy dashboard
            
            # Current bill amount
            data.current_bill = forecast_data.get("currentBillAmount")
            if data.current_bill is None:
                data.current_bill = forecast_data.get("projectedBillAmount")
            
            # Billing period dates
            billing_start = forecast_data.get("billingPeriodStartDate")
            billing_end = forecast_data.get("billingPeriodEndDate")
            
            if billing_start:
                try:
                    data.billing_period_start = datetime.fromisoformat(
                        billing_start.replace("Z", "+00:00")
                    )
                except ValueError:
                    _LOGGER.warning("Could not parse billing start date: %s", billing_start)
            
            if billing_end:
                try:
                    data.billing_period_end = datetime.fromisoformat(
                        billing_end.replace("Z", "+00:00")
                    )
                except ValueError:
                    _LOGGER.warning("Could not parse billing end date: %s", billing_end)

            # Calculate rate if we have usage and cost
            if data.current_bill and data.monthly_usage and data.monthly_usage > 0:
                data.current_rate = round(data.current_bill / data.monthly_usage, 4)

            # Calculate daily cost estimate
            if data.billing_period_start and data.current_bill:
                days_elapsed = (datetime.now() - data.billing_period_start.replace(tzinfo=None)).days
                if days_elapsed > 0:
                    data.daily_cost = round(data.current_bill / days_elapsed, 2)

            # Grid return (for solar customers) - look for net metering data
            data.grid_return = forecast_data.get("netMeteringExportKwh", 0.0)
            if data.grid_return is None:
                data.grid_return = forecast_data.get("gridReturnKwh", 0.0)

        except DominionEnergyApiError as err:
            _LOGGER.error("Error fetching bill forecast: %s", err)

        try:
            # Get usage history for detailed daily data
            usage_history = await self.get_usage_history()
            history_data = usage_history.get("data", {})
            
            daily_usage = history_data.get("dailyUsage", [])
            if daily_usage:
                data.daily_usage = daily_usage
                
            daily_return = history_data.get("dailyReturn", [])
            if daily_return:
                data.daily_return = daily_return

        except DominionEnergyApiError as err:
            _LOGGER.debug("Error fetching usage history: %s", err)

        try:
            # Get bill history for historical billing data
            bill_history = await self.get_bill_history()
            bills = bill_history.get("data", {}).get("bills", [])
            
            if bills:
                # Use the most recent bill for rate calculation if not already set
                latest_bill = bills[0] if bills else None
                if latest_bill and not data.current_rate:
                    bill_amount = latest_bill.get("totalAmount")
                    bill_usage = latest_bill.get("totalUsageKwh")
                    if bill_amount and bill_usage and bill_usage > 0:
                        data.current_rate = round(bill_amount / bill_usage, 4)

        except DominionEnergyApiError as err:
            _LOGGER.debug("Error fetching bill history: %s", err)

        return data

    async def validate_credentials(self) -> bool:
        """Validate credentials by attempting to fetch data.
        
        Returns True if credentials are valid, False otherwise.
        """
        try:
            await self.authenticate()
            # Try to make a simple API call to verify the token works
            await self.get_bill_forecast()
            return True
        except DominionEnergyAuthError:
            return False
        except DominionEnergyApiError:
            # Auth worked but API call failed - credentials are still valid
            return True

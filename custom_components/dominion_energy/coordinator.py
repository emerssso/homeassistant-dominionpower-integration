"""DataUpdateCoordinator for Dominion Energy."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    DominionEnergyApi,
    DominionEnergyApiError,
    DominionEnergyAuthError,
    DominionEnergyData,
)
from .const import CONF_ACCOUNT_NUMBER, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class DominionEnergyCoordinator(DataUpdateCoordinator[DominionEnergyData]):
    """Class to manage fetching Dominion Energy data."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.config_entry = entry
        self._api: DominionEnergyApi | None = None

    @property
    def api(self) -> DominionEnergyApi:
        """Get the API client, creating it if necessary."""
        if self._api is None:
            session = async_get_clientsession(self.hass)
            self._api = DominionEnergyApi(
                username=self.config_entry.data[CONF_USERNAME],
                password=self.config_entry.data[CONF_PASSWORD],
                account_number=self.config_entry.data[CONF_ACCOUNT_NUMBER],
                session=session,
            )
        return self._api

    async def _async_update_data(self) -> DominionEnergyData:
        """Fetch data from Dominion Energy API."""
        try:
            # Authenticate if we don't have a token
            await self.api.authenticate()
            
            # Fetch all data
            data = await self.api.get_all_data()
            
            _LOGGER.debug(
                "Fetched Dominion Energy data: consumption=%s kWh, return=%s kWh, bill=$%s",
                data.grid_consumption,
                data.grid_return,
                data.current_bill,
            )
            
            return data

        except DominionEnergyAuthError as err:
            # Trigger reauth flow
            raise ConfigEntryAuthFailed(
                f"Authentication failed: {err}"
            ) from err
        except DominionEnergyApiError as err:
            raise UpdateFailed(f"Error communicating with Dominion Energy: {err}") from err

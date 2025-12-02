"""Sensor platform for Dominion Energy integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import DominionEnergyData
from .const import (
    ATTRIBUTION,
    CONF_ACCOUNT_NUMBER,
    DOMAIN,
    SENSOR_BILLING_PERIOD_END,
    SENSOR_BILLING_PERIOD_START,
    SENSOR_CURRENT_BILL,
    SENSOR_CURRENT_RATE,
    SENSOR_DAILY_COST,
    SENSOR_GRID_CONSUMPTION,
    SENSOR_GRID_RETURN,
    SENSOR_MONTHLY_USAGE,
)
from .coordinator import DominionEnergyCoordinator


@dataclass(frozen=True, kw_only=True)
class DominionEnergySensorEntityDescription(SensorEntityDescription):
    """Describe Dominion Energy sensor entity."""

    value_fn: Callable[[DominionEnergyData], Any]


SENSOR_DESCRIPTIONS: tuple[DominionEnergySensorEntityDescription, ...] = (
    DominionEnergySensorEntityDescription(
        key=SENSOR_GRID_CONSUMPTION,
        translation_key="grid_consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
        value_fn=lambda data: data.grid_consumption,
    ),
    DominionEnergySensorEntityDescription(
        key=SENSOR_GRID_RETURN,
        translation_key="grid_return",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
        value_fn=lambda data: data.grid_return,
    ),
    DominionEnergySensorEntityDescription(
        key=SENSOR_MONTHLY_USAGE,
        translation_key="monthly_usage",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=1,
        value_fn=lambda data: data.monthly_usage,
    ),
    DominionEnergySensorEntityDescription(
        key=SENSOR_CURRENT_BILL,
        translation_key="current_bill",
        native_unit_of_measurement="USD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        value_fn=lambda data: data.current_bill,
    ),
    DominionEnergySensorEntityDescription(
        key=SENSOR_DAILY_COST,
        translation_key="daily_cost",
        native_unit_of_measurement="USD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: data.daily_cost,
    ),
    DominionEnergySensorEntityDescription(
        key=SENSOR_CURRENT_RATE,
        translation_key="current_rate",
        native_unit_of_measurement="USD/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        value_fn=lambda data: data.current_rate,
    ),
    DominionEnergySensorEntityDescription(
        key=SENSOR_BILLING_PERIOD_START,
        translation_key="billing_period_start",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda data: data.billing_period_start.date() if data.billing_period_start else None,
    ),
    DominionEnergySensorEntityDescription(
        key=SENSOR_BILLING_PERIOD_END,
        translation_key="billing_period_end",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda data: data.billing_period_end.date() if data.billing_period_end else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dominion Energy sensors based on a config entry."""
    coordinator: DominionEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        DominionEnergySensor(coordinator, description, entry)
        for description in SENSOR_DESCRIPTIONS
    )


class DominionEnergySensor(
    CoordinatorEntity[DominionEnergyCoordinator], SensorEntity
):
    """Representation of a Dominion Energy sensor."""

    entity_description: DominionEnergySensorEntityDescription
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DominionEnergyCoordinator,
        description: DominionEnergySensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.data[CONF_ACCOUNT_NUMBER]}_{description.key}"
        
        account_number = entry.data[CONF_ACCOUNT_NUMBER]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, account_number)},
            name=f"Dominion Energy {account_number}",
            manufacturer="Dominion Energy",
            model="Utility Account",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not super().available:
            return False
        if self.coordinator.data is None:
            return False
        # Check if this specific value is available
        value = self.entity_description.value_fn(self.coordinator.data)
        return value is not None

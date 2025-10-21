"""Capteurs binaires pour l'intégration Big Blue."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure les capteurs binaires Big Blue."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    entities = [
        BigBlueBMSEnableBinarySensor(coordinator, "bms_enable", "BMS Activé"),
        BigBlueGridEnableBinarySensor(coordinator, "grid_enable", "Réseau Activé"),
    ]
    
    async_add_entities(entities)


class BigBlueBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Capteur binaire de base pour Big Blue."""
    
    def __init__(self, coordinator, key: str, name: str):
        """Initialise le capteur binaire."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"Big Blue {name}"
        self._attr_unique_id = f"bigblue_{key}"
    
    @property
    def is_on(self) -> bool:
        """Retourne l'état du capteur binaire."""
        if self.coordinator.data and self._key in self.coordinator.data:
            return self.coordinator.data[self._key]
        return False


class BigBlueBMSEnableBinarySensor(BigBlueBinarySensor):
    """Capteur binaire BMS activé."""
    
    def __init__(self, coordinator, key: str, name: str):
        super().__init__(coordinator, key, name)
        self._attr_icon = "mdi:battery"
        self._attr_device_class = "switch"


class BigBlueGridEnableBinarySensor(BigBlueBinarySensor):
    """Capteur binaire réseau activé."""
    
    def __init__(self, coordinator, key: str, name: str):
        super().__init__(coordinator, key, name)
        self._attr_icon = "mdi:transmission-tower"
        self._attr_device_class = "switch"

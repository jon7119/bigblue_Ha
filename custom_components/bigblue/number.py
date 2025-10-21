"""Entités numériques pour l'intégration Big Blue."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import translation

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Configure les entités numériques Big Blue."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    entities = []
    
    if coordinator.data:
        for device_mac, device_info in coordinator.data.items():
            if device_mac == "default" or device_info.get("offline", False):
                continue
            
            device_name = device_info.get("device_name", f"Big Blue {device_mac}")
            
            # Seuil de décharge
            entities.append(
                BigBlueDischargeThresholdNumber(coordinator, device_mac, f"Seuil Décharge {device_name}")
            )
    
    _LOGGER.info(f"Création de {len(entities)} entités numériques")
    async_add_entities(entities)


class BigBlueDischargeThresholdNumber(CoordinatorEntity, NumberEntity):
    """Entité numérique du seuil de décharge."""
    
    def __init__(self, coordinator, device_mac: str, name: str):
        super().__init__(coordinator)
        self._device_mac = device_mac
        self._attr_name = name
        self._attr_unique_id = f"bigblue_{device_mac}_discharge_threshold"
        self._attr_icon = "mdi:battery-alert"
        self._attr_native_min_value = 5
        self._attr_native_max_value = 50
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = "%"
        self._attr_device_class = "battery"
        self._translation_key = "discharge_threshold"
    
    @property
    def native_value(self) -> float:
        """Retourne le seuil de décharge actuel."""
        if self.coordinator.data and self._device_mac:
            device_data = self.coordinator.data.get(self._device_mac, {})
            if device_data and "discharge_threshold" in device_data:
                return device_data["discharge_threshold"]
        return 10.0  # Valeur par défaut
    
    @property
    def device_info(self):
        """Retourne les informations de l'appareil."""
        return {
            "identifiers": {(DOMAIN, self._device_mac)},
            "name": self.coordinator.data.get(self._device_mac, {}).get("device_name", f"Big Blue {self._device_mac}"),
            "manufacturer": "Big Blue",
            "model": "Battery System",
            "sw_version": "1.0.0"
        }
    
    async def async_set_native_value(self, value: float) -> None:
        """Définit le seuil de décharge."""
        try:
            _LOGGER.info(f"🔧 Modification du seuil de décharge à {value}% pour {self._device_mac}")
            
            # Appeler l'API pour mettre à jour le seuil
            success = await self.coordinator.api_client.set_discharge_threshold(self._device_mac, int(value))
            
            if success:
                _LOGGER.info(f"✅ Seuil de décharge mis à jour à {value}%")
                # Forcer la mise à jour des données
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"❌ Échec mise à jour seuil de décharge à {value}%")
                
        except Exception as err:
            _LOGGER.error(f"❌ Erreur modification seuil de décharge: {err}")

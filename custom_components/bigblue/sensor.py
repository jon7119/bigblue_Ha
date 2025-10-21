"""Capteurs pour l'intégration Big Blue."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import translation

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure les capteurs Big Blue."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    entities = []
    
    # Créer des capteurs pour chaque batterie
    devices_data = coordinator.data
    if not devices_data:
        # Si pas de données, ne pas créer de capteurs par défaut
        _LOGGER.warning("⚠️ Aucune donnée du coordinateur - Aucun capteur créé")
        return entities
    else:
        for device_mac, device_info in devices_data.items():
            device_name = device_info.get("device_name", f"Big Blue {device_mac}")
            
            # Capteurs pour cette batterie
            device_entities = [
                # Batterie - Noms comme Storcube
                BigBlueSOCSensor(coordinator, "soc", f"État de charge {device_name}", "%", "battery", device_mac),
                BigBlueSOHSensor(coordinator, "soh", f"État de santé {device_name}", "%", "battery", device_mac),
                BigBlueBatteryVoltageSensor(coordinator, "voltage", f"Tension {device_name}", "V", "voltage", device_mac),
                BigBlueBatteryCurrentSensor(coordinator, "current", f"Courant {device_name}", "A", "current", device_mac),
                BigBlueBatteryPowerSensor(coordinator, "power", f"Puissance {device_name}", "W", "power", device_mac),
                BigBlueRemainingCapacitySensor(coordinator, "remaining_capacity", f"Capacité Restante {device_name}", "kWh", "energy", device_mac),
                BigBlueRatedCapacitySensor(coordinator, "rated_capacity", f"Capacité Nominale {device_name}", "kWh", "energy", device_mac),
                
                # Panneaux solaires - Noms comme Storcube
                BigBluePV1VoltageSensor(coordinator, "pv1_voltage", f"Tension PV1 {device_name}", "V", "voltage", device_mac),
                BigBluePV1CurrentSensor(coordinator, "pv1_current", f"Courant PV1 {device_name}", "A", "current", device_mac),
                BigBluePV1PowerSensor(coordinator, "pv1_power", f"Puissance PV1 {device_name}", "W", "power", device_mac),
                BigBluePV2VoltageSensor(coordinator, "pv2_voltage", f"Tension PV2 {device_name}", "V", "voltage", device_mac),
                BigBluePV2CurrentSensor(coordinator, "pv2_current", f"Courant PV2 {device_name}", "A", "current", device_mac),
                BigBluePV2PowerSensor(coordinator, "pv2_power", f"Puissance PV2 {device_name}", "W", "power", device_mac),
                BigBluePVTotalPowerSensor(coordinator, "pv_total_power", f"Puissance PV Totale {device_name}", "W", "power", device_mac),
                
                # Production d'énergie - Noms comme Storcube
                BigBlueDailyGenerationSensor(coordinator, "daily_generation", f"Énergie Solaire {device_name}", "kWh", "energy", device_mac),
                BigBlueTotalGenerationSensor(coordinator, "total_generation", f"Énergie Solaire Totale {device_name}", "kWh", "energy", device_mac),
                BigBlueDailyOutputEnergySensor(coordinator, "daily_output_energy", f"Énergie Sortie {device_name}", "kWh", "energy", device_mac),
                BigBlueTotalOutputEnergySensor(coordinator, "total_output_energy", f"Énergie Sortie Totale {device_name}", "kWh", "energy", device_mac),
                
                # Température
                BigBlueMaxTemperatureSensor(coordinator, "max_temperature", f"Température Max {device_name}", "°C", "temperature", device_mac),
                BigBlueMinTemperatureSensor(coordinator, "min_temperature", f"Température Min {device_name}", "°C", "temperature", device_mac),
                
                # CO2 et économies
                BigBlueDailyCO2SavingsSensor(coordinator, "daily_co2_savings", f"Économies CO2 {device_name}", "g", "weight", device_mac),
                
                # Temps de fonctionnement
                BigBlueDailyRuntimeSensor(coordinator, "daily_runtime", f"Temps Fonctionnement {device_name}", "h", "duration", device_mac),
                BigBlueTotalRuntimeSensor(coordinator, "total_runtime", f"Temps Total {device_name}", "h", "duration", device_mac),
                
                # Mode actuel
                BigBlueCurrentModeSensor(coordinator, "current_mode", f"Mode Actuel {device_name}", None, None, device_mac),
                
            ]
            
            entities.extend(device_entities)
    
    _LOGGER.info(f"Création de {len(entities)} capteurs")
    async_add_entities(entities)


class BigBlueSensor(CoordinatorEntity, SensorEntity):
    """Capteur de base pour Big Blue."""
    
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str = None, device_mac: str = None):
        """Initialise le capteur."""
        super().__init__(coordinator)
        self._key = key
        self._device_mac = device_mac
        self._attr_name = name  # Nom complet déjà fourni
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_unique_id = f"bigblue_{device_mac}_{key}" if device_mac else f"bigblue_{key}"
        self._translation_key = key
    
    @property
    def device_info(self):
        """Retourne les informations de l'appareil."""
        if self._device_mac:
            return {
                "identifiers": {(DOMAIN, self._device_mac)},
                "name": self.coordinator.data.get(self._device_mac, {}).get("device_name", f"Big Blue {self._device_mac}"),
                "manufacturer": "Big Blue",
                "model": "Battery System",
                "sw_version": "1.0.0"
            }
        return None
    
    @property
    def native_value(self) -> Any:
        """Retourne la valeur du capteur."""
        if self.coordinator.data and self._device_mac:
            device_data = self.coordinator.data.get(self._device_mac, {})
            if device_data and self._key in device_data:
                value = device_data[self._key]
                # Vérifier si le device est hors ligne
                if device_data.get("offline", False):
                    return None  # Retourner None pour les devices hors ligne
                return value
        return None


# Capteurs de batterie
class BigBlueSOCSensor(BigBlueSensor):
    """Capteur d'état de charge total."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:battery"


class BigBlueSOHSensor(BigBlueSensor):
    """Capteur d'état de santé."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:heart-pulse"


class BigBlueBatteryVoltageSensor(BigBlueSensor):
    """Capteur de tension batterie."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:lightning-bolt"


class BigBlueBatteryCurrentSensor(BigBlueSensor):
    """Capteur de courant batterie."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:current-ac"


class BigBlueBatteryPowerSensor(BigBlueSensor):
    """Capteur de puissance batterie."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:power"


class BigBlueRemainingCapacitySensor(BigBlueSensor):
    """Capteur de capacité restante."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:battery-50"


class BigBlueRatedCapacitySensor(BigBlueSensor):
    """Capteur de capacité nominale."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:battery"


# Capteurs panneaux solaires
class BigBluePV1VoltageSensor(BigBlueSensor):
    """Capteur de tension PV1."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:solar-power"  # Icône soleil comme Storcube


class BigBluePV1CurrentSensor(BigBlueSensor):
    """Capteur de courant PV1."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:solar-power"  # Icône soleil comme Storcube


class BigBluePV1PowerSensor(BigBlueSensor):
    """Capteur de puissance PV1."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:solar-power"  # Icône soleil comme Storcube


class BigBluePV2VoltageSensor(BigBlueSensor):
    """Capteur de tension PV2."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:solar-power"  # Icône soleil comme Storcube


class BigBluePV2CurrentSensor(BigBlueSensor):
    """Capteur de courant PV2."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:solar-power"  # Icône soleil comme Storcube


class BigBluePV2PowerSensor(BigBlueSensor):
    """Capteur de puissance PV2."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:solar-power"


class BigBluePVTotalPowerSensor(BigBlueSensor):
    """Capteur de puissance PV totale."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:solar-power-variant"


# Capteurs de production
class BigBlueDailyGenerationSensor(BigBlueSensor):
    """Capteur de production journalière."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:solar-power"  # Icône soleil comme Storcube


class BigBlueTotalGenerationSensor(BigBlueSensor):
    """Capteur de production totale."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:solar-power"  # Icône soleil comme Storcube


class BigBlueDailyOutputEnergySensor(BigBlueSensor):
    """Capteur d'énergie sortie journalière."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:lightning-bolt"  # Icône éclair comme Storcube


class BigBlueTotalOutputEnergySensor(BigBlueSensor):
    """Capteur d'énergie sortie totale."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:lightning-bolt"  # Icône éclair comme Storcube


# Capteurs de température
class BigBlueMaxTemperatureSensor(BigBlueSensor):
    """Capteur de température maximale."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:thermometer-high"


class BigBlueMinTemperatureSensor(BigBlueSensor):
    """Capteur de température minimale."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:thermometer-low"


# Capteurs CO2 et économies
class BigBlueDailyCO2SavingsSensor(BigBlueSensor):
    """Capteur d'économies CO2 journalières."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:leaf"


# Capteurs de temps de fonctionnement
class BigBlueDailyRuntimeSensor(BigBlueSensor):
    """Capteur de temps de fonctionnement journalier."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:clock-outline"


class BigBlueTotalRuntimeSensor(BigBlueSensor):
    """Capteur de temps de fonctionnement total."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:clock"


class BigBlueCurrentModeSensor(BigBlueSensor):
    """Capteur du mode actuel."""
    def __init__(self, coordinator, key: str, name: str, unit: str, device_class: str, device_mac: str = None):
        super().__init__(coordinator, key, name, unit, device_class, device_mac)
        self._attr_icon = "mdi:cog"
    
    @property
    def native_value(self) -> str:
        """Retourne le mode actuel sous forme de texte."""
        if self.coordinator.data and self._device_mac:
            device_data = self.coordinator.data.get(self._device_mac, {})
            if device_data and self._key in device_data:
                mode = device_data[self._key]
                return self._get_mode_name(mode)
        return "Inconnu"
    
    def _get_mode_name(self, mode: int) -> str:
        """Convertit le numéro de mode en nom."""
        mode_names = {
            1: "Mode 1 - Priorité batterie",
            2: "Mode 2 - Priorité micro-onduleur", 
            3: "Mode 3 - Mode personnalisé"
        }
        return mode_names.get(mode, f"Mode {mode}")


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
            
            # Seuil de charge
            entities.append(
                BigBlueChargeThresholdNumber(coordinator, device_mac, f"Seuil Charge {device_name}")
            )
            
            # Puissance de sortie (bmsPower)
            entities.append(
                BigBlueOutputPowerNumber(coordinator, device_mac, f"Puissance Sortie {device_name}")
            )
            
            # Facteur de puissance (pfValue)
            entities.append(
                BigBluePowerFactorNumber(coordinator, device_mac, f"Facteur Puissance {device_name}")
            )
            
            # Puissances CT
            entities.append(
                BigBlueCTAPowerNumber(coordinator, device_mac, f"Puissance CT A {device_name}")
            )
            entities.append(
                BigBlueCTBPowerNumber(coordinator, device_mac, f"Puissance CT B {device_name}")
            )
            entities.append(
                BigBlueCTCPowerNumber(coordinator, device_mac, f"Puissance CT C {device_name}")
            )
            entities.append(
                BigBlueCTTotalPowerNumber(coordinator, device_mac, f"Puissance CT Totale {device_name}")
            )
            
            # Temps réseau (gridTime)
            entities.append(
                BigBlueGridTimeNumber(coordinator, device_mac, f"Temps Réseau {device_name}")
            )
            
            # Prix par kWh
            entities.append(
                BigBluePricePerKwhNumber(coordinator, device_mac, f"Prix kWh {device_name}")
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


class BigBlueChargeThresholdNumber(CoordinatorEntity, NumberEntity):
    """Entité numérique du seuil de charge."""
    
    def __init__(self, coordinator, device_mac: str, name: str):
        super().__init__(coordinator)
        self._device_mac = device_mac
        self._attr_name = name
        self._attr_unique_id = f"bigblue_{device_mac}_charge_threshold"
        self._attr_icon = "mdi:battery-charging"
        self._attr_native_min_value = 50
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = "%"
        self._attr_device_class = "battery"
        self._translation_key = "charge_threshold"
    
    @property
    def native_value(self) -> float:
        """Retourne le seuil de charge actuel."""
        if self.coordinator.data and self._device_mac:
            device_data = self.coordinator.data.get(self._device_mac, {})
            if device_data and "charge_threshold" in device_data:
                return device_data["charge_threshold"]
        return 90.0  # Valeur par défaut
    
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
        """Définit le seuil de charge."""
        try:
            _LOGGER.info(f"🔧 Modification du seuil de charge à {value}% pour {self._device_mac}")
            
            # Appeler l'API pour mettre à jour le seuil
            success = await self.coordinator.api_client.set_charge_threshold(self._device_mac, int(value))
            
            if success:
                _LOGGER.info(f"✅ Seuil de charge mis à jour à {value}%")
                # Forcer la mise à jour des données
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"❌ Échec mise à jour seuil de charge à {value}%")
                
        except Exception as err:
            _LOGGER.error(f"❌ Erreur modification seuil de charge: {err}")


class BigBlueOutputPowerNumber(CoordinatorEntity, NumberEntity):
    """Entité numérique de la puissance de sortie (bmsPower).
    
    Cette entité permet de contrôler la puissance de sortie de la batterie en pourcentage.
    La plage va de 5% à 100% selon les spécifications de l'appareil.
    """
    
    def __init__(self, coordinator, device_mac: str, name: str):
        super().__init__(coordinator)
        self._device_mac = device_mac
        self._attr_name = name
        self._attr_unique_id = f"bigblue_{device_mac}_output_power"
        self._attr_icon = "mdi:flash"
        self._attr_native_min_value = 5
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = "%"
        self._attr_device_class = None
        self._translation_key = "output_power"
    
    @property
    def native_value(self) -> float:
        """Retourne la puissance de sortie actuelle en pourcentage."""
        if self.coordinator.data and self._device_mac:
            device_data = self.coordinator.data.get(self._device_mac, {})
            # Priorité 1: valeur depuis output_power
            if device_data and "output_power" in device_data:
                value = device_data["output_power"]
                if value is not None:
                    return float(value)
            # Priorité 2: valeur depuis les settings
            settings = device_data.get("settings", {})
            if settings and "bmsPower" in settings:
                value = settings.get("bmsPower")
                if value is not None:
                    return float(value)
        return 20.0  # Valeur par défaut
    
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
        """Définit la puissance de sortie en pourcentage.
        
        Args:
            value: Puissance de sortie en pourcentage (5-100%)
        """
        try:
            # Valider la valeur
            if value < 5 or value > 100:
                _LOGGER.error(f"❌ Valeur invalide: {value}% (doit être entre 5% et 100%)")
                return
            
            # Arrondir à l'entier le plus proche
            power_value = int(round(value))
            
            _LOGGER.info(f"🔧 Modification de la puissance de sortie à {power_value}% pour {self._device_mac}")
            
            # Appeler l'API pour mettre à jour le paramètre
            success = await self.coordinator.api_client.set_device_config_parameter(
                self._device_mac, "bmsPower", power_value
            )
            
            if success:
                _LOGGER.info(f"✅ Puissance de sortie mise à jour à {power_value}% pour {self._device_mac}")
                # Forcer la mise à jour des données
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"❌ Échec mise à jour puissance de sortie à {power_value}% pour {self._device_mac}")
                
        except Exception as err:
            _LOGGER.error(f"❌ Erreur modification puissance de sortie pour {self._device_mac}: {err}")


class BigBluePowerFactorNumber(CoordinatorEntity, NumberEntity):
    """Entité numérique du facteur de puissance (pfValue)."""
    
    def __init__(self, coordinator, device_mac: str, name: str):
        super().__init__(coordinator)
        self._device_mac = device_mac
        self._attr_name = name
        self._attr_unique_id = f"bigblue_{device_mac}_power_factor"
        self._attr_icon = "mdi:sine-wave"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = "%"
        self._attr_device_class = None
        self._translation_key = "power_factor"
    
    @property
    def native_value(self) -> float:
        """Retourne le facteur de puissance actuel."""
        settings = self.coordinator.data.get(self._device_mac, {}).get("settings", {})
        if settings and "pfValue" in settings:
            return float(settings.get("pfValue", 0))
        return 0.0  # Valeur par défaut
    
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
        """Définit le facteur de puissance."""
        try:
            _LOGGER.info(f"🔧 Modification du facteur de puissance à {value}% pour {self._device_mac}")
            
            success = await self.coordinator.api_client.set_device_config_parameter(
                self._device_mac, "pfValue", int(value)
            )
            
            if success:
                _LOGGER.info(f"✅ Facteur de puissance mis à jour à {value}%")
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"❌ Échec mise à jour facteur de puissance à {value}%")
                
        except Exception as err:
            _LOGGER.error(f"❌ Erreur modification facteur de puissance: {err}")


class BigBlueCTAPowerNumber(CoordinatorEntity, NumberEntity):
    """Entité numérique de la puissance CT A (ctAPower)."""
    
    def __init__(self, coordinator, device_mac: str, name: str):
        super().__init__(coordinator)
        self._device_mac = device_mac
        self._attr_name = name
        self._attr_unique_id = f"bigblue_{device_mac}_cta_power"
        self._attr_icon = "mdi:current-ac"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 10000
        self._attr_native_step = 100
        self._attr_native_unit_of_measurement = "W"
        self._attr_device_class = "power"
        self._translation_key = "cta_power"
    
    @property
    def native_value(self) -> float:
        """Retourne la puissance CT A actuelle."""
        settings = self.coordinator.data.get(self._device_mac, {}).get("settings", {})
        if settings and "ctAPower" in settings:
            return float(settings.get("ctAPower", 0))
        return 0.0
    
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
        """Définit la puissance CT A."""
        try:
            _LOGGER.info(f"🔧 Modification de la puissance CT A à {value}W pour {self._device_mac}")
            
            success = await self.coordinator.api_client.set_device_config_parameter(
                self._device_mac, "ctAPower", int(value)
            )
            
            if success:
                _LOGGER.info(f"✅ Puissance CT A mise à jour à {value}W")
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"❌ Échec mise à jour puissance CT A à {value}W")
                
        except Exception as err:
            _LOGGER.error(f"❌ Erreur modification puissance CT A: {err}")


class BigBlueCTBPowerNumber(CoordinatorEntity, NumberEntity):
    """Entité numérique de la puissance CT B (ctBPower)."""
    
    def __init__(self, coordinator, device_mac: str, name: str):
        super().__init__(coordinator)
        self._device_mac = device_mac
        self._attr_name = name
        self._attr_unique_id = f"bigblue_{device_mac}_ctb_power"
        self._attr_icon = "mdi:current-ac"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 10000
        self._attr_native_step = 100
        self._attr_native_unit_of_measurement = "W"
        self._attr_device_class = "power"
        self._translation_key = "ctb_power"
    
    @property
    def native_value(self) -> float:
        """Retourne la puissance CT B actuelle."""
        settings = self.coordinator.data.get(self._device_mac, {}).get("settings", {})
        if settings and "ctBPower" in settings:
            return float(settings.get("ctBPower", 0))
        return 0.0
    
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
        """Définit la puissance CT B."""
        try:
            _LOGGER.info(f"🔧 Modification de la puissance CT B à {value}W pour {self._device_mac}")
            
            success = await self.coordinator.api_client.set_device_config_parameter(
                self._device_mac, "ctBPower", int(value)
            )
            
            if success:
                _LOGGER.info(f"✅ Puissance CT B mise à jour à {value}W")
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"❌ Échec mise à jour puissance CT B à {value}W")
                
        except Exception as err:
            _LOGGER.error(f"❌ Erreur modification puissance CT B: {err}")


class BigBlueCTCPowerNumber(CoordinatorEntity, NumberEntity):
    """Entité numérique de la puissance CT C (ctCPower)."""
    
    def __init__(self, coordinator, device_mac: str, name: str):
        super().__init__(coordinator)
        self._device_mac = device_mac
        self._attr_name = name
        self._attr_unique_id = f"bigblue_{device_mac}_ctc_power"
        self._attr_icon = "mdi:current-ac"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 10000
        self._attr_native_step = 100
        self._attr_native_unit_of_measurement = "W"
        self._attr_device_class = "power"
        self._translation_key = "ctc_power"
    
    @property
    def native_value(self) -> float:
        """Retourne la puissance CT C actuelle."""
        settings = self.coordinator.data.get(self._device_mac, {}).get("settings", {})
        if settings and "ctCPower" in settings:
            return float(settings.get("ctCPower", 0))
        return 0.0
    
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
        """Définit la puissance CT C."""
        try:
            _LOGGER.info(f"🔧 Modification de la puissance CT C à {value}W pour {self._device_mac}")
            
            success = await self.coordinator.api_client.set_device_config_parameter(
                self._device_mac, "ctCPower", int(value)
            )
            
            if success:
                _LOGGER.info(f"✅ Puissance CT C mise à jour à {value}W")
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"❌ Échec mise à jour puissance CT C à {value}W")
                
        except Exception as err:
            _LOGGER.error(f"❌ Erreur modification puissance CT C: {err}")


class BigBlueCTTotalPowerNumber(CoordinatorEntity, NumberEntity):
    """Entité numérique de la puissance CT totale (ctTotalPower)."""
    
    def __init__(self, coordinator, device_mac: str, name: str):
        super().__init__(coordinator)
        self._device_mac = device_mac
        self._attr_name = name
        self._attr_unique_id = f"bigblue_{device_mac}_ct_total_power"
        self._attr_icon = "mdi:current-ac"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 30000
        self._attr_native_step = 100
        self._attr_native_unit_of_measurement = "W"
        self._attr_device_class = "power"
        self._translation_key = "ct_total_power"
    
    @property
    def native_value(self) -> float:
        """Retourne la puissance CT totale actuelle."""
        settings = self.coordinator.data.get(self._device_mac, {}).get("settings", {})
        if settings and "ctTotalPower" in settings:
            return float(settings.get("ctTotalPower", 0))
        return 0.0
    
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
        """Définit la puissance CT totale."""
        try:
            _LOGGER.info(f"🔧 Modification de la puissance CT totale à {value}W pour {self._device_mac}")
            
            success = await self.coordinator.api_client.set_device_config_parameter(
                self._device_mac, "ctTotalPower", int(value)
            )
            
            if success:
                _LOGGER.info(f"✅ Puissance CT totale mise à jour à {value}W")
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"❌ Échec mise à jour puissance CT totale à {value}W")
                
        except Exception as err:
            _LOGGER.error(f"❌ Erreur modification puissance CT totale: {err}")


class BigBlueGridTimeNumber(CoordinatorEntity, NumberEntity):
    """Entité numérique du temps réseau (gridTime)."""
    
    def __init__(self, coordinator, device_mac: str, name: str):
        super().__init__(coordinator)
        self._device_mac = device_mac
        self._attr_name = name
        self._attr_unique_id = f"bigblue_{device_mac}_grid_time"
        self._attr_icon = "mdi:timer"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 3600
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = "s"
        self._attr_device_class = None
        self._translation_key = "grid_time"
    
    @property
    def native_value(self) -> float:
        """Retourne le temps réseau actuel."""
        settings = self.coordinator.data.get(self._device_mac, {}).get("settings", {})
        if settings and "gridTime" in settings:
            return float(settings.get("gridTime", 0))
        return 0.0
    
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
        """Définit le temps réseau."""
        try:
            _LOGGER.info(f"🔧 Modification du temps réseau à {value}s pour {self._device_mac}")
            
            success = await self.coordinator.api_client.set_device_config_parameter(
                self._device_mac, "gridTime", int(value)
            )
            
            if success:
                _LOGGER.info(f"✅ Temps réseau mis à jour à {value}s")
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"❌ Échec mise à jour temps réseau à {value}s")
                
        except Exception as err:
            _LOGGER.error(f"❌ Erreur modification temps réseau: {err}")


class BigBluePricePerKwhNumber(CoordinatorEntity, NumberEntity):
    """Entité numérique du prix par kWh (pricePerKwh)."""
    
    def __init__(self, coordinator, device_mac: str, name: str):
        super().__init__(coordinator)
        self._device_mac = device_mac
        self._attr_name = name
        self._attr_unique_id = f"bigblue_{device_mac}_price_per_kwh"
        self._attr_icon = "mdi:currency-eur"
        self._attr_native_min_value = 0.0
        self._attr_native_max_value = 10.0
        self._attr_native_step = 0.01
        self._attr_native_unit_of_measurement = "€/kWh"
        self._attr_device_class = None
        self._translation_key = "price_per_kwh"
    
    @property
    def native_value(self) -> float:
        """Retourne le prix par kWh actuel."""
        settings = self.coordinator.data.get(self._device_mac, {}).get("settings", {})
        if settings and "pricePerKwh" in settings:
            return float(settings.get("pricePerKwh", 0.3))
        return 0.3  # Valeur par défaut
    
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
        """Définit le prix par kWh."""
        try:
            _LOGGER.info(f"🔧 Modification du prix par kWh à {value}€/kWh pour {self._device_mac}")
            
            success = await self.coordinator.api_client.set_device_config_parameter(
                self._device_mac, "pricePerKwh", float(value)
            )
            
            if success:
                _LOGGER.info(f"✅ Prix par kWh mis à jour à {value}€/kWh")
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"❌ Échec mise à jour prix par kWh à {value}€/kWh")
                
        except Exception as err:
            _LOGGER.error(f"❌ Erreur modification prix par kWh: {err}")

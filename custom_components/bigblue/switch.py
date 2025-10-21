"""Support for Big Blue switches."""
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up Big Blue switches from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    entities = []
    
    # Créer des switches pour chaque batterie
    devices_data = coordinator.data
    if not devices_data:
        _LOGGER.warning("⚠️ Aucune donnée du coordinateur - Aucun switch créé")
        return
    
    for device_mac, device_info in devices_data.items():
        device_name = device_info.get("device_name", f"Big Blue {device_mac}")
        
        # Switches pour cette batterie
        device_switches = [
            BigBlueMode1Switch(coordinator, device_mac, f"Mode 1 {device_name}"),
            BigBlueMode2Switch(coordinator, device_mac, f"Mode 2 {device_name}"),
            BigBlueMode3Switch(coordinator, device_mac, f"Mode 3 {device_name}"),
        ]
        
        entities.extend(device_switches)
        _LOGGER.info(f"🔧 {len(device_switches)} switches créés pour {device_name}")
    
    async_add_entities(entities)


class BigBlueSwitch(CoordinatorEntity, SwitchEntity):
    """Switch de base pour Big Blue."""
    
    def __init__(self, coordinator, device_mac: str, name: str):
        """Initialise le switch."""
        super().__init__(coordinator)
        self._device_mac = device_mac
        self._attr_name = name
        self._attr_unique_id = f"bigblue_{device_mac}_{self.__class__.__name__.lower()}"
        self._attr_is_on = False
        self._translation_key = self.__class__.__name__.lower().replace("bigblue", "").replace("switch", "")
    
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
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Active le mode."""
        try:
            # Vérifier si le mode est déjà actif
            current_mode = await self.coordinator.api_client.get_current_mode(self._device_mac)
            if current_mode == self.mode_value:
                _LOGGER.info(f"ℹ️ Mode {self.mode_value} déjà actif pour {self._device_mac}")
                return
            
            success = await self.coordinator.api_client.set_device_mode(self._device_mac, self.mode_value)
            if success:
                _LOGGER.info(f"✅ Mode {self.mode_value} activé pour {self._device_mac}")
                
                # Forcer la mise à jour des données du coordinateur
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"❌ Échec activation mode {self.mode_value} pour {self._device_mac}")
        except Exception as err:
            _LOGGER.error(f"❌ Erreur activation mode {self.mode_value}: {err}")
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Désactive le mode."""
        # Les modes ne peuvent pas être "désactivés", on peut seulement changer de mode
        _LOGGER.info(f"ℹ️ Mode {self.mode_value} ne peut pas être désactivé, utilisez un autre mode")
    
    async def _deactivate_other_modes(self):
        """Désactive les autres modes du même device."""
        # Cette méthode sera appelée pour désactiver les autres switches
        pass


class BigBlueMode1Switch(BigBlueSwitch):
    """Switch pour le mode 1 (Priorité batterie)."""
    
    def __init__(self, coordinator, device_mac: str, name: str):
        super().__init__(coordinator, device_mac, name)
        self.mode_value = 1
        self._attr_icon = "mdi:battery"
    
    @property
    def is_on(self) -> bool:
        """Retourne l'état du switch."""
        if self.coordinator.data and self._device_mac:
            device_data = self.coordinator.data.get(self._device_mac, {})
            if device_data and "current_mode" in device_data:
                current_mode = device_data.get("current_mode", 1)
                return current_mode == 1
        return False


class BigBlueMode2Switch(BigBlueSwitch):
    """Switch pour le mode 2 (Priorité micro-onduleur)."""
    
    def __init__(self, coordinator, device_mac: str, name: str):
        super().__init__(coordinator, device_mac, name)
        self.mode_value = 2
        self._attr_icon = "mdi:solar-power"
    
    @property
    def is_on(self) -> bool:
        """Retourne l'état du switch."""
        if self.coordinator.data and self._device_mac:
            device_data = self.coordinator.data.get(self._device_mac, {})
            if device_data and "current_mode" in device_data:
                current_mode = device_data.get("current_mode", 1)
                return current_mode == 2
        return False


class BigBlueMode3Switch(BigBlueSwitch):
    """Switch pour le mode 3 (Mode personnalisé)."""
    
    def __init__(self, coordinator, device_mac: str, name: str):
        super().__init__(coordinator, device_mac, name)
        self.mode_value = 3
        self._attr_icon = "mdi:cog"
    
    @property
    def is_on(self) -> bool:
        """Retourne l'état du switch."""
        if self.coordinator.data and self._device_mac:
            device_data = self.coordinator.data.get(self._device_mac, {})
            if device_data and "current_mode" in device_data:
                current_mode = device_data.get("current_mode", 1)
                return current_mode == 3
        return False

"""Big Blue Battery Integration for Home Assistant."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import BigBlueDataUpdateCoordinator, BigBlueAPIClient

_LOGGER = logging.getLogger(__name__)

DOMAIN = "bigblue"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH, Platform.NUMBER]

async def async_setup(hass, config):
    """Set up the Big Blue component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Big Blue from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Configuration
    email = entry.data.get("email")
    password = entry.data.get("password")
    
    # Initialisation du client API
    api_client = BigBlueAPIClient(email, password)
    
    # Initialisation du coordinateur
    coordinator = BigBlueDataUpdateCoordinator(hass, api_client)
    
    # Stockage des données
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api_client": api_client
    }
    
    # Démarrage du coordinateur
    await coordinator.async_config_entry_first_refresh()
    
    # Configuration des plateformes (capteurs)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Création des appareils Home Assistant pour chaque batterie
    devices_data = coordinator.data
    if devices_data:
        from homeassistant.helpers import device_registry as dr
        
        for device_mac, device_info in devices_data.items():
            # Vérifier que ce n'est pas un device par défaut
            if device_mac == "default" or device_info.get("offline", False):
                _LOGGER.warning(f"⚠️ Device {device_mac} ignoré (par défaut ou hors ligne)")
                continue
                
            device_name = device_info.get("device_name", f"Big Blue {device_mac}")
            device_registry = dr.async_get(hass)
            
            # Vérifier si le device existe déjà
            existing_device = device_registry.async_get_device(identifiers={(DOMAIN, device_mac)})
            if existing_device:
                _LOGGER.info(f"📱 Device existant trouvé: {device_name} ({device_mac})")
                continue
            
            device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, device_mac)},
                name=device_name,
                manufacturer="Big Blue",
                model="Battery System",
                sw_version="1.0.0"
            )
            
            _LOGGER.info(f"📱 Appareil créé: {device_name} ({device_mac})")
    else:
        _LOGGER.warning("⚠️ Aucune donnée du coordinateur - Aucun device créé")
    
    _LOGGER.info("Big Blue integration initialized")
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload Big Blue config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok

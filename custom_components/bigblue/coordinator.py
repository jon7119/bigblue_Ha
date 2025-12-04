"""Coordinateur pour l'intégration Big Blue."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, API_BASE_URL, API_TIMEOUT

_LOGGER = logging.getLogger(__name__)

# Import optionnel de l'API locale
try:
    from .local_api import BigBlueLocalAPIClient
    LOCAL_API_AVAILABLE = True
except ImportError:
    _LOGGER.warning("⚠️ Module local_api non disponible - L'API locale ne sera pas utilisée")
    BigBlueLocalAPIClient = None
    LOCAL_API_AVAILABLE = False


class BigBlueDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinateur pour les données Big Blue."""
    
    def __init__(self, hass: HomeAssistant, api_client, update_interval: int = 30, api_preference: str = "auto") -> None:
        """Initialise le coordinateur.
        
        Args:
            hass: Instance Home Assistant
            api_client: Client API
            update_interval: Intervalle de mise à jour en secondes (défaut: 30)
            api_preference: Préférence API ("auto", "local", "cloud") (défaut: "auto")
        """
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )
        self.api_client = api_client
        self.devices = []  # Liste des appareils trouvés
        self.api_preference = api_preference  # "auto", "local", "cloud"
    
    async def _async_update_data(self):
        """Met à jour les données pour tous les appareils."""
        try:
            # S'assurer que l'authentification est faite
            if not self.api_client.token or not self.api_client.user_id:
                _LOGGER.info("🔐 Authentification nécessaire...")
                auth_success = await self.api_client.authenticate()
                if not auth_success:
                    raise UpdateFailed("Échec de l'authentification")

            # Récupération des appareils (une seule fois)
            if not self.devices:
                _LOGGER.info("📋 Récupération des appareils...")
                devices = await self.api_client.get_devices()
                if not devices:
                    raise UpdateFailed("Aucun appareil trouvé")
                self.devices = devices
                _LOGGER.info(f"📱 {len(devices)} appareil(s) trouvé(s)")

            # Récupération des données pour chaque appareil
            all_devices_data = {}
            
            for device in self.devices:
                device_mac = device.get("bleMac")
                device_name = device.get("name", f"Big Blue {device_mac}")
                
                _LOGGER.info(f"📊 Récupération des données pour {device_name}...")
                
                # Récupération des informations de l'appareil (versions firmware, MAC, etc.) - une seule fois
                device_info = await self.api_client.get_device_info(device_mac)
                
                # Essayer d'abord l'API locale si l'IP est disponible
                data = None
                data_source = "cloud"  # Par défaut, on utilise le cloud
                local_ip = None
                
                # Récupérer l'IP depuis device_info
                if device_info:
                    local_ip = device_info.get("localIp", device_info.get("ip", device_info.get("ipAddress", "")))
                    if local_ip and local_ip.strip():
                        local_ip = local_ip.strip()
                
                # Gérer la préférence API
                if self.api_preference == "local":
                    # Forcer l'utilisation de l'API locale uniquement
                    if not LOCAL_API_AVAILABLE:
                        _LOGGER.warning("⚠️ API locale demandée mais module non disponible, utilisation du cloud")
                        data = await self.api_client.get_device_data_for_mac(device_mac)
                        if data:
                            data_source = "cloud"
                    elif local_ip and local_ip != "Non disponible" and local_ip.strip():
                        _LOGGER.info(f"🔍 Utilisation forcée de l'API locale sur {local_ip}...")
                        try:
                            local_client = BigBlueLocalAPIClient(local_ip)
                            async with local_client:
                                if await local_client.is_available():
                                    local_data = await local_client.get_device_data(device_mac)
                                    if local_data:
                                        _LOGGER.info(f"✅ Données récupérées via API locale pour {device_name}")
                                        data = local_data
                                        data_source = "local"
                                    else:
                                        _LOGGER.warning(f"⚠️ API locale disponible mais aucune donnée pour {device_name}")
                                else:
                                    _LOGGER.warning(f"⚠️ API locale non disponible pour {device_name}")
                        except Exception as e:
                            _LOGGER.error(f"❌ Erreur API locale: {e}")
                    else:
                        _LOGGER.warning(f"⚠️ IP locale non disponible, impossible d'utiliser l'API locale")
                
                elif self.api_preference == "cloud":
                    # Forcer l'utilisation du cloud uniquement
                    _LOGGER.info(f"☁️ Utilisation forcée de l'API cloud pour {device_name}...")
                    data = await self.api_client.get_device_data_for_mac(device_mac)
                    if data:
                        data_source = "cloud"
                
                else:  # "auto" - Essayer local puis cloud
                    # Si on a une IP locale, essayer l'API locale
                    if LOCAL_API_AVAILABLE and local_ip and local_ip != "Non disponible" and local_ip.strip():
                        _LOGGER.info(f"🔍 Tentative de connexion à l'API locale sur {local_ip}...")
                        try:
                            local_client = BigBlueLocalAPIClient(local_ip)
                            async with local_client:
                                if await local_client.is_available():
                                    local_data = await local_client.get_device_data(device_mac)
                                    if local_data:
                                        _LOGGER.info(f"✅ Données récupérées via API locale pour {device_name}")
                                        data = local_data
                                        data_source = "local"
                        except Exception as e:
                            _LOGGER.debug(f"⚠️ API locale indisponible, bascule sur le cloud: {e}")
                    
                    # Si l'API locale n'a pas fonctionné, utiliser le cloud
                    if not data or data_source != "local":
                        _LOGGER.info(f"☁️ Utilisation de l'API cloud pour {device_name}...")
                        data = await self.api_client.get_device_data_for_mac(device_mac)
                        if data:
                            data_source = "cloud"
                
                if data:
                    # Récupération de la configuration pour les coûts
                    device_config = await self.api_client.get_device_settings(device_mac)
                    price_per_kwh = device_config.get("pricePerKwh", 0.0) if device_config else 0.0
                    currency_code = device_config.get("currencyCode", "EUR") if device_config else "EUR"
                    
                    # Récupération des OTA
                    ota_infos = await self.api_client.get_ota_infos(device_mac, device_name)
                    ota_progress = await self.api_client.get_ota_status(device_mac)
                    
                    # Formatage des données pour cet appareil
                    formatted_data = {
                        # Batterie - Données existantes
                        "soc": data.get("totalSoc", 0) / 10,  # Conversion en %
                        "soh": data.get("totalSoh", 0) / 10,  # Conversion en %
                        "voltage": data.get("totalVoltage", 0) / 10,  # Conversion en V
                        "current": data.get("totalCurrent", 0),
                        "power": data.get("totalPower", 0) / 10,  # Conversion en W
                        "remaining_capacity": data.get("totalRemainingCapacity", 0) / 1000,  # Conversion en kWh
                        "rated_capacity": data.get("totalRatedCapacity", 0) / 1000,  # Conversion en kWh
                        "battery_count": data.get("batteryCount", 0),
                        "battery_voltage": data.get("batteryVoltage", 0) / 10,  # Conversion en V
                        "battery_current": data.get("batteryCurrent", 0),
                        "battery_power": data.get("batteryPower", 0) / 10,  # Conversion en W
                        "battery_warning": data.get("batteryWarning", 0),
                        "batteries": data.get("batteries", ""),
                        
                        # Panneaux Solaires - PV1 et PV2 existants
                        "pv1_voltage": data.get("pv1V", 0) / 10,  # Conversion en V
                        "pv1_current": data.get("pv1A", 0),
                        "pv1_power": data.get("pv1W", 0) / 10,  # Conversion en W
                        "pv2_voltage": data.get("pv2V", 0) / 10,  # Conversion en V
                        "pv2_current": data.get("pv2A", 0),
                        "pv2_power": data.get("pv2W", 0) / 10,  # Conversion en W
                        "pv_total_power": data.get("pvTotalPower", 0) / 10,  # Conversion en W
                        "pv_num": data.get("pvNum", 0),
                        
                        # Panneaux Solaires - PV3 et PV4 (nouveaux)
                        "pv3": data.get("pv3", 0),
                        "pv3_current": data.get("pv3A", 0),
                        "pv3_power": data.get("pv3W", 0) / 10,  # Conversion en W
                        "pv4_voltage": data.get("pv4V", 0) / 10,  # Conversion en V
                        "pv4_current": data.get("pv4A", 0),
                        "pv4_power": data.get("pv4W", 0) / 10,  # Conversion en W
                        
                        # Onduleur (Inverter) - Nouveaux
                        "inverter_status": data.get("inverterStatus", 0),
                        "inverter_model": data.get("inverterModel", 0),
                        "inverter_current": data.get("inverterCurrent", 0),
                        "inverter_voltage": data.get("inverterVoltage", 0) / 10,  # Conversion en V
                        "inverter_frequency": data.get("inverterFrequency", 0) / 10,  # Conversion en Hz
                        "inverter_temp_min": data.get("inverterTempMin", 0) / 10,  # Conversion en °C
                        "inverter_temp_max": data.get("inverterTempMax", 0) / 10,  # Conversion en °C
                        "inverter_alert": data.get("inverterAlert", 0),
                        
                        # Réseau (Grid) - Nouveaux
                        "grid_voltage": data.get("gridVoltage", 0) / 10,  # Conversion en V
                        "grid_current": data.get("gridCurrent", 0),
                        "grid_frequency": data.get("gridFrequency", 0) / 10,  # Conversion en Hz
                        "grid_countdown": data.get("gridCountdown", 0),
                        
                        # Puissance Avancée - Nouveaux
                        "active_power": data.get("activePower", 0) / 10,  # Conversion en W
                        "apparent_power": data.get("apparentPower", 0) / 10,  # Conversion en VA
                        "reactive_power": data.get("reactivePower", 0) / 10,  # Conversion en VAR
                        "power_factor": data.get("powerFactor", 0) / 100,  # Conversion (0-1)
                        "power_general": data.get("power", 0) / 10,  # Conversion en W
                        "voltage_general": data.get("voltage", 0) / 10,  # Conversion en V
                        "current_general": data.get("current", 0),
                        "leakage_current": data.get("leakageCurrent", 0),
                        "total_heat_power": data.get("totalHeatPower", 0) / 10,  # Conversion en W
                        
                        # Énergie - Données existantes
                        "daily_generation": data.get("dailyGeneration", 0) / 1000,  # Conversion en kWh
                        "total_generation": data.get("totalGeneration", 0) / 1000,  # Conversion en kWh
                        "daily_output_energy": data.get("dailyOutputEnergy", 0) / 1000,  # Conversion en kWh
                        "total_output_energy": data.get("totalOutputEnergy", 0) / 1000,  # Conversion en kWh
                        
                        # Énergie d'Entrée - Nouveaux
                        "daily_input_energy": data.get("dailyInputEnergy", 0) / 1000,  # Conversion en kWh
                        "total_input_energy": data.get("totalInputEnergy", 0) / 1000,  # Conversion en kWh
                        "total_charge_energy": data.get("totalChargeEnergy", 0) / 1000,  # Conversion en kWh
                        "total_charge_remaining_time": data.get("totalChargeRemainingTime", 0) / 3600,  # Conversion en heures
                        
                        # Température - Données existantes + seuils
                        "max_temperature": data.get("maxTemperature", 0) / 10,  # Conversion en °C
                        "min_temperature": data.get("minTemperature", 0) / 10,  # Conversion en °C
                        "temp_max": data.get("tempMax", 0) / 10,  # Conversion en °C
                        "temp_min": data.get("tempMin", 0) / 10,  # Conversion en °C
                        
                        # CO2 et Économies - Données existantes
                        "daily_co2_savings": data.get("dailyCo2Savings", 0),
                        
                        # Temps de fonctionnement - Données existantes
                        "daily_runtime": data.get("dailyRuntime", 0) / 3600,  # Conversion en heures
                        "total_runtime": data.get("totalRuntime", 0) / 3600,  # Conversion en heures
                        
                        # Statut et Alertes - Nouveaux
                        "status": data.get("Status", 0),
                        "device_alert": data.get("deviceAlert", 0),
                        
                        # Configuration
                        "current_mode": await self.api_client.get_current_mode(device_mac),
                        "discharge_threshold": await self.api_client.get_discharge_threshold(device_mac),
                        "charge_threshold": await self.api_client.get_charge_threshold(device_mac),
                        
                        # Paramètres configurables (settings) - stockés pour les entités numériques et switches
                        "settings": device_config if device_config else {},
                        "output_power": device_config.get("bmsPower", 20) if device_config else 20,  # Puissance de sortie (bmsPower en %)
                        
                        # Coûts et Économies - Nouveaux
                        "price_per_kwh": price_per_kwh,
                        "currency_code": currency_code,
                        "daily_cost_saved": (data.get("dailyOutputEnergy", 0) / 1000) * price_per_kwh if price_per_kwh > 0 else 0,
                        "total_cost_saved": (data.get("totalOutputEnergy", 0) / 1000) * price_per_kwh if price_per_kwh > 0 else 0,
                        
                        # OTA (Mises à jour firmware) - Nouveaux
                        "ota_available": len(ota_infos) > 0 if ota_infos else False,
                        "ota_version": ota_infos[0].get("version", "") if ota_infos and len(ota_infos) > 0 else "",
                        "ota_progress": ota_progress.get("progress", 0) if ota_progress else 0,
                        "ota_status": ota_progress.get("status", 0) if ota_progress else 0,
                        "ota_infos": ota_infos if ota_infos else [],
                        # Détails OTA supplémentaires
                        "ota_file_url": ota_infos[0].get("fileUrl", "") if ota_infos and len(ota_infos) > 0 else "",
                        "ota_size": ota_infos[0].get("size", 0) if ota_infos and len(ota_infos) > 0 else 0,
                        "ota_md5": ota_infos[0].get("MD5", "") if ota_infos and len(ota_infos) > 0 else "",
                        "ota_module_name": ota_infos[0].get("moduleName", "") if ota_infos and len(ota_infos) > 0 else "",
                        "ota_release_notes_cn": ota_infos[0].get("releaseNotesCN", "") if ota_infos and len(ota_infos) > 0 else "",
                        "ota_release_notes_en": ota_infos[0].get("releaseNotesEN", "") if ota_infos and len(ota_infos) > 0 else "",
                        "ota_status_text": ota_infos[0].get("status", "") if ota_infos and len(ota_infos) > 0 else "",
                        "ota_device_code": ota_infos[0].get("deviceCode", 0) if ota_infos and len(ota_infos) > 0 else 0,
                        "ota_id": ota_infos[0].get("ID", 0) if ota_infos and len(ota_infos) > 0 else 0,
                        
                        # Informations Appareil (Versions firmware, MAC, etc.) - Nouveaux
                        "bms_version": device_info.get("bmsVersion", "") if device_info else "",
                        "com_version": device_info.get("comVersion", "") if device_info else "",
                        "control_version": device_info.get("controlVersion", "") if device_info else "",
                        "inv_version": device_info.get("invVersion", "") if device_info else "",
                        "wifi_mac": device_info.get("wifiMac", "") if device_info else "",
                        "ble_mac": device_info.get("bleMac", device_mac) if device_info else device_mac,
                        "wifi_status": device_info.get("wifiStatus", 0) if device_info else 0,
                        "device_code": device_info.get("deviceCode", 0) if device_info else 0,
                        # Adresse IP locale (si disponible dans l'API)
                        "local_ip": device_info.get("localIp", device_info.get("ip", device_info.get("ipAddress", ""))) if device_info else "",
                        
                        # Métadonnées
                        "last_update": data.get("last_update"),
                        "device_mac": device_mac,
                        "device_name": device_name,
                        "data_source": data_source,  # "local" ou "cloud"
                    }
                    
                    all_devices_data[device_mac] = formatted_data
                    
                    _LOGGER.info(f"✅ Données mises à jour pour {device_name}: SOC={formatted_data.get('soc', 'N/A')}%, "
                                f"Puissance PV={formatted_data.get('pv_total_power', 'N/A')}W")
                else:
                    _LOGGER.warning(f"⚠️ Aucune donnée pour {device_name} - Device ignoré (pas de données par défaut)")
                    # Ne pas créer de données par défaut pour éviter les devices "default"
            
            return all_devices_data
            
        except Exception as err:
            _LOGGER.error(f"❌ Erreur lors de la mise à jour des données: {err}")
            raise UpdateFailed(f"Erreur API: {err}")


class BigBlueAPIClient:
    """Client API pour Powafree."""
    
    def __init__(self, email: str, password: str):
        """Initialise le client API."""
        self.email = email
        self.password = password
        self.base_url = API_BASE_URL
        self.token = None
        self.user_id = None
        self.device_mac = None
        self.session = None
    
    async def __aenter__(self):
        """Context manager entry."""
        import aiohttp
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.session:
            await self.session.close()
    
    async def authenticate(self) -> bool:
        """Authentification sur l'API Powafree."""
        try:
            # Initialiser la session si nécessaire
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()
            
            login_data = {
                "email": self.email,
                "password": self.password
            }
            
            headers = {
                "Accept": "application/json",
                "Accept-Language": "fr",
                "Content-Type": "application/json",
                "User-Agent": "okhttp/3.14.9"
            }
            
            _LOGGER.info(f"🔐 Tentative de connexion à {self.base_url}/api/user/login/email")
            _LOGGER.debug(f"Headers: {headers}")
            _LOGGER.debug(f"Email: {self.email}")
            
            async with self.session.post(
                f"{self.base_url}/api/user/login/email",
                json=login_data,
                headers=headers
            ) as response:
                
                _LOGGER.info(f"📥 Réponse reçue: HTTP {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.debug(f"Données de réponse: {data}")
                    
                    if data.get("code") == 0:
                        user_data = data["data"]
                        self.token = user_data["token"]
                        self.user_id = user_data["userId"]
                        
                        _LOGGER.info(f"✅ Authentification réussie pour {user_data.get('name', 'N/A')}")
                        _LOGGER.info(f"User ID: {self.user_id}")
                        _LOGGER.info(f"Token: {self.token[:20]}...")
                        return True
                    else:
                        _LOGGER.error(f"❌ Erreur d'authentification: {data.get('message')}")
                        _LOGGER.error(f"Code d'erreur: {data.get('code')}")
                        return False
                else:
                    response_text = await response.text()
                    _LOGGER.error(f"❌ Erreur HTTP: {response.status}")
                    _LOGGER.error(f"Réponse: {response_text[:200]}...")
                    return False
                    
        except Exception as e:
            _LOGGER.error(f"❌ Erreur de connexion: {e}")
            _LOGGER.error(f"Type d'erreur: {type(e).__name__}")
            _LOGGER.error(f"URL tentée: {self.base_url}/api/user/login/email")
            return False
    
    async def get_devices(self) -> list:
        """Récupère la liste des appareils."""
        if not self.token or not self.user_id:
            _LOGGER.error("Token ou User ID manquant pour get_devices")
            return []
        
        try:
            # Initialiser la session si nécessaire
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Accept": "application/json",
                "Accept-Language": "fr",
                "Authorization": self.token,
                "Content-Type": "application/json",
                "User-Agent": "okhttp/3.14.9"
            }
            
            data = {"userId": self.user_id}
            
            _LOGGER.info(f"📋 Récupération des appareils depuis {self.base_url}/api/devices/list")
            _LOGGER.debug(f"User ID: {self.user_id}")
            
            async with self.session.post(
                f"{self.base_url}/api/devices/list",
                json=data,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    if response_data.get("code") == 0:
                        devices = response_data.get("data", [])
                        if devices:
                            self.device_mac = devices[0].get("bleMac")
                            _LOGGER.info(f"Appareil trouvé: {devices[0].get('name', 'N/A')}")
                        return devices
                    else:
                        _LOGGER.error(f"Erreur API: {response_data.get('message')}")
                        return []
                else:
                    _LOGGER.error(f"Erreur HTTP: {response.status}")
                    return []
                    
        except Exception as e:
            _LOGGER.error(f"❌ Erreur récupération appareils: {e}")
            _LOGGER.error(f"Type d'erreur: {type(e).__name__}")
            return []
    
    async def get_device_data(self) -> dict:
        """Récupère les données de l'appareil."""
        if not self.token or not self.user_id or not self.device_mac:
            _LOGGER.error("Token, User ID ou Device MAC manquant pour get_device_data")
            return {}
        
        try:
            # Initialiser la session si nécessaire
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Accept": "application/json",
                "Accept-Language": "fr",
                "Authorization": self.token,
                "Content-Type": "application/json",
                "User-Agent": "okhttp/3.14.9"
            }
            
            data = {
                "userId": self.user_id,
                "bleMac": self.device_mac
            }
            
            _LOGGER.info(f"📊 Récupération des données depuis {self.base_url}/api/devices/last_data")
            _LOGGER.debug(f"User ID: {self.user_id}, Device MAC: {self.device_mac}")
            
            # Récupération des données en temps réel
            async with self.session.post(
                f"{self.base_url}/api/devices/last_data",
                json=data,
                headers=headers
            ) as response:
                
                _LOGGER.info(f"📥 Réponse données: HTTP {response.status}")
                
                if response.status == 200:
                    response_data = await response.json()
                    _LOGGER.debug(f"Données brutes: {response_data}")
                    
                    if response_data.get("code") == 0:
                        device_data = response_data.get("data", {})
                        device_data["last_update"] = asyncio.get_event_loop().time()
                        
                        # Conversion des valeurs si nécessaire
                        if "totalSoc" in device_data:
                            device_data["totalSoc"] = device_data["totalSoc"] / 10  # Conversion en %
                        if "totalSoh" in device_data:
                            device_data["totalSoh"] = device_data["totalSoh"] / 10  # Conversion en %
                        if "maxTemperature" in device_data:
                            device_data["maxTemperature"] = device_data["maxTemperature"] / 10  # Conversion en °C
                        if "minTemperature" in device_data:
                            device_data["minTemperature"] = device_data["minTemperature"] / 10  # Conversion en °C
                        
                        _LOGGER.info(f"✅ Données récupérées: SOC={device_data.get('totalSoc', 'N/A')}%, "
                                   f"Puissance PV={device_data.get('pvTotalPower', 'N/A')}W, "
                                   f"Production journalière={device_data.get('dailyGeneration', 'N/A')}Wh")
                        
                        return device_data
                    else:
                        _LOGGER.error(f"❌ Erreur API: {response_data.get('message')}")
                        _LOGGER.error(f"Code d'erreur: {response_data.get('code')}")
                        return {}
                else:
                    response_text = await response.text()
                    _LOGGER.error(f"❌ Erreur HTTP: {response.status}")
                    _LOGGER.error(f"Réponse: {response_text[:200]}...")
                    return {}
                    
        except Exception as e:
            _LOGGER.error(f"❌ Erreur récupération données: {e}")
            _LOGGER.error(f"Type d'erreur: {type(e).__name__}")
            return {}
    
    async def get_device_data_for_mac(self, device_mac: str) -> dict:
        """Récupère les données d'un appareil spécifique par son MAC."""
        if not self.token or not self.user_id or not device_mac:
            _LOGGER.error("Token, User ID ou Device MAC manquant pour get_device_data_for_mac")
            return {}
        
        try:
            # Initialiser la session si nécessaire
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Accept": "application/json",
                "Accept-Language": "fr",
                "Authorization": self.token,
                "Content-Type": "application/json",
                "User-Agent": "okhttp/3.14.9"
            }
            
            data = {
                "userId": self.user_id,
                "bleMac": device_mac
            }
            
            _LOGGER.info(f"📊 Récupération des données pour {device_mac} depuis {self.base_url}/api/devices/last_data")
            
            # Récupération des données en temps réel
            async with self.session.post(
                f"{self.base_url}/api/devices/last_data",
                json=data,
                headers=headers
            ) as response:
                
                _LOGGER.info(f"📥 Réponse données pour {device_mac}: HTTP {response.status}")
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    if response_data.get("code") == 0:
                        device_data = response_data.get("data", {})
                        device_data["last_update"] = asyncio.get_event_loop().time()
                        
                        # Les valeurs sont déjà dans le bon format depuis l'API
                        
                        _LOGGER.info(f"✅ Données récupérées pour {device_mac}: SOC={device_data.get('totalSoc', 'N/A')/10:.1f}%, "
                                    f"Puissance PV={device_data.get('pvTotalPower', 'N/A')}W")
                        
                        return device_data
                    else:
                        # Gestion des erreurs d'authentification
                        if response_data.get("code") == 1009:  # Invalid token
                            _LOGGER.warning(f"🔄 Token expiré pour {device_mac}, tentative de renouvellement...")
                            auth_success = await self.authenticate()
                            if auth_success:
                                _LOGGER.info(f"✅ Token renouvelé, nouvelle tentative pour {device_mac}")
                                # Retry avec le nouveau token
                                headers["Authorization"] = self.token
                                async with self.session.post(
                                    f"{self.base_url}/api/devices/last_data",
                                    json=data,
                                    headers=headers
                                ) as retry_response:
                                    if retry_response.status == 200:
                                        retry_data = await retry_response.json()
                                        if retry_data.get("code") == 0:
                                            device_data = retry_data.get("data", {})
                                            device_data["last_update"] = asyncio.get_event_loop().time()
                                            _LOGGER.info(f"✅ Données récupérées après renouvellement: SOC={device_data.get('totalSoc', 'N/A')/10:.1f}%")
                                            return device_data
                            else:
                                _LOGGER.error(f"❌ Échec du renouvellement du token pour {device_mac}")
                                return {}
                        else:
                            error_message = response_data.get('message', 'Erreur inconnue')
                            error_code = response_data.get('code', 'N/A')
                            
                            # Gestion spécifique des erreurs
                            if error_code == 1013:  # Record not found (code réel de l'API)
                                _LOGGER.warning(f"⚠️ Device {device_mac} non trouvé dans l'API (Record not found)")
                                return {}
                            elif error_code == 1002:  # Device offline
                                _LOGGER.warning(f"⚠️ Device {device_mac} hors ligne")
                                return {}
                            else:
                                _LOGGER.error(f"❌ Erreur API pour {device_mac}: {error_message} (Code: {error_code})")
                                return {}
                else:
                    response_text = await response.text()
                    _LOGGER.error(f"❌ Erreur HTTP pour {device_mac}: {response.status}")
                    return {}
                    
        except Exception as e:
            _LOGGER.error(f"❌ Erreur récupération données pour {device_mac}: {e}")
            return {}
    
    async def set_device_mode(self, device_mac: str, mode: int) -> bool:
        """Change le mode de fonctionnement d'un appareil."""
        if not self.token or not self.user_id or not device_mac:
            _LOGGER.error("Token, User ID ou Device MAC manquant pour set_device_mode")
            return False
        
        try:
            # Initialiser la session si nécessaire
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Accept": "application/json",
                "Accept-Language": "fr",
                "Authorization": self.token,
                "Content-Type": "application/json",
                "User-Agent": "okhttp/3.14.9"
            }
            
            # Récupérer les paramètres actuels pour préserver les scènes (periodDetail)
            current_settings = await self.get_device_settings(device_mac)
            if not current_settings:
                _LOGGER.error(f"❌ Impossible de récupérer les paramètres actuels pour {device_mac}")
                return False
            
            # Données pour changer le mode - on préserve TOUS les paramètres existants
            data = {
                "bleMac": device_mac,
                "bmsEnable": current_settings.get("bmsEnable", True),
                "bmsPower": current_settings.get("bmsPower", 12),
                "ctAPower": current_settings.get("ctAPower", 0),
                "ctBPower": current_settings.get("ctBPower", 0),
                "ctCPower": current_settings.get("ctCPower", 0),
                "ctEnable": current_settings.get("ctEnable", 0),
                "ctTotalPower": current_settings.get("ctTotalPower", 0),
                "currencyCode": current_settings.get("currencyCode", "EUR"),
                "deviceControl": current_settings.get("deviceControl", 0),
                "gridCode": current_settings.get("gridCode", 0),
                "gridControl": current_settings.get("gridControl", 0),
                "gridEnable": current_settings.get("gridEnable", 0),
                "gridTime": current_settings.get("gridTime", 0),
                "mode": mode,  # Seul le mode change
                "otaStatus": current_settings.get("otaStatus", 1),
                "peakShavingDetails": current_settings.get("peakShavingDetails", ["|00:00-23:59|4000|"]),
                "periodDetail": current_settings.get("periodDetail", [
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|3000|", "|22:00-23:59|1000|"],
                    ["|00:00-08:00|1000|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|3000|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"]
                ]),
                "periods": current_settings.get("periods", 0),
                "pfSwitch": current_settings.get("pfSwitch", 0),
                "pfValue": current_settings.get("pfValue", 0),
                "pricePerKwh": current_settings.get("pricePerKwh", 0.3),
                "soc": current_settings.get("soc", 10),
                "timezone": current_settings.get("timezone", 2.0),
                "userId": self.user_id
            }
            
            _LOGGER.info(f"🔧 Changement du mode {mode} pour {device_mac}...")
            
            async with self.session.post(
                f"{self.base_url}/api/devices/setting/upload",
                json=data,
                headers=headers
            ) as response:
                
                _LOGGER.info(f"📥 Réponse changement mode: HTTP {response.status}")
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    if response_data.get("code") == 0:
                        _LOGGER.info(f"✅ Mode {mode} activé avec succès pour {device_mac}")
                        return True
                    else:
                        _LOGGER.error(f"❌ Erreur API changement mode: {response_data.get('message')}")
                        return False
                else:
                    response_text = await response.text()
                    _LOGGER.error(f"❌ Erreur HTTP changement mode: {response.status}")
                    return False
                    
        except Exception as e:
            _LOGGER.error(f"❌ Erreur changement mode pour {device_mac}: {e}")
            return False
    
    async def get_current_mode(self, device_mac: str) -> int:
        """Récupère le mode actuel d'un appareil."""
        if not self.token or not self.user_id or not device_mac:
            _LOGGER.error("Token, User ID ou Device MAC manquant pour get_current_mode")
            return 1  # Mode par défaut
        
        try:
            # Initialiser la session si nécessaire
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Accept": "application/json",
                "Accept-Language": "fr",
                "Authorization": self.token,
                "Content-Type": "application/json",
                "User-Agent": "okhttp/3.14.9"
            }
            
            data = {
                "userId": self.user_id,
                "bleMac": device_mac
            }
            
            _LOGGER.info(f"🔍 Récupération du mode actuel pour {device_mac}...")
            
            async with self.session.post(
                f"{self.base_url}/api/devices/setting/download",
                json=data,
                headers=headers
            ) as response:
                
                _LOGGER.info(f"📥 Réponse mode actuel: HTTP {response.status}")
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    if response_data.get("code") == 0:
                        device_settings = response_data.get("data", {})
                        current_mode = device_settings.get("mode", 1)
                        _LOGGER.info(f"✅ Mode actuel récupéré: {current_mode}")
                        return current_mode
                    else:
                        _LOGGER.error(f"❌ Erreur API mode actuel: {response_data.get('message')}")
                        return 1
                else:
                    response_text = await response.text()
                    _LOGGER.error(f"❌ Erreur HTTP mode actuel: {response.status}")
                    return 1
                    
        except Exception as e:
            _LOGGER.error(f"❌ Erreur récupération mode actuel pour {device_mac}: {e}")
            return 1
    
    async def set_discharge_threshold(self, device_mac: str, threshold: int) -> bool:
        """Change le seuil de décharge d'un appareil."""
        if not self.token or not self.user_id or not device_mac:
            _LOGGER.error("Token, User ID ou Device MAC manquant pour set_discharge_threshold")
            return False
        
        try:
            # Initialiser la session si nécessaire
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Accept": "application/json",
                "Accept-Language": "fr",
                "Authorization": self.token,
                "Content-Type": "application/json",
                "User-Agent": "okhttp/3.14.9"
            }
            
            # Récupérer les paramètres actuels
            current_settings = await self.get_device_settings(device_mac)
            if not current_settings:
                _LOGGER.error(f"❌ Impossible de récupérer les paramètres actuels pour {device_mac}")
                return False
            
            # Mettre à jour le seuil de décharge avec tous les paramètres requis
            data = {
                "bleMac": device_mac,
                "bmsEnable": current_settings.get("bmsEnable", True),
                "bmsPower": threshold,
                "ctAPower": current_settings.get("ctAPower", 0),
                "ctBPower": current_settings.get("ctBPower", 0),
                "ctCPower": current_settings.get("ctCPower", 0),
                "ctEnable": current_settings.get("ctEnable", 0),
                "ctTotalPower": current_settings.get("ctTotalPower", 0),
                "currencyCode": current_settings.get("currencyCode", "EUR"),
                "deviceControl": current_settings.get("deviceControl", 0),
                "gridCode": current_settings.get("gridCode", 0),
                "gridControl": current_settings.get("gridControl", 0),
                "gridEnable": current_settings.get("gridEnable", 0),
                "gridTime": current_settings.get("gridTime", 0),
                "mode": current_settings.get("mode", 1),
                "otaStatus": current_settings.get("otaStatus", 1),
                "peakShavingDetails": current_settings.get("peakShavingDetails", ["|00:00-23:59|4000|"]),
                "periodDetail": current_settings.get("periodDetail", [
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|3000|", "|22:00-23:59|1000|"],
                    ["|00:00-08:00|1000|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|3000|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"]
                ]),
                "periods": current_settings.get("periods", 0),
                "pfSwitch": current_settings.get("pfSwitch", 0),
                "pfValue": current_settings.get("pfValue", 0),
                "pricePerKwh": current_settings.get("pricePerKwh", 0.3),
                "soc": current_settings.get("soc", 10),
                "timezone": current_settings.get("timezone", 2.0),
                "userId": self.user_id
            }
            
            _LOGGER.info(f"🔧 Modification du seuil de décharge à {threshold}% pour {device_mac}...")
            
            async with self.session.post(
                f"{self.base_url}/api/devices/setting/upload",
                json=data,
                headers=headers
            ) as response:
                
                _LOGGER.info(f"📥 Réponse seuil de décharge: HTTP {response.status}")
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    if response_data.get("code") == 0:
                        _LOGGER.info(f"✅ Seuil de décharge mis à jour à {threshold}% pour {device_mac}")
                        return True
                    else:
                        _LOGGER.error(f"❌ Erreur API seuil de décharge: {response_data.get('message')}")
                        return False
                else:
                    response_text = await response.text()
                    _LOGGER.error(f"❌ Erreur HTTP seuil de décharge: {response.status}")
                    return False
                    
        except Exception as e:
            _LOGGER.error(f"❌ Erreur modification seuil de décharge pour {device_mac}: {e}")
            return False
    
    async def get_device_settings(self, device_mac: str) -> dict:
        """Récupère les paramètres actuels d'un appareil."""
        if not self.token or not self.user_id or not device_mac:
            _LOGGER.error("Token, User ID ou Device MAC manquant pour get_device_settings")
            return {}
        
        try:
            # Initialiser la session si nécessaire
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Accept": "application/json",
                "Accept-Language": "fr",
                "Authorization": self.token,
                "Content-Type": "application/json",
                "User-Agent": "okhttp/3.14.9"
            }
            
            data = {
                "userId": self.user_id,
                "bleMac": device_mac
            }
            
            async with self.session.post(
                f"{self.base_url}/api/devices/setting/download",
                json=data,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    if response_data.get("code") == 0:
                        device_settings = response_data.get("data", {})
                        return device_settings
                    else:
                        _LOGGER.error(f"❌ Erreur API paramètres: {response_data.get('message')}")
                        return {}
                else:
                    _LOGGER.error(f"❌ Erreur HTTP paramètres: {response.status}")
                    return {}
                    
        except Exception as e:
            _LOGGER.error(f"❌ Erreur récupération paramètres pour {device_mac}: {e}")
            return {}
    
    async def get_discharge_threshold(self, device_mac: str) -> int:
        """Récupère le seuil de décharge actuel d'un appareil."""
        if not self.token or not self.user_id or not device_mac:
            _LOGGER.error("Token, User ID ou Device MAC manquant pour get_discharge_threshold")
            return 10  # Valeur par défaut
        
        try:
            # Initialiser la session si nécessaire
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Accept": "application/json",
                "Accept-Language": "fr",
                "Authorization": self.token,
                "Content-Type": "application/json",
                "User-Agent": "okhttp/3.14.9"
            }
            
            data = {
                "userId": self.user_id,
                "bleMac": device_mac
            }
            
            _LOGGER.info(f"🔍 Récupération du seuil de décharge pour {device_mac}...")
            
            async with self.session.post(
                f"{self.base_url}/api/devices/setting/download",
                json=data,
                headers=headers
            ) as response:
                
                _LOGGER.info(f"📥 Réponse seuil de décharge: HTTP {response.status}")
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    if response_data.get("code") == 0:
                        device_settings = response_data.get("data", {})
                        threshold = device_settings.get("bmsPower", 10)
                        _LOGGER.info(f"✅ Seuil de décharge récupéré: {threshold}%")
                        return threshold
                    else:
                        _LOGGER.error(f"❌ Erreur API seuil de décharge: {response_data.get('message')}")
                        return 10
                else:
                    response_text = await response.text()
                    _LOGGER.error(f"❌ Erreur HTTP seuil de décharge: {response.status}")
                    return 10
                    
        except Exception as e:
            _LOGGER.error(f"❌ Erreur récupération seuil de décharge pour {device_mac}: {e}")
            return 10
    
    async def get_ota_infos(self, device_mac: str, device_name: str = None) -> list:
        """Récupère les informations sur les mises à jour OTA disponibles."""
        if not self.token or not self.user_id or not device_mac:
            _LOGGER.error("Token, User ID ou Device MAC manquant pour get_ota_infos")
            return []
        
        try:
            # Initialiser la session si nécessaire
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Accept": "application/json",
                "Accept-Language": "fr",
                "Authorization": self.token,
                "Content-Type": "application/json",
                "User-Agent": "okhttp/3.14.9"
            }
            
            # L'API nécessite userId, deviceName et mac (pas bleMac)
            data = {
                "userId": self.user_id,
                "deviceName": device_name or f"Big Blue {device_mac}",
                "mac": device_mac
            }
            
            _LOGGER.info(f"🔍 Récupération des informations OTA pour {device_mac}...")
            
            async with self.session.post(
                f"{self.base_url}/api/devices/ota_infos",
                json=data,
                headers=headers
            ) as response:
                
                _LOGGER.info(f"📥 Réponse OTA infos: HTTP {response.status}")
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    if response_data.get("code") == 0:
                        ota_infos = response_data.get("data", [])
                        _LOGGER.info(f"✅ {len(ota_infos)} mise(s) à jour OTA disponible(s)")
                        return ota_infos
                    else:
                        _LOGGER.error(f"❌ Erreur API OTA infos: {response_data.get('message')}")
                        return []
                else:
                    response_text = await response.text()
                    _LOGGER.error(f"❌ Erreur HTTP OTA infos: {response.status}")
                    return []
                    
        except Exception as e:
            _LOGGER.error(f"❌ Erreur récupération OTA infos pour {device_mac}: {e}")
            return []
    
    async def get_ota_status(self, device_mac: str) -> dict:
        """Récupère le statut de la mise à jour OTA en cours."""
        if not self.token or not self.user_id or not device_mac:
            _LOGGER.error("Token, User ID ou Device MAC manquant pour get_ota_status")
            return {}
        
        try:
            # Initialiser la session si nécessaire
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Accept": "application/json",
                "Accept-Language": "fr",
                "Authorization": self.token,
                "Content-Type": "application/json",
                "User-Agent": "okhttp/3.14.9"
            }
            
            data = {
                "userId": self.user_id,
                "bleMac": device_mac
            }
            
            _LOGGER.info(f"🔍 Récupération du statut OTA pour {device_mac}...")
            
            async with self.session.post(
                f"{self.base_url}/api/devices/ota_status",
                json=data,
                headers=headers
            ) as response:
                
                _LOGGER.info(f"📥 Réponse OTA status: HTTP {response.status}")
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    if response_data.get("code") == 0:
                        ota_progress = response_data.get("data", {})
                        _LOGGER.info(f"✅ Statut OTA récupéré: {ota_progress.get('progress', 0)}%")
                        return ota_progress
                    else:
                        _LOGGER.error(f"❌ Erreur API OTA status: {response_data.get('message')}")
                        return {}
                else:
                    response_text = await response.text()
                    _LOGGER.error(f"❌ Erreur HTTP OTA status: {response.status}")
                    return {}
                    
        except Exception as e:
            _LOGGER.error(f"❌ Erreur récupération OTA status pour {device_mac}: {e}")
            return {}
    
    async def get_device_info(self, device_mac: str) -> dict:
        """Récupère les informations de l'appareil (versions firmware, MAC, etc.)."""
        if not self.token or not self.user_id or not device_mac:
            _LOGGER.error("Token, User ID ou Device MAC manquant pour get_device_info")
            return {}
        
        try:
            # Initialiser la session si nécessaire
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Accept": "application/json",
                "Accept-Language": "fr",
                "Authorization": self.token,
                "Content-Type": "application/json",
                "User-Agent": "okhttp/3.14.9"
            }
            
            data = {
                "userId": self.user_id,
                "bleMac": device_mac
            }
            
            _LOGGER.info(f"🔍 Récupération des informations de l'appareil pour {device_mac}...")
            
            async with self.session.post(
                f"{self.base_url}/api/devices/info",
                json=data,
                headers=headers
            ) as response:
                
                _LOGGER.info(f"📥 Réponse informations appareil: HTTP {response.status}")
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    if response_data.get("code") == 0:
                        device_info = response_data.get("data", {})
                        _LOGGER.info(f"✅ Informations appareil récupérées: BMS={device_info.get('bmsVersion', 'N/A')}, "
                                   f"WiFi Status={device_info.get('wifiStatus', 'N/A')}")
                        _LOGGER.debug(f"📋 Données complètes device_info: {device_info}")  # Log pour voir toutes les données
                        return device_info
                    else:
                        _LOGGER.error(f"❌ Erreur API informations appareil: {response_data.get('message')}")
                        return {}
                else:
                    response_text = await response.text()
                    _LOGGER.error(f"❌ Erreur HTTP informations appareil: {response.status}")
                    return {}
                    
        except Exception as e:
            _LOGGER.error(f"❌ Erreur récupération informations appareil pour {device_mac}: {e}")
            return {}
    
    async def get_charge_threshold(self, device_mac: str) -> int:
        """Récupère le seuil de charge actuel d'un appareil."""
        if not self.token or not self.user_id or not device_mac:
            _LOGGER.error("Token, User ID ou Device MAC manquant pour get_charge_threshold")
            return 90  # Valeur par défaut (90%)
        
        try:
            # Initialiser la session si nécessaire
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Accept": "application/json",
                "Accept-Language": "fr",
                "Authorization": self.token,
                "Content-Type": "application/json",
                "User-Agent": "okhttp/3.14.9"
            }
            
            data = {
                "userId": self.user_id,
                "bleMac": device_mac
            }
            
            _LOGGER.info(f"🔍 Récupération du seuil de charge pour {device_mac}...")
            
            async with self.session.post(
                f"{self.base_url}/api/devices/setting/download",
                json=data,
                headers=headers
            ) as response:
                
                _LOGGER.info(f"📥 Réponse seuil de charge: HTTP {response.status}")
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    if response_data.get("code") == 0:
                        device_settings = response_data.get("data", {})
                        threshold = device_settings.get("soc", 90)  # soc est le seuil de charge
                        _LOGGER.info(f"✅ Seuil de charge récupéré: {threshold}%")
                        return threshold
                    else:
                        _LOGGER.error(f"❌ Erreur API seuil de charge: {response_data.get('message')}")
                        return 90
                else:
                    response_text = await response.text()
                    _LOGGER.error(f"❌ Erreur HTTP seuil de charge: {response.status}")
                    return 90
                    
        except Exception as e:
            _LOGGER.error(f"❌ Erreur récupération seuil de charge pour {device_mac}: {e}")
            return 90
    
    async def set_charge_threshold(self, device_mac: str, threshold: int) -> bool:
        """Change le seuil de charge d'un appareil."""
        if not self.token or not self.user_id or not device_mac:
            _LOGGER.error("Token, User ID ou Device MAC manquant pour set_charge_threshold")
            return False
        
        try:
            # Initialiser la session si nécessaire
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Accept": "application/json",
                "Accept-Language": "fr",
                "Authorization": self.token,
                "Content-Type": "application/json",
                "User-Agent": "okhttp/3.14.9"
            }
            
            # Récupérer les paramètres actuels
            current_settings = await self.get_device_settings(device_mac)
            if not current_settings:
                _LOGGER.error(f"❌ Impossible de récupérer les paramètres actuels pour {device_mac}")
                return False
            
            # Mettre à jour le seuil de charge avec tous les paramètres requis
            data = {
                "bleMac": device_mac,
                "bmsEnable": current_settings.get("bmsEnable", True),
                "bmsPower": current_settings.get("bmsPower", 10),  # Seuil de décharge inchangé
                "ctAPower": current_settings.get("ctAPower", 0),
                "ctBPower": current_settings.get("ctBPower", 0),
                "ctCPower": current_settings.get("ctCPower", 0),
                "ctEnable": current_settings.get("ctEnable", 0),
                "ctTotalPower": current_settings.get("ctTotalPower", 0),
                "currencyCode": current_settings.get("currencyCode", "EUR"),
                "deviceControl": current_settings.get("deviceControl", 0),
                "gridCode": current_settings.get("gridCode", 0),
                "gridControl": current_settings.get("gridControl", 0),
                "gridEnable": current_settings.get("gridEnable", 0),
                "gridTime": current_settings.get("gridTime", 0),
                "mode": current_settings.get("mode", 1),
                "otaStatus": current_settings.get("otaStatus", 1),
                "peakShavingDetails": current_settings.get("peakShavingDetails", ["|00:00-23:59|4000|"]),
                "periodDetail": current_settings.get("periodDetail", [
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|3000|", "|22:00-23:59|1000|"],
                    ["|00:00-08:00|1000|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|3000|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"]
                ]),
                "periods": current_settings.get("periods", 0),
                "pfSwitch": current_settings.get("pfSwitch", 0),
                "pfValue": current_settings.get("pfValue", 0),
                "pricePerKwh": current_settings.get("pricePerKwh", 0.3),
                "soc": threshold,  # Seuil de charge
                "timezone": current_settings.get("timezone", 2.0),
                "userId": self.user_id
            }
            
            _LOGGER.info(f"🔧 Modification du seuil de charge à {threshold}% pour {device_mac}...")
            
            async with self.session.post(
                f"{self.base_url}/api/devices/setting/upload",
                json=data,
                headers=headers
            ) as response:
                
                _LOGGER.info(f"📥 Réponse seuil de charge: HTTP {response.status}")
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    if response_data.get("code") == 0:
                        _LOGGER.info(f"✅ Seuil de charge mis à jour à {threshold}% pour {device_mac}")
                        return True
                    else:
                        _LOGGER.error(f"❌ Erreur API seuil de charge: {response_data.get('message')}")
                        return False
                else:
                    response_text = await response.text()
                    _LOGGER.error(f"❌ Erreur HTTP seuil de charge: {response.status}")
                    return False
                    
        except Exception as e:
            _LOGGER.error(f"❌ Erreur modification seuil de charge pour {device_mac}: {e}")
            return False

    async def set_device_config_parameter(self, device_mac: str, parameter_name: str, parameter_value: Any) -> bool:
        """Méthode générique pour mettre à jour un paramètre de configuration d'un appareil."""
        if not self.token or not self.user_id or not device_mac:
            _LOGGER.error("Token, User ID ou Device MAC manquant pour set_device_config_parameter")
            return False
        
        try:
            # Initialiser la session si nécessaire
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Accept": "application/json",
                "Accept-Language": "fr",
                "Authorization": self.token,
                "Content-Type": "application/json",
                "User-Agent": "okhttp/3.14.9"
            }
            
            # Récupérer les paramètres actuels
            current_settings = await self.get_device_settings(device_mac)
            if not current_settings:
                _LOGGER.error(f"❌ Impossible de récupérer les paramètres actuels pour {device_mac}")
                return False
            
            # Créer une copie des paramètres actuels et mettre à jour le paramètre demandé
            data = {
                "bleMac": device_mac,
                "bmsEnable": current_settings.get("bmsEnable", True),
                "bmsPower": current_settings.get("bmsPower", 10),
                "ctAPower": current_settings.get("ctAPower", 0),
                "ctBPower": current_settings.get("ctBPower", 0),
                "ctCPower": current_settings.get("ctCPower", 0),
                "ctEnable": current_settings.get("ctEnable", 0),
                "ctTotalPower": current_settings.get("ctTotalPower", 0),
                "currencyCode": current_settings.get("currencyCode", "EUR"),
                "deviceControl": current_settings.get("deviceControl", 0),
                "gridCode": current_settings.get("gridCode", 0),
                "gridControl": current_settings.get("gridControl", 0),
                "gridEnable": current_settings.get("gridEnable", 0),
                "gridTime": current_settings.get("gridTime", 0),
                "mode": current_settings.get("mode", 1),
                "otaStatus": current_settings.get("otaStatus", 1),
                "peakShavingDetails": current_settings.get("peakShavingDetails", ["|00:00-23:59|4000|"]),
                "periodDetail": current_settings.get("periodDetail", [
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|3000|", "|22:00-23:59|1000|"],
                    ["|00:00-08:00|1000|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|3000|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"]
                ]),
                "periods": current_settings.get("periods", 0),
                "pfSwitch": current_settings.get("pfSwitch", 0),
                "pfValue": current_settings.get("pfValue", 0),
                "pricePerKwh": current_settings.get("pricePerKwh", 0.3),
                "soc": current_settings.get("soc", 10),
                "timezone": current_settings.get("timezone", 2.0),
                "userId": self.user_id
            }
            
            # Mettre à jour le paramètre demandé
            # Convertir les booléens en int pour bmsEnable (0 ou 1)
            if parameter_name == "bmsEnable":
                data[parameter_name] = 1 if parameter_value else 0
            else:
                data[parameter_name] = parameter_value
            
            _LOGGER.info(f"🔧 Modification du paramètre {parameter_name} à {parameter_value} pour {device_mac}...")
            
            async with self.session.post(
                f"{self.base_url}/api/devices/setting/upload",
                json=data,
                headers=headers
            ) as response:
                
                _LOGGER.info(f"📥 Réponse modification paramètre: HTTP {response.status}")
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    if response_data.get("code") == 0:
                        _LOGGER.info(f"✅ Paramètre {parameter_name} mis à jour à {parameter_value} pour {device_mac}")
                        return True
                    else:
                        _LOGGER.error(f"❌ Erreur API modification paramètre: {response_data.get('message')}")
                        return False
                else:
                    response_text = await response.text()
                    _LOGGER.error(f"❌ Erreur HTTP modification paramètre: {response.status}")
                    return False
                    
        except Exception as e:
            _LOGGER.error(f"❌ Erreur modification paramètre {parameter_name} pour {device_mac}: {e}")
            return False
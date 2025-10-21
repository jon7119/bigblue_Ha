"""Coordinateur pour l'intégration Big Blue."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, API_BASE_URL, API_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class BigBlueDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinateur pour les données Big Blue."""
    
    def __init__(self, hass: HomeAssistant, api_client) -> None:
        """Initialise le coordinateur."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.api_client = api_client
        self.devices = []  # Liste des appareils trouvés
    
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
                
                # Récupération des données de cet appareil
                data = await self.api_client.get_device_data_for_mac(device_mac)
                
                if data:
                    # Formatage des données pour cet appareil
                    formatted_data = {
                        "soc": data.get("totalSoc", 0) / 10,  # Conversion en %
                        "soh": data.get("totalSoh", 0) / 10,  # Conversion en %
                        "voltage": data.get("totalVoltage", 0) / 10,  # Conversion en V
                        "current": data.get("totalCurrent", 0),
                        "power": data.get("totalPower", 0) / 10,  # Conversion en W
                        "remaining_capacity": data.get("totalRemainingCapacity", 0) / 1000,  # Conversion en kWh
                        "rated_capacity": data.get("TotalRatedCapacity", 0) / 1000,  # Conversion en kWh
                        "pv1_voltage": data.get("pv1V", 0) / 10,  # Conversion en V
                        "pv1_current": data.get("pv1A", 0),
                        "pv1_power": data.get("pv1W", 0) / 10,  # Conversion en W
                        "pv2_voltage": data.get("pv2V", 0) / 10,  # Conversion en V
                        "pv2_current": data.get("pv2A", 0),
                        "pv2_power": data.get("pv2W", 0) / 10,  # Conversion en W
                        "pv_total_power": data.get("pvTotalPower", 0) / 10,  # Conversion en W
                        "daily_generation": data.get("dailyGeneration", 0) / 1000,  # Conversion en kWh
                        "total_generation": data.get("totalGeneration", 0) / 1000,  # Conversion en kWh
                        "daily_output_energy": data.get("dailyOutputEnergy", 0) / 1000,  # Conversion en kWh
                        "total_output_energy": data.get("totalOutputEnergy", 0) / 1000,  # Conversion en kWh
                        "max_temperature": data.get("maxTemperature", 0) / 10,  # Conversion en °C
                        "min_temperature": data.get("minTemperature", 0) / 10,  # Conversion en °C
                        "daily_co2_savings": data.get("dailyCo2Savings", 0),
                        "daily_runtime": data.get("dailyRuntime", 0) / 3600,  # Conversion en heures
                        "total_runtime": data.get("totalRuntime", 0),
                        "battery_count": data.get("batteryCount", 0),
                        "status": data.get("status", 0),
                        "current_mode": await self.api_client.get_current_mode(device_mac),  # Récupération du mode actuel
                        "discharge_threshold": await self.api_client.get_discharge_threshold(device_mac),  # Récupération du seuil de décharge
                        "last_update": data.get("last_update"),
                        "device_mac": device_mac,
                        "device_name": device_name,
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
            
            # Données pour changer le mode
            data = {
                "bleMac": device_mac,
                "bmsEnable": True,
                "bmsPower": 12,
                "ctAPower": 0,
                "ctBPower": 0,
                "ctCPower": 0,
                "ctEnable": 0,
                "ctTotalPower": 0,
                "currencyCode": "EUR",
                "deviceControl": 0,
                "gridCode": 0,
                "gridControl": 0,
                "gridEnable": 0,
                "gridTime": 0,
                "mode": mode,
                "otaStatus": 1,
                "peakShavingDetails": ["|00:00-23:59|4000|"],
                "periodDetail": [
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|3000|", "|22:00-23:59|1000|"],
                    ["|00:00-08:00|1000|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|3000|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"],
                    ["|00:00-08:00|1500|", "|08:00-18:00|0|", "|18:00-22:00|2000|", "|22:00-23:59|1500|"]
                ],
                "periods": 0,
                "pfSwitch": 0,
                "pfValue": 0,
                "pricePerKwh": 0.3,
                "soc": 10,
                "timezone": 2.0,
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

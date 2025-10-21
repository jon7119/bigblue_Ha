"""Config flow for Big Blue integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("email"): str,
        vol.Required("password"): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Big Blue."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            # Test connection to Powafree API
            await self._test_connection(user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        if not errors:
            return self.async_create_entry(
                title=f"Big Blue {user_input['email']}", data=user_input
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def _test_connection(self, user_input: dict[str, Any]) -> None:
        """Test connection to Powafree API."""
        from .coordinator import BigBlueAPIClient
        
        async with BigBlueAPIClient(
            user_input["email"], 
            user_input["password"]
        ) as api_client:
            if not await api_client.authenticate():
                raise CannotConnect("Authentication failed")
            
            devices = await api_client.get_devices()
            if not devices:
                raise CannotConnect("No devices found")


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

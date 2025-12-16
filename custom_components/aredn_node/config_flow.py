"""Adds config flow for Blueprint."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from slugify import slugify

from .api import (
    ArednNodeApiClient,
    ArednNodeApiClientAuthenticationError,
    ArednNodeApiClientCommunicationError,
    ArednNodeApiClientError,
)
from .const import DOMAIN, LOGGER


class ArednNodeFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for AREDN Node."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    host=user_input[CONF_HOST],
                )
            except ArednNodeApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "cannot_connect"
            except ArednNodeApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "cannot_connect"
            except ArednNodeApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(slugify(user_input[CONF_HOST]))
                self._abort_if_unique_id_configured()
                api_data = await self._get_data(user_input[CONF_HOST])
                return self.async_create_entry(
                    title=api_data.get("node", user_input[CONF_HOST]),
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=(user_input or {}).get(CONF_HOST, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def _test_credentials(self, host: str) -> None:
        """Validate credentials."""
        await self._get_data(host)

    async def _get_data(self, host: str) -> dict:
        """Get data from the API."""
        client = ArednNodeApiClient(
            host=host,
            session=async_create_clientsession(self.hass),
        )
        return await client.async_get_data()

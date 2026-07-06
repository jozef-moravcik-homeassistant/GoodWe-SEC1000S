from __future__ import annotations
"""Integration for Goodwe SEC1000"""
"""Author: Jozef Moravcik"""
"""email: jozef.moravcik@moravcik.eu"""

""" sensor.py """

"""Config flow for Goodwe SEC1000 integration"""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    EntitySelector,
    EntitySelectorConfig,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.storage import Store

from .goodwe_sec1000 import Goodwe_SEC1000_Instance
from .const import *

_LOGGER = logging.getLogger(__name__)

class GoodweSEC1000ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
#    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize the config flow."""
        self._data = {}

    # An initialization method that redirects the config flow to the first configuration step
    # This method must be here, it must not be deleted !!!
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        return await self.async_step_connection(user_input)

    async def async_step_connection(self, user_input=None):
        """Handle the step 1. - Connection Parameters."""
        errors = {}

        if user_input is not None:
            try:
                host = user_input[CONF_HOST]
                # Test connection to Goodwe SEC1000
                instance = Goodwe_SEC1000_Instance(host)
                
                # Test connection by reading data
                await self.hass.async_add_executor_job(instance.sec1000_get_telemetry_data)
                
                # Save user input to proceed to next step
                self._data.update(user_input)

                # Proceed to export settings step
                return await self.async_step_export_settings()
                
            except Exception as ex:
                _LOGGER.error("Failed to connect to Goodwe SEC1000: %s", ex)
                errors["base"] = "cannot_connect"

        # Display a form for connection settings
                
        # Zistiť počet existujúcich zariadení a nastaviť default názov
        existing_entries = self.hass.config_entries.async_entries(DOMAIN)
        device_number = len(existing_entries) + 1
        default_device_name = f"Device {device_number}"

        # Use default values for new installation
        host = DEFAULT_HOST
        scan_interval = DEFAULT_SCAN_INTERVAL   
        
        connection_schema = vol.Schema(
            {
                vol.Required(
                    CONF_DEVICE_NAME,
                    default=default_device_name,
                ): cv.string,
                vol.Required(
                    CONF_INCLUDE_DEVICE_NAME_IN_ENTITY,
                    default=DEFAULT_INCLUDE_DEVICE_NAME_IN_ENTITY,
                ): cv.boolean,
                vol.Required(
                    CONF_HOST,
                    default=host
                ): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=scan_interval
                ): int,
            }
        )

        return self.async_show_form(
            step_id="connection",
            data_schema=connection_schema,
            errors=errors,
            last_step=False,
        )

    async def async_step_export_settings(self, user_input=None):
        """Handle the export settings step."""
        errors = {}

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_control_settings()

        export_schema = vol.Schema(
            {
                vol.Optional(CONF_MIN_EXPORT_LIMIT, default=DEFAULT_MIN_EXPORT_LIMIT): 
                    vol.All(vol.Coerce(float), vol.Range(min=-100.00, max=100.00)),
                vol.Optional(CONF_MAX_EXPORT_LIMIT, default=DEFAULT_MAX_EXPORT_LIMIT): 
                    vol.All(vol.Coerce(float), vol.Range(min=-100.00, max=100.00)),
                vol.Optional(CONF_TOTAL_CAPACITY, default=DEFAULT_TOTAL_CAPACITY): 
                    vol.All(vol.Coerce(float), vol.Range(min=0.00, max=100.00)),
            }
        )

        return self.async_show_form(
            step_id="export_settings",
            data_schema=export_schema,
            errors=errors,
            last_step=False,
        )

    async def async_step_control_settings(self, user_input=None):
        """Handle the control settings step."""
        errors = {}

        if user_input is not None:
            # Convert string back to int before saving
            if CONF_EXPORT_LIMIT_CONTROL_MODE in user_input:
                user_input[CONF_EXPORT_LIMIT_CONTROL_MODE] = int(user_input[CONF_EXPORT_LIMIT_CONTROL_MODE])
                
            # Merge data from all steps
            self._data.update(user_input)
            
            # Použiť názov zariadenia v unique_id
            device_name = self._data.get(CONF_DEVICE_NAME, DEFAULT_DEVICE_NAME)
            unique_id = f"{DOMAIN}_{device_name.lower().replace(' ', '_')}"
            
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            
            conf_host = self._data.get(CONF_HOST, DEFAULT_HOST)
            
            return self.async_create_entry(
                title=f"GoodWe SEC1000 - {device_name} - host:{conf_host}",
                data=self._data,
            )

        control_schema = vol.Schema(
            {
                vol.Optional(CONF_EXPORT_LIMIT_CONTROL_MODE, default=str(DEFAULT_EXPORT_LIMIT_CONTROL_MODE)): 
                    SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                str(EXPORT_LIMIT_CONTROL_MODE_DISABLED),
                                str(EXPORT_LIMIT_CONTROL_MODE_VALUE),
                                str(EXPORT_LIMIT_CONTROL_MODE_DRED),
                                str(EXPORT_LIMIT_CONTROL_MODE_RCR)
                            ],
#                            mode=SelectSelectorMode.DROPDOWN,
                            mode=SelectSelectorMode.LIST,
                            translation_key="export_limit_control_mode"
                        )
                    ),
                vol.Optional(CONF_SCAN_THREE_PHASES, default=DEFAULT_SCAN_THREE_PHASES): bool,
            }
        )

        return self.async_show_form(
            step_id="control_settings",
            data_schema=control_schema,
            errors=errors,
        )
        
    async def async_step_import(self, import_config):
        """Import config from configuration.yaml."""
        # Add default values for any missing export settings
        if CONF_MIN_EXPORT_LIMIT not in import_config:
            import_config[CONF_MIN_EXPORT_LIMIT] = DEFAULT_MIN_EXPORT_LIMIT
        if CONF_MAX_EXPORT_LIMIT not in import_config:
            import_config[CONF_MAX_EXPORT_LIMIT] = DEFAULT_MAX_EXPORT_LIMIT
        if CONF_TOTAL_CAPACITY not in import_config:
            import_config[CONF_TOTAL_CAPACITY] = DEFAULT_TOTAL_CAPACITY
        if CONF_EXPORT_LIMIT_CONTROL_MODE not in import_config:
            import_config[CONF_EXPORT_LIMIT_CONTROL_MODE] = DEFAULT_EXPORT_LIMIT_CONTROL_MODE
        if CONF_SCAN_THREE_PHASES not in import_config:
            import_config[CONF_SCAN_THREE_PHASES] = DEFAULT_SCAN_THREE_PHASES
            
        return await self.async_step_user(import_config)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return GoodweSEC1000OptionsFlowHandler(config_entry)

class GoodweSEC1000OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Goodwe SEC1000 options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        super().__init__()
        self._config_entry = config_entry
        self._data = {}
        
    # An initialization method that redirects the config flow to the first configuration step
    # This method must be here, it must not be deleted !!!
    async def async_step_init(self, user_input=None):
        """Handle the initial step."""
        return await self.async_step_connection(user_input)

    async def async_step_connection(self, user_input=None):
        """Manage the options - connection settings."""
        if user_input is not None:
            # Zachovaj device_name z existujúcej konfigurácie
            current_device_name = self.config_entry.options.get(
                CONF_DEVICE_NAME,
                self.config_entry.data.get(CONF_DEVICE_NAME, DEFAULT_DEVICE_NAME)
            )
            user_input[CONF_DEVICE_NAME] = current_device_name
            
            # Save data from previous step
            self._data.update(user_input)
            # Go to the next step
            return await self.async_step_export_settings()

        host = self.config_entry.options.get(
            CONF_HOST,
            self._config_entry.data.get(CONF_HOST, DEFAULT_HOST)
        )
        scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )

        # Získať aktuálne hodnoty z options (ak existujú) alebo z data
        current_device_name = self.config_entry.options.get(
            CONF_DEVICE_NAME,
            self.config_entry.data.get(CONF_DEVICE_NAME, DEFAULT_DEVICE_NAME)
        )
        current_include_device_name = self.config_entry.options.get(
            CONF_INCLUDE_DEVICE_NAME_IN_ENTITY,
            self.config_entry.data.get(CONF_INCLUDE_DEVICE_NAME_IN_ENTITY, DEFAULT_INCLUDE_DEVICE_NAME_IN_ENTITY)
        )        

        return self.async_show_form(
            step_id="connection",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_INCLUDE_DEVICE_NAME_IN_ENTITY,
                        default=current_include_device_name,
                    ): cv.boolean,
                    vol.Required(
                        CONF_HOST, 
                        default=host
                    ): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=scan_interval
                    ): int,
                }
            ),
            last_step=False,
        )

    async def async_step_export_settings(self, user_input=None):
        """Manage the export settings options."""
        if user_input is not None:
            # Store export settings and proceed to control settings
            self._data.update(user_input)
            return await self.async_step_control_settings()

        # Čítaj min/max zo storage (kde ich ukladajú service set_min/max_export_limit),
        # s fallback na options → data → default
        _storage = Store(self.hass, STORAGE_VERSION, STORAGE_KEY)
        _stored = await _storage.async_load() or {}
        min_export_limit = _stored.get(
            "min_export_limit",
            self.config_entry.options.get(CONF_MIN_EXPORT_LIMIT,
                self._config_entry.data.get(CONF_MIN_EXPORT_LIMIT, DEFAULT_MIN_EXPORT_LIMIT))
        )
        max_export_limit = _stored.get(
            "max_export_limit",
            self.config_entry.options.get(CONF_MAX_EXPORT_LIMIT,
                self._config_entry.data.get(CONF_MAX_EXPORT_LIMIT, DEFAULT_MAX_EXPORT_LIMIT))
        )
        total_capacity = self.config_entry.options.get(
            CONF_TOTAL_CAPACITY,
            self._config_entry.data.get(CONF_TOTAL_CAPACITY, DEFAULT_TOTAL_CAPACITY)
        )
        return self.async_show_form(
            step_id="export_settings",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_MIN_EXPORT_LIMIT, default=min_export_limit):
                        vol.All(vol.Coerce(float), vol.Range(min=-100.00, max=100.00)),
                    vol.Optional(CONF_MAX_EXPORT_LIMIT, default=max_export_limit):
                        vol.All(vol.Coerce(float), vol.Range(min=-100.00, max=100.00)),
                    vol.Optional(CONF_TOTAL_CAPACITY, default=total_capacity):
                        vol.All(vol.Coerce(float), vol.Range(min=0.00, max=100.00)),
                }
            ),
            last_step=False,
        )

    async def async_step_control_settings(self, user_input=None):
        """Manage the control settings options."""
        if user_input is not None:
            # Convert string back to int before saving
            if CONF_EXPORT_LIMIT_CONTROL_MODE in user_input:
                user_input[CONF_EXPORT_LIMIT_CONTROL_MODE] = int(user_input[CONF_EXPORT_LIMIT_CONTROL_MODE])
                
            # Skombinuj dáta zo všetkých krokov
            if not hasattr(self, '_data'):
                self._data = {}
            self._data.update(user_input)
            return self.async_create_entry(title="", data=self._data)                

        export_limit_control_mode = self.config_entry.options.get(
            CONF_EXPORT_LIMIT_CONTROL_MODE,
            self._config_entry.data.get(CONF_EXPORT_LIMIT_CONTROL_MODE, DEFAULT_EXPORT_LIMIT_CONTROL_MODE)
        )
        scan_three_phases = self.config_entry.options.get(
            CONF_SCAN_THREE_PHASES,
            self._config_entry.data.get(CONF_SCAN_THREE_PHASES, DEFAULT_SCAN_THREE_PHASES)
        )

        return self.async_show_form(
            step_id="control_settings",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_EXPORT_LIMIT_CONTROL_MODE, default=str(export_limit_control_mode)): 
                        SelectSelector(
                            SelectSelectorConfig(
                                options=[
                                    str(EXPORT_LIMIT_CONTROL_MODE_DISABLED),
                                    str(EXPORT_LIMIT_CONTROL_MODE_VALUE),
                                    str(EXPORT_LIMIT_CONTROL_MODE_DRED),
                                    str(EXPORT_LIMIT_CONTROL_MODE_RCR)
                                ],
#                                mode=SelectSelectorMode.DROPDOWN,
                                mode=SelectSelectorMode.LIST,
                                translation_key="export_limit_control_mode"
                            )
                        ),
                    vol.Optional(CONF_SCAN_THREE_PHASES, default=scan_three_phases): bool,
                }
            ),
        )
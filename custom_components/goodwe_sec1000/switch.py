from __future__ import annotations
"""Integration for Goodwe SEC1000"""
"""Author: Jozef Moravcik"""
"""email: jozef.moravcik@moravcik.eu"""

""" switch.py """

"""Switch platform for Goodwe SEC1000."""
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    DOMAIN,
    VERSION,
    MANUFACTURER,
    MODEL,
    ENTITY_PREFIX,
    SERVICE_EXPORT_ENABLE,
    SERVICE_EXPORT_DISABLE,
    ENTITY_SWITCH_export_to_grid,
    ENTITY_SENSOR_export_state,
    sanitize_device_name,
)

_LOGGER = logging.getLogger(__name__)

async def _load_translations(hass: HomeAssistant) -> dict:
    """Load translations for the current language."""
    import json
    import os
    
    def _load_file():
        try:
            language = hass.config.language if hass else "en"
            
            # Skúsiť načítať translations súbor pre daný jazyk
            translations_path = os.path.join(os.path.dirname(__file__), "translations", f"{language}.json")
            
            # Ak neexistuje pre daný jazyk, použiť strings.json ako fallback
            if not os.path.exists(translations_path):
                translations_path = os.path.join(os.path.dirname(__file__), "strings.json")
            
            if os.path.exists(translations_path):
                with open(translations_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    return await hass.async_add_executor_job(_load_file)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""
    instance = hass.data[DOMAIN][entry.entry_id]["instance"]
    
    # Načítať translations asynchrónne
    translations = await _load_translations(hass)
    
    entities = [
        ExportSwitch(
            instance,
            entry_id=entry.entry_id,
            translations=translations,
        ),
    ]

    async_add_entities(entities)


class ExportSwitch(SwitchEntity):
    """Representation of Export to Grid switch."""

    def __init__(
        self,
        instance,
        entry_id: str,
        translations: dict = None,
    ) -> None:
        """Initialize the switch."""
        self._instance = instance
        self._entry_id = entry_id
        
        device_name_sanitized = sanitize_device_name(instance.settings.device_name)
        
        self._attr_unique_id = f"{ENTITY_PREFIX}_{entry_id}_{ENTITY_SWITCH_export_to_grid}"
        self._attr_has_entity_name = instance.settings.include_device_name_in_entity
        self._attr_translation_key = ENTITY_SWITCH_export_to_grid
        
        # Ak has_entity_name = False, nastaviť _attr_name z preloaded translations
        if not instance.settings.include_device_name_in_entity and translations:
            entity_trans = translations.get("entity", {}).get("switch", {}).get(ENTITY_SWITCH_export_to_grid, {})
            translated_name = entity_trans.get("name")
            if translated_name:
                self._attr_name = translated_name
            else:
                self._attr_name = "Export to Grid"
        
        self.entity_id = f"switch.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SWITCH_export_to_grid}"
        
        # Načítať počiatočný stav zo senzora export_state
        self._attr_is_on = getattr(instance.settings, ENTITY_SENSOR_export_state, False)
        self._attr_available = instance.settings.device_initialized  # Available only after device is initialized
        self._update_icon()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._instance.settings.device_display_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=VERSION,
            configuration_url="https://github.com/jozef-moravcik-homeassistant/goodwe-sec1000s",
        )

    def _update_icon(self) -> None:
        """Update icon based on switch state."""
        self._attr_icon = "mdi:transmission-tower-export" if self._attr_is_on else "mdi:transmission-tower-off"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        
        # Subscribe to updates
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_feedback_update_{self._entry_id}",
                self._handle_feedback_update,
            )
        )
        
        # Initial update
        self._handle_feedback_update()

    @callback
    def _handle_feedback_update(self) -> None:
        """Handle feedback update and sync switch state with export_state sensor."""
        try:
            # Check if device is initialized
            if not self._instance.settings.device_initialized:
                self._attr_available = False
                self.async_write_ha_state()
                return
            
            # Device is initialized, make switch available
            self._attr_available = True
            
            # Načítať export_state zo settings
            export_state = getattr(self._instance.settings, ENTITY_SENSOR_export_state, None)
            
            if export_state is not None:
                # Konvertovať na boolean
                if isinstance(export_state, str):
                    self._attr_is_on = export_state.lower() == "on"
                else:
                    self._attr_is_on = bool(export_state)
                
                self._update_icon()
            
        except AttributeError:
            pass
        
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on - enable export."""
        try:
            await self.hass.services.async_call(
                DOMAIN,
                SERVICE_EXPORT_ENABLE,
                {},
                blocking=True,
            )
            _LOGGER.info(f"Switch {self.entity_id} turned on, calling service {SERVICE_EXPORT_ENABLE}")
            
            # Update state immediately for responsiveness
            self._attr_is_on = True
            self._update_icon()
            self.async_write_ha_state()
            
        except Exception as e:
            _LOGGER.error(f"Error calling service {SERVICE_EXPORT_ENABLE}: {e}")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off - disable export."""
        try:
            await self.hass.services.async_call(
                DOMAIN,
                SERVICE_EXPORT_DISABLE,
                {},
                blocking=True,
            )
            _LOGGER.info(f"Switch {self.entity_id} turned off, calling service {SERVICE_EXPORT_DISABLE}")
            
            # Update state immediately for responsiveness
            self._attr_is_on = False
            self._update_icon()
            self.async_write_ha_state()
            
        except Exception as e:
            _LOGGER.error(f"Error calling service {SERVICE_EXPORT_DISABLE}: {e}")

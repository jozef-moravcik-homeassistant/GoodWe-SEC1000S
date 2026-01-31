from __future__ import annotations
"""Integration for Goodwe SEC1000"""
"""Author: Jozef Moravcik"""
"""email: jozef.moravcik@moravcik.eu"""

""" button.py """

"""Button platform for Goodwe SEC1000"""
import logging
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.entity import EntityCategory, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import (
    DOMAIN,
    VERSION,
    MANUFACTURER,
    MODEL,
    ENTITY_PREFIX,
    SERVICE_RESET_EXPORT_WATCHDOG,
    ENTITY_BUTTON_reset_export_watchdog,
    ENTITY_SENSOR_reset_export_watchdog_feedback,
    SERVICE_SET_DATETIME,
    ENTITY_BUTTON_set_datetime,
    ENTITY_SENSOR_set_datetime_feedback,
    SERVICE_EXPORT_ENABLE,
    ENTITY_BUTTON_export_enable,
    ENTITY_SENSOR_export_enable_feedback,
    SERVICE_EXPORT_DISABLE,
    ENTITY_BUTTON_export_disable,
    ENTITY_SENSOR_export_disable_feedback,
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
    """Set up button entities."""
    instance = hass.data[DOMAIN][entry.entry_id]["instance"]

    # Načítať translations asynchrónne
    translations = await _load_translations(hass)

    entities = [
        # Button - Enable Export (1. pozícia)
        ButtonEntityDefinition(
            instance,
            entry_id=entry.entry_id,
            entity_id=ENTITY_BUTTON_export_enable,
            name="Enable Export",
            translations=translations,
            service_name=SERVICE_EXPORT_ENABLE,
            feedback_sensor_id=ENTITY_SENSOR_export_enable_feedback,
            icon_ready="mdi:transmission-tower-export",
            icon_processing="mdi:progress-upload",
            icon_error="mdi:alert",
            enabled_by_default=True,
        ),
        
        # Button - Disable Export (2. pozícia)
        ButtonEntityDefinition(
            instance,
            entry_id=entry.entry_id,
            entity_id=ENTITY_BUTTON_export_disable,
            name="Disable Export",
            translations=translations,
            service_name=SERVICE_EXPORT_DISABLE,
            feedback_sensor_id=ENTITY_SENSOR_export_disable_feedback,
            icon_ready="mdi:transmission-tower-off",
            icon_processing="mdi:progress-upload",
            icon_error="mdi:alert",
            enabled_by_default=True,
        ),
        
        # Button - Reset Export Watchdog (3. pozícia)
        ButtonEntityDefinition(
            instance,
            entry_id=entry.entry_id,
            entity_id=ENTITY_BUTTON_reset_export_watchdog,
            name="Reset Export Watchdog",
            translations=translations,
            service_name=SERVICE_RESET_EXPORT_WATCHDOG,
            feedback_sensor_id=ENTITY_SENSOR_reset_export_watchdog_feedback,
            icon_ready="mdi:update",
            icon_processing="mdi:progress-upload",
            icon_error="mdi:alert",
            enabled_by_default=True,
        ),
        
        # Button - Set Date Time (4. pozícia)
        ButtonEntityDefinition(
            instance,
            entry_id=entry.entry_id,
            entity_id=ENTITY_BUTTON_set_datetime,
            name="Set Date Time",
            translations=translations,
            service_name=SERVICE_SET_DATETIME,
            feedback_sensor_id=ENTITY_SENSOR_set_datetime_feedback,
            icon_ready="mdi:clock-digital",
            icon_processing="mdi:progress-upload",
            icon_error="mdi:alert",
            enabled_by_default=True,
        ),
    ]

    async_add_entities(entities)


class ButtonEntityDefinition(ButtonEntity):
    """Representation of a Goodwe SEC1000 Button."""

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._instance.settings.device_display_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=VERSION,
            configuration_url="https://github.com/jozef-moravcik-homeassistant/goodwe-sec1000s",
        )

    def __init__(
        self,
        instance,
        entry_id: str,
        entity_id: str,
        name: str,
        service_name: str,
        feedback_sensor_id: str,
        translations: dict = None,
        icon_ready: str = "mdi:button-pointer",
        icon_processing: str = "mdi:progress-upload",
        icon_error: str = "mdi:alert",
        enabled_by_default: bool = True,
        device_class: ButtonDeviceClass | None = None,
        entity_category: EntityCategory | None = None,
    ) -> None:
        """Initialize the button."""
        self._instance = instance
        self._entry_id = entry_id
        self._service_name = service_name
        self._feedback_sensor_id = feedback_sensor_id
        self._icon_ready = icon_ready
        self._icon_processing = icon_processing
        self._icon_error = icon_error
        
        # Sanitize device name for entity ID
        from .const import sanitize_device_name
        device_name_sanitized = sanitize_device_name(instance.settings.device_name)
        
        self._attr_unique_id = f"{ENTITY_PREFIX}_{entry_id}_{entity_id}"
        self._attr_has_entity_name = instance.settings.include_device_name_in_entity
        self._attr_translation_key = entity_id
        
        # Ak has_entity_name = False, nastaviť _attr_name z preloaded translations
        if not instance.settings.include_device_name_in_entity and translations:
            entity_trans = translations.get("entity", {}).get("button", {}).get(entity_id, {})
            translated_name = entity_trans.get("name")
            if translated_name:
                self._attr_name = translated_name
            else:
                self._attr_name = name
        
        self.entity_id = f"button.{ENTITY_PREFIX}_{device_name_sanitized}_{entity_id}"
        self._entity_id = entity_id
        self._attr_icon = icon_ready
        self._attr_available = instance.settings.device_initialized  # Available only after device is initialized
        self._attr_entity_registry_enabled_default = enabled_by_default
        self._attr_entity_registry_visible_default = enabled_by_default
        
        # Custom attributes pre stav
        self._attr_extra_state_attributes = {
            "button_state": "ready",
            "feedback_value": None,
        }

        if device_class is not None:
            self._attr_device_class = device_class
        if entity_category is not None:
            self._attr_entity_category = entity_category

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
        """Handle feedback update and update button state."""
        try:
            # Check if device is initialized
            if not self._instance.settings.device_initialized:
                self._attr_available = False
                self._attr_extra_state_attributes["button_state"] = "initializing"
                self.async_write_ha_state()
                return
            
            # Read feedback value from instance settings
            feedback_value = getattr(self._instance.settings, self._feedback_sensor_id, None)
            
            if feedback_value is not None:
                self._attr_extra_state_attributes["feedback_value"] = feedback_value
                
                # Determine button state based on feedback value
                if feedback_value > 1:
                    # Error state
                    self._attr_extra_state_attributes["button_state"] = "error"
                    self._attr_icon = self._icon_error
                    self._attr_available = True  # Button is available but shows error
                elif feedback_value == 0:
                    # Processing state
                    self._attr_extra_state_attributes["button_state"] = "processing"
                    self._attr_icon = self._icon_processing
                    self._attr_available = False  # Button is disabled during processing
                else:  # feedback_value == 1
                    # Ready state
                    self._attr_extra_state_attributes["button_state"] = "ready"
                    self._attr_icon = self._icon_ready
                    self._attr_available = True
            
        except AttributeError:
            pass
        
        self.async_write_ha_state()

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # Call the service
            await self.hass.services.async_call(
                DOMAIN,
                self._service_name,
                {},
                blocking=False,
            )
            _LOGGER.info(f"Button {self.entity_id} pressed, calling service {self._service_name}")
        except Exception as e:
            _LOGGER.error(f"Error calling service {self._service_name}: {e}")

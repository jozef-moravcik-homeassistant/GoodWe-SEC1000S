from __future__ import annotations
"""Integration for Goodwe SEC1000"""
"""Author: Jozef Moravcik"""
"""email: jozef.moravcik@moravcik.eu"""

""" number.py """

"""Number platform for Goodwe SEC1000"""
import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberDeviceClass, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.entity import EntityCategory, DeviceInfo
from homeassistant.const import UnitOfPower

from .const import (
    DOMAIN,
    VERSION,
    MANUFACTURER,
    MODEL,
    NAME,
    ENTITY_PREFIX,
    SERVICE_SET_EXPORT_LIMIT,
    ENTITY_NUMBER_export_limit,
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
    """Set up number entities."""
    instance = hass.data[DOMAIN][entry.entry_id]["instance"]
    
    # Načítať translations asynchrónne
    translations = await _load_translations(hass)
    
    entities = [
        # Number - Export Limit Control
        NumberEntityDefinition(
            instance,
            entry_id=entry.entry_id,
            entity_id=ENTITY_NUMBER_export_limit,
            name="Export Limit",
            translations=translations,
            min_value=-100.0,
            max_value=100.0,
            step=0.1,
            icon="mdi:transmission-tower-export",
            enabled_by_default=True,
        ),
    ]

    async_add_entities(entities)


class NumberEntityDefinition(NumberEntity):
    """Representation of a Goodwe SEC1000 Number."""

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
        min_value: float,
        max_value: float,
        step: float,
        translations: dict = None,
        icon: str = "mdi:counter",
        enabled_by_default: bool = True,
        device_class: NumberDeviceClass | None = None,
        entity_category: EntityCategory | None = None,
    ) -> None:
        """Initialize the number entity."""
        self._instance = instance
        self._entry_id = entry_id
        
        # Sanitize device name for entity ID
        from .const import sanitize_device_name
        device_name_sanitized = sanitize_device_name(instance.settings.device_name)
        
        self._attr_unique_id = f"{ENTITY_PREFIX}_{entry_id}_{entity_id}"
        self._attr_has_entity_name = instance.settings.include_device_name_in_entity
        self._attr_translation_key = entity_id
        
        # Ak has_entity_name = False, nastaviť _attr_name z preloaded translations
        if not instance.settings.include_device_name_in_entity and translations:
            entity_trans = translations.get("entity", {}).get("number", {}).get(entity_id, {})
            translated_name = entity_trans.get("name")
            if translated_name:
                self._attr_name = translated_name
            else:
                self._attr_name = name
        
        self.entity_id = f"number.{ENTITY_PREFIX}_{device_name_sanitized}_{entity_id}"
        self._entity_id = entity_id
        
        # Number configuration
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_mode = NumberMode.BOX  # Show as input box, not slider
        self._attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
        
        # Initialize value from instance.settings.export_limit_desired (požadovaný limit nastavený používateľom)
        try:
            self._attr_native_value = float(getattr(instance.settings, 'export_limit_desired', min_value))
        except (ValueError, TypeError):
            self._attr_native_value = min_value
        
        self._attr_icon = icon
        self._attr_available = True
        self._attr_entity_registry_enabled_default = enabled_by_default
        self._attr_entity_registry_visible_default = enabled_by_default

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
        """Handle feedback update and sync number value with instance.settings.export_limit_desired."""
        try:
            # Read export limit desired from instance settings (požadovaný limit nastavený používateľom)
            # NIE export_limit, lebo ten sa mení pri čítaní zo zariadenia
            export_limit_desired = getattr(self._instance.settings, 'export_limit_desired', None)
            
            if export_limit_desired is not None:
                try:
                    new_value = float(export_limit_desired)
                    # Only update if value is within valid range
                    if self._attr_native_min_value <= new_value <= self._attr_native_max_value:
                        self._attr_native_value = new_value
                except (ValueError, TypeError):
                    pass
            
        except AttributeError:
            pass
        
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set new value - call set_export_limit service."""
        try:
            # Call the set export limit service
            await self.hass.services.async_call(
                DOMAIN,
                SERVICE_SET_EXPORT_LIMIT,
                {"limit": value},
                blocking=True,
            )
            _LOGGER.info(f"Number {self.entity_id} set to {value}, calling service {SERVICE_SET_EXPORT_LIMIT}")

            # Persist desired value so the number doesn't reset on feedback updates
            self._instance.settings.export_limit_desired = value

            # Update value immediately for responsiveness
            self._attr_native_value = value
            self.async_write_ha_state()
            
        except Exception as e:
            _LOGGER.error(f"Error calling service {SERVICE_SET_EXPORT_LIMIT}: {e}")

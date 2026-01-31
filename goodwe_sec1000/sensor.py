from __future__ import annotations
"""Integration for Goodwe SEC1000"""
"""Author: Jozef Moravcik"""
"""email: jozef.moravcik@moravcik.eu"""

""" sensor.py """

"""Sensor platform for Goodwe SEC1000"""
import logging
from datetime import timedelta
import asyncio

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.entity import EntityCategory, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from homeassistant.const import (
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    UnitOfPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
)

from .const import (
    DOMAIN,
    VERSION,
    MANUFACTURER,
    MODEL,
    NAME,
    ENTITY_PREFIX,
    DEFAULT_HOST,
    DEFAULT_SCAN_INTERVAL,
    ENTITY_SENSOR_v1,
    ENTITY_SENSOR_v2,
    ENTITY_SENSOR_v3,
    ENTITY_SENSOR_i1,
    ENTITY_SENSOR_i2,
    ENTITY_SENSOR_i3,
    ENTITY_SENSOR_p1,
    ENTITY_SENSOR_p2,
    ENTITY_SENSOR_p3,
    ENTITY_SENSOR_meters_power,
    ENTITY_SENSOR_inverters_power,
    ENTITY_SENSOR_load_power,
    ENTITY_SENSOR_export_limit,
    ENTITY_SENSOR_export_state,
    ENTITY_SENSOR_modul_started,
    ENTITY_SENSOR_export_disable_feedback,
    ENTITY_SENSOR_export_enable_feedback,
    ENTITY_SENSOR_get_export_limit_feedback,
    ENTITY_SENSOR_set_export_limit_feedback,
    ENTITY_SENSOR_set_datetime_feedback,
    ENTITY_SENSOR_get_telemetry_data_feedback,
    ENTITY_SENSOR_reset_export_watchdog_feedback,
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
    """Set up sensor entities."""
    instance = hass.data[DOMAIN][entry.entry_id]["instance"]
    
    # Načítať translations asynchrónne
    translations = await _load_translations(hass)
    
    entities = [

    # Sensor - Voltage on L1
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_v1, 
            name = "Voltage L1",
            translations = translations, 
            icon = "mdi:sine-wave",
            default_value = "0",
            enabled_by_default = True,
            device_class = SensorDeviceClass.VOLTAGE,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = UnitOfElectricPotential.VOLT,
            suggested_display_precision = 1,
        ),

    # Sensor - Voltage on L2
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_v2, 
            name = "Voltage L2",
            translations = translations, 
            icon = "mdi:sine-wave",
            default_value = "0",
            enabled_by_default = True,
            device_class = SensorDeviceClass.VOLTAGE,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = UnitOfElectricPotential.VOLT,
            suggested_display_precision = 1,
        ),

    # Sensor - Voltage on L3
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_v3, 
            name = "Voltage L3",
            translations = translations, 
            icon = "mdi:sine-wave",
            default_value = "0",
            enabled_by_default = True,
            device_class = SensorDeviceClass.VOLTAGE,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = UnitOfElectricPotential.VOLT,
            suggested_display_precision = 1,
        ),

    # Sensor - Current on L1
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_i1, 
            name = "Current L1",
            translations = translations, 
            icon = "mdi:current-ac",
            default_value = "0",
            enabled_by_default = True,
            device_class = SensorDeviceClass.CURRENT,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = UnitOfElectricCurrent.AMPERE,
            suggested_display_precision = 2,
        ),

    # Sensor - Current on L2
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_i2, 
            name = "Current L2",
            translations = translations, 
            icon = "mdi:current-ac",
            default_value = "0",
            enabled_by_default = True,
            device_class = SensorDeviceClass.CURRENT,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = UnitOfElectricCurrent.AMPERE,
            suggested_display_precision = 2,
        ),

    # Sensor - Current on L3
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_i3, 
            name = "Current L3",
            translations = translations, 
            icon = "mdi:current-ac",
            default_value = "0",
            enabled_by_default = True,
            device_class = SensorDeviceClass.CURRENT,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = UnitOfElectricCurrent.AMPERE,
            suggested_display_precision = 2,
        ),

    # Sensor - Power on L1
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_p1, 
            name = "Power L1",
            translations = translations, 
            icon = "mdi:flash",
            default_value = "0",
            enabled_by_default = True,
            device_class = SensorDeviceClass.POWER,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = UnitOfPower.KILO_WATT,
            suggested_display_precision = 3,
        ),

    # Sensor - Power on L2
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_p2, 
            name = "Power L2",
            translations = translations, 
            icon = "mdi:flash",
            default_value = "0",
            enabled_by_default = True,
            device_class = SensorDeviceClass.POWER,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = UnitOfPower.KILO_WATT,
            suggested_display_precision = 3,
        ),

    # Sensor - Power on L3
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_p3, 
            name = "Power L3",
            translations = translations, 
            icon = "mdi:flash",
            default_value = "0",
            enabled_by_default = True,
            device_class = SensorDeviceClass.POWER,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = UnitOfPower.KILO_WATT,
            suggested_display_precision = 3,
        ),

    # Sensor - Meters Power
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_meters_power, 
            name = "Meters Power",
            translations = translations, 
            icon = "mdi:transmission-tower",
            default_value = "0",
            enabled_by_default = True,
            device_class = SensorDeviceClass.POWER,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = UnitOfPower.KILO_WATT,
            suggested_display_precision = 3,
        ),

    # Sensor - Inverters Power
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_inverters_power, 
            name = "Inverters Power",
            translations = translations, 
            icon = "mdi:solar-power-variant-outline",
            default_value = "0",
            enabled_by_default = True,
            device_class = SensorDeviceClass.POWER,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = UnitOfPower.KILO_WATT,
            suggested_display_precision = 3,
        ),

    # Sensor - Load Power
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_load_power, 
            name = "Load Power",
            translations = translations, 
            icon = "mdi:home-lightning-bolt-outline",
            default_value = "0",
            enabled_by_default = True,
            device_class = SensorDeviceClass.POWER,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = UnitOfPower.KILO_WATT,
            suggested_display_precision = 3,
        ),

    # Sensor - Export Limit
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_export_limit, 
            name = "Export Limit",
            translations = translations, 
            icon = "mdi:car-speed-limiter",
            default_value = "0",
            enabled_by_default = True,
            device_class = SensorDeviceClass.POWER,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = UnitOfPower.KILO_WATT,
            suggested_display_precision = 1,
        ),

    # Sensor - Export State
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_export_state, 
            name = "Export State",
            translations = translations, 
            icon = "mdi:lightbulb-on-50",
            default_value = "off",
            enabled_by_default = True,
            device_class = None,
            state_class = None,
            native_unit_of_measurement = None,
            suggested_display_precision = None,
        ),

    # Sensor - Modul started
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_modul_started, 
            name = "Modul started",
            translations = translations, 
            icon = "mdi:lightbulb-on-50",
            default_value = None,
            enabled_by_default = True,
            device_class = None,
            state_class = None,
            native_unit_of_measurement = None,
            suggested_display_precision = None,
        ),

    # Sensor - Export Disable - Feedback
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_export_disable_feedback, 
            name = "Export Disable - Feedback",
            translations = translations, 
            icon = "mdi:lightbulb-on-50",
            default_value = None,
            enabled_by_default = True,
            device_class = None,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = None,
            suggested_display_precision = 0,
        ),
   
    # Sensor - Export Enable - Feedback
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_export_enable_feedback, 
            name = "Export Enable - Feedback",
            translations = translations, 
            icon = "mdi:lightbulb-on-50",
            default_value = None,
            enabled_by_default = True,
            device_class = None,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = None,
            suggested_display_precision = 0,
        ), 
   
    # Sensor - Get Export Limit - Feedback
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_get_export_limit_feedback, 
            name = "Get Export Limit - Feedback",
            translations = translations, 
            icon = "mdi:lightbulb-on-50",
            default_value = None,
            enabled_by_default = True,
            device_class = None,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = None,
            suggested_display_precision = 0,
        ),

    # Sensor - Set Export Limit - Feedback
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_set_export_limit_feedback, 
            name = "Set Export Limit - Feedback",
            translations = translations, 
            icon = "mdi:lightbulb-on-50",
            default_value = None,
            enabled_by_default = True,
            device_class = None,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = None,
            suggested_display_precision = 0,
        ),

    # Sensor - Set Date and Time - Feedback
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_set_datetime_feedback, 
            name = "Set Date and Time - Feedback",
            translations = translations, 
            icon = "mdi:lightbulb-on-50",
            default_value = None,
            enabled_by_default = True,
            device_class = None,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = None,
            suggested_display_precision = 0,
        ),

    # Sensor - Get Telemetry Data - Feedback
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_get_telemetry_data_feedback, 
            name = "Get Telemetry Data - Feedback",
            translations = translations, 
            icon = "mdi:lightbulb-on-50",
            default_value = None,
            enabled_by_default = True,
            device_class = None,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = None,
            suggested_display_precision = 0,
        ),

    # Sensor - Reset Export Watchdog - Feedback
        SensorEntityDefinition(
            instance, 
            entry_id = entry.entry_id, 
            entity_id = ENTITY_SENSOR_reset_export_watchdog_feedback, 
            name = "Reset Export Watchdog - Feedback",
            translations = translations, 
            icon = "mdi:lightbulb-on-50",
            default_value = None,
            enabled_by_default = True,
            device_class = None,
            state_class = SensorStateClass.MEASUREMENT,
            native_unit_of_measurement = None,
            suggested_display_precision = 0,
        ),
    ]

    async_add_entities(entities)

class SensorEntityDefinition(SensorEntity):

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
        translations: dict = None,
        icon: str = "mdi:eye",
        default_value: str = None,
        enabled_by_default: bool = True,
        device_class: SensorDeviceClass | None = None,
        state_class: SensorStateClass | None = None,
        native_unit_of_measurement: str | None = None,
        suggested_display_precision: int | None = None,
        suggested_unit_of_measurement: str | None = None,
        entity_category: EntityCategory | None = None,
        options: list[str] | None = None,
        available: bool = True,
        last_reset: str | None = None,
    ) -> None:
        """Initialize the sensor."""
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
            entity_trans = translations.get("entity", {}).get("sensor", {}).get(entity_id, {})
            translated_name = entity_trans.get("name")
            if translated_name:
                self._attr_name = translated_name
            else:
                self._attr_name = name
        
        self.entity_id = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{entity_id}"
        self._attr_icon = icon
        self._entity_id = entity_id
        self._attr_native_value = default_value
        self._attr_available = available
        self._attr_entity_registry_enabled_default = enabled_by_default
        self._attr_entity_registry_visible_default = enabled_by_default

        if device_class is not None:
            self._attr_device_class = device_class
        if state_class is not None:
            self._attr_state_class = state_class
        if native_unit_of_measurement is not None:
            self._attr_native_unit_of_measurement = native_unit_of_measurement
        if suggested_display_precision is not None:
            self._attr_suggested_display_precision = suggested_display_precision
        if suggested_unit_of_measurement is not None:
            self._attr_suggested_unit_of_measurement = suggested_unit_of_measurement
        if entity_category is not None:
            self._attr_entity_category = entity_category
        if options is not None:
            self._attr_options = options
        if last_reset is not None:
            self._attr_last_reset = last_reset

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

    @callback
    def _handle_feedback_update(self) -> None:
        """Handle feedback update."""
        # Read value from appropriate source based on entity_id
        new_value = None
        try:
            # Telemetry data sensors (v1, v2, v3, i1, i2, i3, p1, p2, p3, meters_power, inverters_power, load_power)
            if self._entity_id in ['v1', 'v2', 'v3', 'i1', 'i2', 'i3', 'p1', 'p2', 'p3', 'meters_power', 'inverters_power', 'load_power']:
                new_value = getattr(self._instance._telemetrydata, self._entity_id, None)
            else:
                # Settings sensors (export_limit, export_state, modul_started, feedback sensors)
                new_value = getattr(self._instance.settings, self._entity_id, None)
            
            if new_value is not None:
                # Convert boolean to string for text-based sensors
                if isinstance(new_value, bool):
                    new_value = "on" if new_value else "off"
                self._attr_native_value = new_value
        except AttributeError:
            pass
        self.async_write_ha_state()

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return self._attr_native_value
from __future__ import annotations
"""Integration for Goodwe SEC1000"""
"""Author: Jozef Moravcik"""
"""email: jozef.moravcik@moravcik.eu"""

""" __init__.py """

"""Init for Goodwe SEC1000 integration"""
import asyncio
import logging
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.template import Template
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers import device_registry as dr


from .goodwe_sec1000 import Goodwe_SEC1000_Instance
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL


from .const import *

_LOGGER = logging.getLogger(__name__)

def _get_entry_id_for_device(hass: HomeAssistant, device: str = None) -> str:
    """Get entry_id for specified device or return the only one if device not specified."""
    if DOMAIN not in hass.data or not hass.data[DOMAIN]:
        raise ValueError("No Goodwe SEC1000 integrations configured")
    
    # Ak je device zadaný, nájdeme zariadenie s týmto názvom (case insensitive)
    if device:
        device_lower = device.lower()
        for entry_id, data in hass.data[DOMAIN].items():
            device_name = data.get("device_name_sanitized", "")
            if device_name.lower() == device_lower:
                return entry_id
        raise ValueError(f"Device '{device}' not found")
    
    # Ak device nie je zadaný
    entry_ids = list(hass.data[DOMAIN].keys())
    
    if len(entry_ids) == 1:
        # Len jedno zariadenie - použijeme ho
        return entry_ids[0]
    elif len(entry_ids) > 1:
        # Viac zariadení - musí byť zadaný parameter device
        available_devices = [data.get("device_name_sanitized") for data in hass.data[DOMAIN].values()]
        raise ValueError(
            f"Multiple devices configured. Please specify 'device' parameter. "
            f"Available devices: {', '.join(available_devices)}"
        )
    else:
        raise ValueError("No devices configured")

# Konštanta pre názov úložiska

# Globálna premenná pre úložisko
_STORAGE = None

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST, default=DEFAULT_HOST): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
                vol.Optional(CONF_MIN_EXPORT_LIMIT, default=DEFAULT_MIN_EXPORT_LIMIT): 
                    vol.All(vol.Coerce(float), vol.Range(min=-100.0, max=100.0)),
                vol.Optional(CONF_MAX_EXPORT_LIMIT, default=DEFAULT_MAX_EXPORT_LIMIT): 
                    vol.All(vol.Coerce(float), vol.Range(min=-100.0, max=100.0)),
                vol.Optional(CONF_TOTAL_CAPACITY, default=DEFAULT_TOTAL_CAPACITY): 
                    vol.All(vol.Coerce(float), vol.Range(min=0.0, max=100.0)),
                vol.Optional(CONF_EXPORT_LIMIT_CONTROL_MODE, default=DEFAULT_EXPORT_LIMIT_CONTROL_MODE): 
                    vol.All(vol.Coerce(int), vol.In([0, 1, 2, 3])),
                vol.Optional(CONF_SCAN_THREE_PHASES, default=DEFAULT_SCAN_THREE_PHASES): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON, Platform.SWITCH, Platform.NUMBER]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Goodwe SEC1000 component."""

    global _STORAGE
    _STORAGE = Store(hass, STORAGE_VERSION, STORAGE_KEY)

    if DOMAIN not in config:
        return True
        
    # Import from configuration.yaml
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "import"}, data=config[DOMAIN]
        )
    )

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Goodwe SEC1000 from a config entry."""
    device_name = entry.options.get(
        CONF_DEVICE_NAME,
        entry.data.get(CONF_DEVICE_NAME, DEFAULT_DEVICE_NAME)
    )
    include_device_name_in_entity = entry.options.get(
        CONF_INCLUDE_DEVICE_NAME_IN_ENTITY,
        entry.data.get(CONF_INCLUDE_DEVICE_NAME_IN_ENTITY, DEFAULT_INCLUDE_DEVICE_NAME_IN_ENTITY)
    )    
    host = entry.options.get(
        CONF_HOST,
        entry.data.get(CONF_HOST, DEFAULT_HOST)
    )
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    total_capacity = entry.options.get(
        CONF_TOTAL_CAPACITY,
        entry.data.get(CONF_TOTAL_CAPACITY, DEFAULT_TOTAL_CAPACITY)
    )
    export_limit_control_mode = entry.options.get(
        CONF_EXPORT_LIMIT_CONTROL_MODE,
        entry.data.get(CONF_EXPORT_LIMIT_CONTROL_MODE, DEFAULT_EXPORT_LIMIT_CONTROL_MODE)
    )
    scan_three_phases = entry.options.get(
        CONF_SCAN_THREE_PHASES,
        entry.data.get(CONF_SCAN_THREE_PHASES, DEFAULT_SCAN_THREE_PHASES)
    )

    # Načítanie uložených dát zo Store.
    # min/max_export_limit: storage má prioritu (nastavené službami) > options > data > default
    stored_data = await _STORAGE.async_load() or {}
    export_state = False
    min_export_limit = stored_data.get(
        "min_export_limit",
        entry.options.get(CONF_MIN_EXPORT_LIMIT,
            entry.data.get(CONF_MIN_EXPORT_LIMIT, DEFAULT_MIN_EXPORT_LIMIT))
    )
    max_export_limit = stored_data.get(
        "max_export_limit",
        entry.options.get(CONF_MAX_EXPORT_LIMIT,
            entry.data.get(CONF_MAX_EXPORT_LIMIT, DEFAULT_MAX_EXPORT_LIMIT))
    )

# ******************************************************************************************
# **** Uloženie všetkých nastavení do inštancie a do "core.config_entries"******************
# ******************************************************************************************    
    instance = Goodwe_SEC1000_Instance(host)
    # Nastavenie hass objektu a entry_id do inštancie
    instance.hass = hass
    instance._entry_id = entry.entry_id

    instance.settings.device_name = device_name
    instance.settings.include_device_name_in_entity = include_device_name_in_entity
    instance.settings.min_export_limit = min_export_limit
    instance.settings.max_export_limit = max_export_limit
    instance.settings.total_capacity = total_capacity
    instance.settings.export_limit_control_mode = export_limit_control_mode
    instance.settings.scan_three_phases = scan_three_phases
    instance.settings.export_state = export_state
    instance._device_lock = asyncio.Lock()
    
    _LOGGER.info(
        f"async_setup_entry: min_export_limit={min_export_limit}kW, "
        f"max_export_limit={max_export_limit}kW, "
        f"from options={CONF_MIN_EXPORT_LIMIT in entry.options}, "
        f"entry.options={entry.options}, entry.data={entry.data}"
    )
    
    # Nastavenie entity IDs po nastavení device_name
    instance.setup_entity_ids()
    
    # Service domain je fixný pre všetky zariadenia
    service_domain = DOMAIN  # "goodwe_sec1000"

    try:
        await hass.async_add_executor_job(instance.sec1000_get_telemetry_data)

        # Zariadenie odpovedá – nastavíme modul_started=True PRED registráciou platforiem,
        # aby žiadna externá automatizácia (napr. homeassistant.start) nemohla zavolať
        # export_enable/disable ešte pred tým, ako je zariadenie pripravené.
        # Bez tohto by export_enable_feedback dostalo hodnotu FEEDBACK_UNKNOWN_ERROR=4.
        instance.settings.modul_started = True

        # Vyčítanie aktuálneho stavu exportu zo zariadenia pred registráciou platforiem,
        # aby senzory a prepínač mali správny stav hneď po štarte.
        # POZOR: set_export_limit() sa tu úmyselne NEVOLÁ – pred touto opravou bola
        # táto funkcia vždy no-op (guard modul_started=False). Keby sa zavolala teraz,
        # zapísala by do zariadenia 4 TCP príkazy hneď po čítaní, čo by spôsobilo
        # nesprávne načítanie stavu exportu pri následnom get_export_limit() v 15s callbacku.
        await hass.async_add_executor_job(instance.get_export_limit)

        # Krátke oneskorenie
        await asyncio.sleep(4)
        
        # Vynútenie okamžitého vyčítania dát
        await hass.async_add_executor_job(instance.sec1000_get_telemetry_data)

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {
            "instance": instance,
            CONF_DEVICE_NAME: device_name,
            "device_name_sanitized": sanitize_device_name(device_name),
            CONF_INCLUDE_DEVICE_NAME_IN_ENTITY: include_device_name_in_entity,
            "host": host,
            "scan_interval": scan_interval,
            "min_export_limit": min_export_limit,
            "max_export_limit": max_export_limit,
            "total_capacity": total_capacity,
            "export_limit_control_mode": export_limit_control_mode,
            "scan_three_phases": scan_three_phases,
        }
        # Registrácia služieb pod fixnou doménou
        if not hass.services.has_service(DOMAIN, SERVICE_SYSTEM_STARTED):
            hass.services.async_register(
                DOMAIN,
                SERVICE_SYSTEM_STARTED,
                system_started_service,
                schema=vol.Schema({
                    vol.Optional("device"): cv.string,
                })
            )

        if not hass.services.has_service(DOMAIN, SERVICE_SET_EXPORT_LIMIT):
            hass.services.async_register(
                DOMAIN,
                SERVICE_SET_EXPORT_LIMIT,
                set_export_limit_service,
                schema=vol.Schema({
                    vol.Required("limit"): vol.Any(vol.Coerce(float), cv.string),
                    vol.Optional("device"): cv.string,
                })
            )

        if not hass.services.has_service(DOMAIN, SERVICE_GET_EXPORT_LIMIT):
            hass.services.async_register(
                DOMAIN,
                SERVICE_GET_EXPORT_LIMIT,
                get_export_limit_service,
                schema=vol.Schema({
                    vol.Optional("device"): cv.string,
                })
            )

        if not hass.services.has_service(DOMAIN, SERVICE_EXPORT_ENABLE):
            hass.services.async_register(
                DOMAIN,
                SERVICE_EXPORT_ENABLE,
                export_enable_service,
                schema=vol.Schema({
                    vol.Optional("device"): cv.string,
                })
            )

        if not hass.services.has_service(DOMAIN, SERVICE_EXPORT_DISABLE):
            hass.services.async_register(
                DOMAIN,
                SERVICE_EXPORT_DISABLE,
                export_disable_service,
                schema=vol.Schema({
                    vol.Optional("device"): cv.string,
                })
            )

        if not hass.services.has_service(DOMAIN, SERVICE_EXPORT_TOGGLE):
            hass.services.async_register(
                DOMAIN,
                SERVICE_EXPORT_TOGGLE,
                export_toggle_service,
                schema=vol.Schema({
                    vol.Optional("device"): cv.string,
                })
            )

        if not hass.services.has_service(DOMAIN, SERVICE_SET_DATETIME):
            hass.services.async_register(
                DOMAIN,
                SERVICE_SET_DATETIME,
                set_datetime_service,
                schema=vol.Schema({
                    vol.Optional("device"): cv.string,
                })
            )

        if not hass.services.has_service(DOMAIN, SERVICE_RESET_EXPORT_WATCHDOG):
            hass.services.async_register(
                DOMAIN,
                SERVICE_RESET_EXPORT_WATCHDOG,
                reset_export_watchdog,
                schema=vol.Schema({
                    vol.Optional("device"): cv.string,
                })
            )

        if not hass.services.has_service(DOMAIN, SERVICE_SET_MIN_EXPORT_LIMIT):
            hass.services.async_register(
                DOMAIN,
                SERVICE_SET_MIN_EXPORT_LIMIT,
                set_min_export_limit_service,
                schema=vol.Schema({
                    vol.Required("limit"): vol.All(vol.Coerce(float), vol.Range(min=-100.0, max=100.0)),
                    vol.Optional("device"): cv.string,
                })
            )

        if not hass.services.has_service(DOMAIN, SERVICE_SET_MAX_EXPORT_LIMIT):
            hass.services.async_register(
                DOMAIN,
                SERVICE_SET_MAX_EXPORT_LIMIT,
                set_max_export_limit_service,
                schema=vol.Schema({
                    vol.Required("limit"): vol.All(vol.Coerce(float), vol.Range(min=-100.0, max=100.0)),
                    vol.Optional("device"): cv.string,
                })
            )

        # Register update listener for options changes
        entry.async_on_unload(entry.add_update_listener(update_listener))

        # Wrapper funkcia pre bezpečné volanie async funkcie
        async def _schedule_callback(_now=None):
            await async_call_get_export_limit_callback(hass, entry.entry_id)
        
        # Schedule get_export_limit to run after a delay to ensure all is initialized
        async_call_later(hass, 15, _schedule_callback)

        async def async_update_feedback_sensors(_now=None):
            """Asynchrónna aktualizácia feedback senzorov."""
            async_dispatcher_send(hass, f"{DOMAIN}_feedback_update_{entry.entry_id}")
        async def async_update_settings_sensors(_now=None):
            """Asynchrónna aktualizácia settings senzorov."""
            async_dispatcher_send(hass, f"{DOMAIN}_settings_update_{entry.entry_id}")
        # Plán jednorazových volaní
        async_call_later(hass, 20, async_update_feedback_sensors)
        async_call_later(hass, 25, async_update_settings_sensors)

        # Funkcia pre pravidelnú aktualizáciu telemetrických údajov
        async def async_update_telemetry(_now=None):
            """Pravidelná aktualizácia telemetrických údajov."""
            try:
                # Načítať telemetriu zo zariadenia
                await hass.async_add_executor_job(instance.sec1000_get_telemetry_data)
                # Aktualizovať senzory
                async_dispatcher_send(hass, f"{DOMAIN}_feedback_update_{entry.entry_id}")
                _LOGGER.debug(f"Telemetry data updated for {entry.entry_id}")
            except Exception as ex:
                _LOGGER.debug(f"Error updating telemetry data: {ex}")
        
        # Nastaviť pravidelný časovač pre aktualizáciu telemetrie
        from datetime import timedelta
        update_interval = timedelta(seconds=scan_interval)
        entry.async_on_unload(
            async_track_time_interval(hass, async_update_telemetry, update_interval)
        )
        _LOGGER.info(f"Telemetry update interval set to {scan_interval} seconds")

        # Forward platform setup at the end to minimize blocking import warnings
        # Vytvorenie platforiem až po nastavení všetkých časovačov a načítaní dát
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        
        # Po vytvorení platforiem okamžite pošleme aktualizáciu, aby mali senzory dostupné dáta
        async_dispatcher_send(hass, f"{DOMAIN}_feedback_update_{entry.entry_id}")
        async_dispatcher_send(hass, f"{DOMAIN}_settings_update_{entry.entry_id}")

    except Exception as ex:
        _LOGGER.debug("Failed to connect to Goodwe SEC1000: %s", ex)
        raise ConfigEntryNotReady from ex

    return True

async def system_started_service(call: ServiceCall) -> None:
    """Handle system started service call."""
    try:
        device = call.data.get("device")
        entry_id = _get_entry_id_for_device(call.hass, device)
        instance = call.hass.data[DOMAIN][entry_id].get("instance")

        if instance:
            await call.hass.async_add_executor_job(instance.system_started)

    except ValueError as ex:
        _LOGGER.error("Error in system_started_service: %s", ex)
        raise HomeAssistantError(str(ex)) from ex
    except Exception as ex:
        _LOGGER.error("Error in system_started_service: %s", ex)
        raise HomeAssistantError(f"Unexpected error: {ex}") from ex

# Async function for the callback
async def async_call_get_export_limit_callback(hass, entry_id):
    """Call the services during initialization (async callback)."""
    try:
        # Získanie device_name_sanitized pre toto zariadenie
        device_name_sanitized = hass.data[DOMAIN][entry_id].get("device_name_sanitized")
        if not device_name_sanitized:
            _LOGGER.error("Device name not found for entry_id: %s", entry_id)
            return
            
        # Volanie prvej služby s parametrom device
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SYSTEM_STARTED,
            {"device": device_name_sanitized},
            blocking=False
        )
        
        # Počkať 2 sekundy a zavolať druhú službu
        await asyncio.sleep(2)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_EXPORT_LIMIT,
            {"device": device_name_sanitized},
            blocking=False
        )
    except Exception as ex:
        _LOGGER.error(f"Error calling services in callback: {ex}")

# Helper function to save export_state to Store
async def _save_to_storage(hass: HomeAssistant, **kwargs) -> None:
    """Uloží zadané kľúče do storage, ostatné existujúce kľúče zachová."""
    try:
        data = await _STORAGE.async_load() or {}
        data.update(kwargs)
        await _STORAGE.async_save(data)
        _LOGGER.info(f"Saved to storage: {kwargs}")
    except Exception as ex:
        _LOGGER.error(f"Error saving to storage: {ex}")


async def save_export_state(hass: HomeAssistant, export_state: bool):
    """Save export_state to persistent storage."""
    await _save_to_storage(hass, export_state=export_state)


async def save_min_export_limit(hass: HomeAssistant, value: float):
    """Save min_export_limit to persistent storage."""
    await _save_to_storage(hass, min_export_limit=value)


async def save_max_export_limit(hass: HomeAssistant, value: float):
    """Save max_export_limit to persistent storage."""
    await _save_to_storage(hass, max_export_limit=value)

# Registrácia služby pre nastavenie limitu exportu
async def set_export_limit_service(call: ServiceCall) -> None:
    """Service to set the export limit."""
    try:
        device = call.data.get("device")
        entry_id = _get_entry_id_for_device(call.hass, device)
        
        # Získanie reťazca limitu
        limit_str = str(call.data.get("limit", "0"))
        
        # Ak obsahuje šablónu, pokúsime sa ju vyhodnotiť
        if "{{" in limit_str and "}}" in limit_str:
            template = Template(limit_str, call.hass)
            limit_rendered = template.async_render()
            try:
                limit_float = float(limit_rendered)
            except ValueError:
                _LOGGER.error("Template rendered to invalid float: %s", limit_rendered)
                return
        else:
            # Inak sa pokúsime priamo konvertovať
            try:
                limit_float = float(limit_str)
            except ValueError:
                _LOGGER.error("Invalid float value: %s", limit_str)
                return
        
        instance = call.hass.data[DOMAIN][entry_id].get("instance")
        if instance:
            min_limit = instance.settings.min_export_limit
            max_limit = instance.settings.max_export_limit

            # Apply min/max limits
            if limit_float < min_limit:
                _LOGGER.warning("Export limit adjusted from %s to minimum %s", limit_float, min_limit)
                limit_float = min_limit
            elif limit_float > max_limit:
                _LOGGER.warning("Export limit adjusted from %s to maximum %s", limit_float, max_limit)
                limit_float = max_limit

            await call.hass.async_add_executor_job(instance.reset_set_export_limit_feedback)
            async_dispatcher_send(call.hass, f"{DOMAIN}_feedback_update_{entry_id}")
            async with instance._device_lock:
                await call.hass.async_add_executor_job(instance.set_export_limit, limit_float)
                # Aktualizácia export_state na základe nastaveného limitu — vo vnútri locku
                old_export_state = instance.settings.export_state
                if (limit_float - instance.settings.min_export_limit) < 0.01:
                    instance.settings.export_state = False
                else:
                    instance.settings.export_state = True
                await asyncio.sleep(DEFAULT_DEVICE_COMMAND_DELAY_MS / 1000)
            # Ak sa export_state zmenil, uložím ho do Store
            if old_export_state != instance.settings.export_state:
                await save_export_state(call.hass, instance.settings.export_state)

            async_dispatcher_send(call.hass, f"{DOMAIN}_feedback_update_{entry_id}")
            async_dispatcher_send(call.hass, f"{DOMAIN}_settings_update_{entry_id}")

        else:
            _LOGGER.error("Instance not found for entry_id %s", entry_id)
            raise HomeAssistantError(f"Instance not found for entry_id {entry_id}")
    except ValueError as ex:
        _LOGGER.error("Error in set_export_limit_service: %s", ex)
        raise HomeAssistantError(str(ex)) from ex
    except HomeAssistantError:
        raise
    except Exception as ex:
        _LOGGER.error("Error in set_export_limit_service: %s", ex)
        raise HomeAssistantError(f"Unexpected error: {ex}") from ex

async def get_export_limit_service(call: ServiceCall) -> bool:
    """Service to get the export limit and update settings."""
    try:
        device = call.data.get("device")
        entry_id = _get_entry_id_for_device(call.hass, device)
        instance = call.hass.data[DOMAIN][entry_id].get("instance")
        
        if instance:
            await call.hass.async_add_executor_job(instance.reset_get_export_limit_feedback)
            async_dispatcher_send(call.hass, f"{DOMAIN}_feedback_update_{entry_id}")
            
            # Získanie údajov z zariadenia
            await call.hass.async_add_executor_job(instance.get_export_limit)
            
            # Aktualizácia hodnôt v hass.data pre danú integráciu
            call.hass.data[DOMAIN][entry_id]["export_limit_control_mode"] = instance.settings.export_limit_control_mode
            call.hass.data[DOMAIN][entry_id]["total_capacity"] = instance.settings.total_capacity

            # Uloženie export_state do Store
            old_export_state = instance.settings.export_state
            if (instance.settings.export_limit - instance.settings.min_export_limit) < 0.01:
                instance.settings.export_state = False
            else:
                instance.settings.export_state = True
                
            # Ak sa export_state zmenil, uložíme ho do Store
            if old_export_state != instance.settings.export_state:
                await save_export_state(call.hass, instance.settings.export_state)

            # Aktualizácia konfiguračného záznamu pre perzistenciu medzi reštartmi
            # Nájdenie zodpovedajúcej konfiguračnej položky
            config_entries = call.hass.config_entries.async_entries(DOMAIN)
            entry = next((e for e in config_entries if e.entry_id == entry_id), None)
            
            if entry:
                # Aktualizácia konfiguračného záznamu
                new_data = dict(entry.data)
                new_data[CONF_EXPORT_LIMIT_CONTROL_MODE] = instance.settings.export_limit_control_mode
                new_data[CONF_TOTAL_CAPACITY] = instance.settings.total_capacity
                call.hass.config_entries.async_update_entry(entry, data=new_data)
                
                _LOGGER.info(
                    f"Settings updated from device: "
                    f"Export Limit Control Mode={instance.settings.export_limit_control_mode}, "
                    f"Total Capacity={instance.settings.total_capacity}kW, "
                    f"Export Limit={instance.settings.export_limit}kW, "
                    f"Export State={instance.settings.export_state}"
                )
            else:
                _LOGGER.error("Config entry not found for entry_id %s", entry_id)

            async_dispatcher_send(call.hass, f"{DOMAIN}_feedback_update_{entry_id}")
            async_dispatcher_send(call.hass, f"{DOMAIN}_settings_update_{entry_id}")
        else:
            _LOGGER.error("Instance not found for entry_id %s", entry_id)
            raise HomeAssistantError(f"Instance not found for entry_id {entry_id}")
    except ValueError as ex:
        _LOGGER.error("Error in get_export_limit_service: %s", ex)
        raise HomeAssistantError(str(ex)) from ex
    except HomeAssistantError:
        raise
    except Exception as ex:
        _LOGGER.error("Error in get_export_limit_service: %s", ex)
        raise HomeAssistantError(f"Unexpected error: {ex}") from ex

async def export_enable_service(call: ServiceCall) -> None:
    """Simple service which enable export following re-setup values and parameters """
    try:
        device = call.data.get("device")
        entry_id = _get_entry_id_for_device(call.hass, device)
        instance = call.hass.data[DOMAIN][entry_id].get("instance")

        if instance:
            await call.hass.async_add_executor_job(instance.reset_export_enable_feedback)
            async_dispatcher_send(call.hass, f"{DOMAIN}_feedback_update_{entry_id}")
            async with instance._device_lock:
                await call.hass.async_add_executor_job(instance.export_enable)
                instance.settings.export_state = True  # vo vnútri locku
                await asyncio.sleep(DEFAULT_DEVICE_COMMAND_DELAY_MS / 1000)
            await save_export_state(call.hass, True)
            async_dispatcher_send(call.hass, f"{DOMAIN}_feedback_update_{entry_id}")
            async_dispatcher_send(call.hass, f"{DOMAIN}_settings_update_{entry_id}")
        else:
            _LOGGER.error("Instance not found for entry_id %s", entry_id)
            raise HomeAssistantError(f"Instance not found for entry_id {entry_id}")

    except ValueError as ex:
        _LOGGER.error("Error in export_enable_service: %s", ex)
        raise HomeAssistantError(str(ex)) from ex
    except HomeAssistantError:
        raise
    except Exception as ex:
        _LOGGER.error("Error in export_enable_service: %s", ex)
        raise HomeAssistantError(f"Unexpected error: {ex}") from ex

async def export_disable_service(call: ServiceCall) -> None:
    """Simple service which disable export following re-setup values and parameters """
    try:
        device = call.data.get("device")
        entry_id = _get_entry_id_for_device(call.hass, device)
        instance = call.hass.data[DOMAIN][entry_id].get("instance")

        if instance:
            await call.hass.async_add_executor_job(instance.reset_export_disable_feedback)
            async_dispatcher_send(call.hass, f"{DOMAIN}_feedback_update_{entry_id}")
            async with instance._device_lock:
                await call.hass.async_add_executor_job(instance.export_disable)
                instance.settings.export_state = False  # vo vnútri locku
                await asyncio.sleep(DEFAULT_DEVICE_COMMAND_DELAY_MS / 1000)
            await save_export_state(call.hass, False)
            async_dispatcher_send(call.hass, f"{DOMAIN}_feedback_update_{entry_id}")
            async_dispatcher_send(call.hass, f"{DOMAIN}_settings_update_{entry_id}")
        else:
            _LOGGER.error("Instance not found for entry_id %s", entry_id)
            raise HomeAssistantError(f"Instance not found for entry_id {entry_id}")

    except ValueError as ex:
        _LOGGER.error("Error in export_disable_service: %s", ex)
        raise HomeAssistantError(str(ex)) from ex
    except HomeAssistantError:
        raise
    except Exception as ex:
        _LOGGER.error("Error in export_disable_service: %s", ex)
        raise HomeAssistantError(f"Unexpected error: {ex}") from ex

async def export_toggle_service(call: ServiceCall) -> None:
    """Simple service which toggles export state """
    try:
        device = call.data.get("device")
        entry_id = _get_entry_id_for_device(call.hass, device)
        instance = call.hass.data[DOMAIN][entry_id].get("instance")

        if instance:
            # Determine which feedback to reset based on current state
            if instance.settings.export_state:
                # Currently enabled, will disable
                await call.hass.async_add_executor_job(instance.reset_export_disable_feedback)
            else:
                # Currently disabled, will enable
                await call.hass.async_add_executor_job(instance.reset_export_enable_feedback)
            
            async_dispatcher_send(call.hass, f"{DOMAIN}_feedback_update_{entry_id}")
            
            # Call toggle and save new state — export_toggle interne aktualizuje export_state
            async with instance._device_lock:
                await call.hass.async_add_executor_job(instance.export_toggle)
                await asyncio.sleep(DEFAULT_DEVICE_COMMAND_DELAY_MS / 1000)
            await save_export_state(call.hass, instance.settings.export_state)
            
            async_dispatcher_send(call.hass, f"{DOMAIN}_feedback_update_{entry_id}")
            async_dispatcher_send(call.hass, f"{DOMAIN}_settings_update_{entry_id}")
        else:
            _LOGGER.error("Instance not found for entry_id %s", entry_id)
            raise HomeAssistantError(f"Instance not found for entry_id {entry_id}")

    except ValueError as ex:
        _LOGGER.error("Error in export_toggle_service: %s", ex)
        raise HomeAssistantError(str(ex)) from ex
    except HomeAssistantError:
        raise
    except Exception as ex:
        _LOGGER.error("Error in export_toggle_service: %s", ex)
        raise HomeAssistantError(f"Unexpected error: {ex}") from ex

async def set_datetime_service(call: ServiceCall) -> None:
    try:
        device = call.data.get("device")
        entry_id = _get_entry_id_for_device(call.hass, device)
        instance = call.hass.data[DOMAIN][entry_id].get("instance")

        if instance:
            await call.hass.async_add_executor_job(instance.reset_set_datetime_feedback)
            async_dispatcher_send(call.hass, f"{DOMAIN}_feedback_update_{entry_id}")
            await call.hass.async_add_executor_job(instance.set_datetime)
            async_dispatcher_send(call.hass, f"{DOMAIN}_feedback_update_{entry_id}")
            async_dispatcher_send(call.hass, f"{DOMAIN}_settings_update_{entry_id}")
        else:
            _LOGGER.error("Instance not found for entry_id %s", entry_id)
            raise HomeAssistantError(f"Instance not found for entry_id {entry_id}")

    except ValueError as ex:
        _LOGGER.error("Error in set_datetime_service: %s", ex)
        raise HomeAssistantError(str(ex)) from ex
    except HomeAssistantError:
        raise
    except Exception as ex:
        _LOGGER.error("Error in set_datetime_service: %s", ex)
        raise HomeAssistantError(f"Unexpected error: {ex}") from ex

async def reset_export_watchdog(call: ServiceCall) -> None:
    """Simple service which "reset" watchdog which controlls export limit on the converters """
    try:
        device = call.data.get("device")
        entry_id = _get_entry_id_for_device(call.hass, device)
        instance = call.hass.data[DOMAIN][entry_id].get("instance")

        if instance:
            await call.hass.async_add_executor_job(instance.reset_reset_export_watchdog_feedback)
            async_dispatcher_send(call.hass, f"{DOMAIN}_feedback_update_{entry_id}")
            await call.hass.async_add_executor_job(instance.reset_export_watchdog)
            async_dispatcher_send(call.hass, f"{DOMAIN}_feedback_update_{entry_id}")
            async_dispatcher_send(call.hass, f"{DOMAIN}_settings_update_{entry_id}")
        else:
            _LOGGER.error("Instance not found for entry_id %s", entry_id)
            raise HomeAssistantError(f"Instance not found for entry_id {entry_id}")

    except ValueError as ex:
        _LOGGER.error("Error in reset_export_watchdog: %s", ex)
        raise HomeAssistantError(str(ex)) from ex
    except HomeAssistantError:
        raise
    except Exception as ex:
        _LOGGER.error("Error in reset_export_watchdog: %s", ex)
        raise HomeAssistantError(f"Unexpected error: {ex}") from ex


async def set_min_export_limit_service(call: ServiceCall) -> None:
    """Service to set the minimum export limit configuration parameter."""
    try:
        device = call.data.get("device")
        entry_id = _get_entry_id_for_device(call.hass, device)
        instance = call.hass.data[DOMAIN][entry_id].get("instance")

        if not instance:
            _LOGGER.error("Instance not found for entry_id %s", entry_id)
            raise HomeAssistantError(f"Instance not found for entry_id {entry_id}")

        new_limit = float(call.data["limit"])

        instance.settings.min_export_limit = new_limit
        call.hass.data[DOMAIN][entry_id]["min_export_limit"] = new_limit

        # Ak je export vypnutý, odošli novú hodnotu do zariadenia.
        # Kontrola export_state je vo vnútri locku — eliminuje race condition
        # s export_enable/disable ktoré bežia súčasne.
        async with instance._device_lock:
            if not instance.settings.export_state:
                _LOGGER.info(f"set_min_export_limit: export OFF -> sending {new_limit}kW to device")
                await call.hass.async_add_executor_job(instance.set_export_limit, new_limit)
                await asyncio.sleep(DEFAULT_DEVICE_COMMAND_DELAY_MS / 1000)

        # Persistencia priamo do _STORAGE — žiadny async_update_entry, žiadny platform reload
        await save_min_export_limit(call.hass, new_limit)
        async_dispatcher_send(call.hass, f"{DOMAIN}_feedback_update_{entry_id}")
        async_dispatcher_send(call.hass, f"{DOMAIN}_settings_update_{entry_id}")

    except ValueError as ex:
        _LOGGER.error("Error in set_min_export_limit_service: %s", ex)
        raise HomeAssistantError(str(ex)) from ex
    except HomeAssistantError:
        raise
    except Exception as ex:
        _LOGGER.error("Error in set_min_export_limit_service: %s", ex)
        raise HomeAssistantError(f"Unexpected error: {ex}") from ex


async def set_max_export_limit_service(call: ServiceCall) -> None:
    """Service to set the maximum export limit configuration parameter."""
    try:
        device = call.data.get("device")
        entry_id = _get_entry_id_for_device(call.hass, device)
        instance = call.hass.data[DOMAIN][entry_id].get("instance")

        if not instance:
            _LOGGER.error("Instance not found for entry_id %s", entry_id)
            raise HomeAssistantError(f"Instance not found for entry_id {entry_id}")

        new_limit = float(call.data["limit"])

        instance.settings.max_export_limit = new_limit
        call.hass.data[DOMAIN][entry_id]["max_export_limit"] = new_limit

        # Ak je export zapnutý, odošli novú hodnotu do zariadenia.
        # Kontrola export_state je vo vnútri locku — eliminuje race condition
        # s export_enable/disable ktoré bežia súčasne.
        async with instance._device_lock:
            if instance.settings.export_state:
                _LOGGER.info(f"set_max_export_limit: export ON -> sending {new_limit}kW to device")
                await call.hass.async_add_executor_job(instance.set_export_limit, new_limit)
                await asyncio.sleep(DEFAULT_DEVICE_COMMAND_DELAY_MS / 1000)

        # Persistencia priamo do _STORAGE — žiadny async_update_entry, žiadny platform reload
        await save_max_export_limit(call.hass, new_limit)
        async_dispatcher_send(call.hass, f"{DOMAIN}_feedback_update_{entry_id}")
        async_dispatcher_send(call.hass, f"{DOMAIN}_settings_update_{entry_id}")

    except ValueError as ex:
        _LOGGER.error("Error in set_max_export_limit_service: %s", ex)
        raise HomeAssistantError(str(ex)) from ex
    except HomeAssistantError:
        raise
    except Exception as ex:
        _LOGGER.error("Error in set_max_export_limit_service: %s", ex)
        raise HomeAssistantError(f"Unexpected error: {ex}") from ex


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    # Získanie údajov z konfigurácie
    device_name = entry.options.get(
        CONF_DEVICE_NAME,
        entry.data.get(CONF_DEVICE_NAME, DEFAULT_DEVICE_NAME)
    )
    include_device_name_in_entity = entry.options.get(
        CONF_INCLUDE_DEVICE_NAME_IN_ENTITY,
        entry.data.get(CONF_INCLUDE_DEVICE_NAME_IN_ENTITY, DEFAULT_INCLUDE_DEVICE_NAME_IN_ENTITY)
    )
    host = entry.options.get(
        CONF_HOST,
        entry.data.get(CONF_HOST, DEFAULT_HOST)
    )
    total_capacity = entry.options.get(
        CONF_TOTAL_CAPACITY,
        entry.data.get(CONF_TOTAL_CAPACITY, DEFAULT_TOTAL_CAPACITY)
    )
    export_limit_control_mode = entry.options.get(
        CONF_EXPORT_LIMIT_CONTROL_MODE,
        entry.data.get(CONF_EXPORT_LIMIT_CONTROL_MODE, DEFAULT_EXPORT_LIMIT_CONTROL_MODE)
    )
    scan_three_phases = entry.options.get(
        CONF_SCAN_THREE_PHASES,
        entry.data.get(CONF_SCAN_THREE_PHASES, DEFAULT_SCAN_THREE_PHASES)
    )
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )

    stored_data = await _STORAGE.async_load() or {}
    export_state = stored_data.get("export_state", False)

    # Ak boli min/max_export_limit zmenené cez UI (Options Flow), prevezmeme hodnoty z options
    # a uložíme ich do storage — storage je autoritatívny zdroj pre tieto hodnoty
    options_min = entry.options.get(CONF_MIN_EXPORT_LIMIT, None)
    options_max = entry.options.get(CONF_MAX_EXPORT_LIMIT, None)
    if options_min is not None:
        stored_data["min_export_limit"] = options_min
    if options_max is not None:
        stored_data["max_export_limit"] = options_max
    if options_min is not None or options_max is not None:
        await _save_to_storage(hass, **{k: v for k, v in stored_data.items()
                                        if k in ("min_export_limit", "max_export_limit")})

    min_export_limit = stored_data.get(
        "min_export_limit",
        entry.options.get(CONF_MIN_EXPORT_LIMIT,
            entry.data.get(CONF_MIN_EXPORT_LIMIT, DEFAULT_MIN_EXPORT_LIMIT))
    )
    max_export_limit = stored_data.get(
        "max_export_limit",
        entry.options.get(CONF_MAX_EXPORT_LIMIT,
            entry.data.get(CONF_MAX_EXPORT_LIMIT, DEFAULT_MAX_EXPORT_LIMIT))
    )

    # Bezpečne skopírujeme inštanciu a všetky nastavenia pred vymazaním
    old_data = None
    old_instance = None
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        old_data = hass.data[DOMAIN][entry.entry_id].copy()
        if "instance" in old_data:
            old_instance = old_data["instance"]
    
    # Vymazanie entít pred vytvorením nových
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if old_instance:
        instance = old_instance
        # Zachovaj hodnoty spätnej väzby z predchádzajúcej inštancie
        export_disable_feedback = old_instance.settings.export_disable_feedback
        export_enable_feedback = old_instance.settings.export_enable_feedback
        get_export_limit_feedback = old_instance.settings.get_export_limit_feedback
        set_export_limit_feedback = old_instance.settings.set_export_limit_feedback
        set_datetime_feedback = old_instance.settings.set_datetime_feedback
        get_telemetry_data_feedback = old_instance.settings.get_telemetry_data_feedback
        reset_export_watchdog_feedback = old_instance.settings.reset_export_watchdog_feedback
        device_initialized = old_instance.settings.device_initialized
    else:
        instance = Goodwe_SEC1000_Instance(host) # Vytvorenie novej inštancie, ak predchádzajúca neexistuje
        export_disable_feedback = FEEDBACK_INIT
        export_enable_feedback = FEEDBACK_INIT
        get_export_limit_feedback = FEEDBACK_INIT
        set_export_limit_feedback = FEEDBACK_INIT
        set_datetime_feedback = FEEDBACK_INIT
        get_telemetry_data_feedback = FEEDBACK_INIT
        reset_export_watchdog_feedback = FEEDBACK_INIT
        device_initialized = False

    # Aktualizácia nastavení inštancie
    instance.set_host(host)
    instance.settings.device_name = device_name
    instance.settings.include_device_name_in_entity = include_device_name_in_entity
    
    # Nastavenie entity IDs po aktualizácii device_name
    instance.setup_entity_ids()
    instance.settings.min_export_limit = min_export_limit
    instance.settings.max_export_limit = max_export_limit
    instance.settings.total_capacity = total_capacity
    instance.settings.export_limit_control_mode = export_limit_control_mode
    instance.settings.scan_three_phases = scan_three_phases
    instance.settings.export_state = export_state
    
    _LOGGER.info(
        f"update_listener: min_export_limit={min_export_limit}kW, "
        f"max_export_limit={max_export_limit}kW, "
        f"export_limit_control_mode={export_limit_control_mode}, "
        f"from options={CONF_EXPORT_LIMIT_CONTROL_MODE in entry.options}"
    )
    
    # Obnov hodnoty spätnej väzby
    instance.settings.export_disable_feedback = export_disable_feedback
    instance.settings.export_enable_feedback = export_enable_feedback
    instance.settings.get_export_limit_feedback = get_export_limit_feedback
    instance.settings.set_export_limit_feedback = set_export_limit_feedback
    instance.settings.set_datetime_feedback = set_datetime_feedback
    instance.settings.get_telemetry_data_feedback = get_telemetry_data_feedback
    instance.settings.reset_export_watchdog_feedback = reset_export_watchdog_feedback
    instance.settings.device_initialized = device_initialized

    
    # Aktualizovať údaje
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "instance": instance,
        "device_name_sanitized": sanitize_device_name(device_name),
        "host": host,
        "scan_interval": scan_interval,
        "min_export_limit": min_export_limit,
        "max_export_limit": max_export_limit,
        "total_capacity": total_capacity,
        "export_limit_control_mode": export_limit_control_mode,
        "scan_three_phases": scan_three_phases
    }
    
    # Nastavenie nových entít
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Prenos konfiguračných údajov do zariadenia len keď sa zmenili limity a zodpovedajú aktuálnemu stavu exportu:
    # - ak sa zmenil min_export_limit A export je vypnutý → odošli min_export_limit do zariadenia
    # - ak sa zmenil max_export_limit A export je zapnutý → odošli max_export_limit do zariadenia
    old_min = old_data.get("min_export_limit") if old_data else None
    old_max = old_data.get("max_export_limit") if old_data else None

    if old_min is not None and old_min != min_export_limit and not instance.settings.export_state:
        _LOGGER.info(f"update_listener: min_export_limit changed {old_min} → {min_export_limit}, export OFF → sending to device")
        await hass.async_add_executor_job(instance.set_export_limit, min_export_limit)
    elif old_max is not None and old_max != max_export_limit and instance.settings.export_state:
        _LOGGER.info(f"update_listener: max_export_limit changed {old_max} → {max_export_limit}, export ON → sending to device")
        await hass.async_add_executor_job(instance.set_export_limit, max_export_limit)
    
    # NEBUDEME volať get_telemetry_data, aby sa zachovali existujúce hodnoty senzorov
    # Nové hodnoty sa načítajú pri najbližšom pravidelnom update cykle
    # Okamžite pošleme aktualizáciu senzorov so zachovanými hodnotami
    async_dispatcher_send(hass, f"{DOMAIN}_feedback_update_{entry.entry_id}")
    async_dispatcher_send(hass, f"{DOMAIN}_settings_update_{entry.entry_id}")
    
#    # Vynútenie aktualizácie všetkých senzorov naraz
#    async def _schedule_update_callback(_now=None):
#        await async_call_get_export_limit_callback(hass)
#    
#    async_call_later(hass, 5, _schedule_update_callback)
    
#    # Reload integráciu aby sa prejavili zmeny v názvoch entít a nastaveniach
#    await hass.config_entries.async_reload(entry.entry_id)    
    
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    try:
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        
        if unload_ok:
            hass.data[DOMAIN].pop(entry.entry_id, None)

#        await async_unload_entry(hass, entry)
#        await async_setup_entry(hass, entry)

        return unload_ok

    except Exception as ex:
        _LOGGER.error("Error unloading entry: %s", ex)
        # Ensure we cleanup even on error
        if DOMAIN in hass.data and entry.entry_id in hass.data.get(DOMAIN, {}):
            hass.data[DOMAIN].pop(entry.entry_id, None)
        return False

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
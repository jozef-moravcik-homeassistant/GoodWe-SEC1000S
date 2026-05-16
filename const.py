"""Integration for Goodwe SEC1000"""
"""Author: Jozef Moravcik"""
"""email: jozef.moravcik@moravcik.eu"""

""" const.py """

"""Constants for the Goodwe SEC1000 integration"""
from homeassistant.const import STATE_ON, STATE_OFF, STATE_UNKNOWN, STATE_UNAVAILABLE, STATE_OK, STATE_PROBLEM

DOMAIN = "goodwe_sec1000"

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.state"
VERSION = "1.01.01"
MANUFACTURER = "Jozef Moravcik"
MODEL = "GoodWe SEC1000/S"
NAME = "GoodWe SEC1000/S"
ENTITY_PREFIX = "sec1000"

def sanitize_device_name(device_name: str) -> str:
    """Sanitize device name for use in entity IDs."""
    import re
    # Convert to lowercase
    sanitized = device_name.lower()
    # Replace spaces and special characters with underscore
    sanitized = re.sub(r'[^a-z0-9]+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Limit length
    sanitized = sanitized[:20]
    return sanitized if sanitized else "device"

##############################################################################################################################
# SERVICES ###################################################################################################################
##############################################################################################################################

SERVICE_SYSTEM_STARTED = "system_started"
SERVICE_SET_EXPORT_LIMIT = "set_export_limit"
SERVICE_GET_EXPORT_LIMIT = "get_export_limit"
SERVICE_EXPORT_ENABLE = "export_enable"
SERVICE_EXPORT_DISABLE = "export_disable"
SERVICE_EXPORT_TOGGLE = "export_toggle"
SERVICE_SET_DATETIME = "set_datetime"
SERVICE_RESET_EXPORT_WATCHDOG = "reset_export_watchdog"
SERVICE_SET_MIN_EXPORT_LIMIT = "set_min_export_limit"
SERVICE_SET_MAX_EXPORT_LIMIT = "set_max_export_limit"

##############################################################################################################################
# Internal entity names (will be prefixed with DOMAIN in code) ###############################################################
# These entities are created by this integration #############################################################################
##############################################################################################################################
ENTITY_SENSOR_v1 = "v1"
ENTITY_SENSOR_v2 = "v2"
ENTITY_SENSOR_v3 = "v3"
ENTITY_SENSOR_i1 = "i1"
ENTITY_SENSOR_i2 = "i2"
ENTITY_SENSOR_i3 = "i3"
ENTITY_SENSOR_p1 = "p1"
ENTITY_SENSOR_p2 = "p2"
ENTITY_SENSOR_p3 = "p3"
ENTITY_SENSOR_meters_power = "meters_power"
ENTITY_SENSOR_inverters_power = "inverters_power"
ENTITY_SENSOR_load_power = "load_power"
ENTITY_SENSOR_export_limit = "export_limit"
ENTITY_SENSOR_export_state = "export_state"
ENTITY_SENSOR_modul_started = "modul_started"
ENTITY_SENSOR_export_disable_feedback = "export_disable_feedback"
ENTITY_SENSOR_export_enable_feedback = "export_enable_feedback"
ENTITY_SENSOR_get_export_limit_feedback = "get_export_limit_feedback"
ENTITY_SENSOR_set_export_limit_feedback = "set_export_limit_feedback"
ENTITY_SENSOR_set_datetime_feedback = "set_datetime_feedback"
ENTITY_SENSOR_get_telemetry_data_feedback = "get_telemetry_data_feedback"
ENTITY_SENSOR_reset_export_watchdog_feedback = "reset_export_watchdog_feedback"

# Button entities
ENTITY_BUTTON_reset_export_watchdog = "reset_export_watchdog"
ENTITY_BUTTON_set_datetime = "set_datetime"
ENTITY_BUTTON_export_enable = "export_enable"
ENTITY_BUTTON_export_disable = "export_disable"

# Switch entities
ENTITY_SWITCH_export_to_grid = "export_to_grid"

# Number entities
ENTITY_NUMBER_export_limit = "export_limit"

##############################################################################################################################
# Configuration keys #########################################################################################################
##############################################################################################################################

CONF_DEVICE_NAME = "device_name"
DEFAULT_DEVICE_NAME = "Device 1"

CONF_DEVICE_DISPLAY_NAME = "device_display_name"
DEFAULT_DEVICE_DISPLAY_NAME = "SEC1000"

CONF_INCLUDE_DEVICE_NAME_IN_ENTITY = "include_device_name_in_entity"
DEFAULT_INCLUDE_DEVICE_NAME_IN_ENTITY = True


# static constants for connection
DEFAULT_Port = 1234
DEFAULT_Timeout = 10
DEFAULT_Num_Retries = 1
DEFAULT_Retry_Waiting_Time = 5

# constants for connection settings
DEFAULT_SCAN_INTERVAL = 10
DEFAULT_HOST = "192.168.1.200"

# Bezpečnostná pauza medzi príkazmi odosielanými do zariadenia (v milisekundách)
DEFAULT_DEVICE_COMMAND_DELAY_MS = 1000

# constants for export settings
DEFAULT_MIN_EXPORT_LIMIT = 0.0
DEFAULT_MAX_EXPORT_LIMIT = 10.0
DEFAULT_TOTAL_CAPACITY = 20.0
DEFAULT_EXPORT_LIMIT_CONTROL_MODE = 3  # Default: Value control mode (3)
DEFAULT_SCAN_THREE_PHASES = True

# Export limit control modes
EXPORT_LIMIT_CONTROL_MODE_DISABLED = 0
EXPORT_LIMIT_CONTROL_MODE_DRED = 1
EXPORT_LIMIT_CONTROL_MODE_RCR = 2
EXPORT_LIMIT_CONTROL_MODE_VALUE = 3

# Export limit control mode options - reference keys from strings.json
EXPORT_LIMIT_CONTROL_MODE_OPTIONS = {
    EXPORT_LIMIT_CONTROL_MODE_DISABLED: "export_limit_mode_disabled",
    EXPORT_LIMIT_CONTROL_MODE_DRED: "export_limit_mode_dred",
    EXPORT_LIMIT_CONTROL_MODE_RCR: "export_limit_mode_rcr",
    EXPORT_LIMIT_CONTROL_MODE_VALUE: "export_limit_mode_value"
}

# Configuration keys
CONF_MIN_EXPORT_LIMIT = "min_export_limit"
CONF_MAX_EXPORT_LIMIT = "max_export_limit"
CONF_TOTAL_CAPACITY = "total_capacity"
CONF_EXPORT_LIMIT_CONTROL_MODE = "export_limit_control_mode"
CONF_SCAN_THREE_PHASES = "scan_three_phases"

# Returned feedback from Service / Method call
FEEDBACK_INIT = 1
FEEDBACK_NONE = 0
FEEDBACK_OK = 1
FEEDBACK_GENERAL_ERROR = 2
FEEDBACK_UNKNOWN_ERROR = 4
FEEDBACK_COMMUNICATION_ERROR_TIMEOUT = 8
FEEDBACK_COMMUNICATION_ERROR_UNEXPECTED_RETURNED_PACKET = 16
FEEDBACK_COMMUNICATION_ERROR_CRC = 32
FEEDBACK_COMMUNICATION_ERROR_SOCKET = 64
FEEDBACK_INVALID_INPUT_PARAMETER = 128
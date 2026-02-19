from __future__ import annotations
"""Integration for Goodwe SEC1000"""
"""Author: Jozef Moravcik"""
"""email: jozef.moravcik@moravcik.eu"""

""" goodwe_sec1000.py """

"""Coordinator for GoodWe SEC1000/S."""
import dataclasses
import json
import logging
import shelve
import socket
import struct
import sys
import time
import datetime
import asyncio
import os
from .const import *

LOGGER = logging.getLogger(__name__)

class Goodwe_SEC1000_Instance:
    """Integration"""
    
    def __init__(self, host: str) -> None:
        self._host = host
        self._telemetrydata = self.sec1000_Data()
        self.settings = self.Settings()
        self.settings.host = host
        self.connected: bool = False

        self.hass = None
        self._entry_id = None

        # Ukladaci priestor pre stavy senzorov
        self.sensor_states = {
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
        }

        # Entity ID budú nastavené po nastavení entry_id
        self.SENSOR_ENTITY_SENSOR_v1 = None
        self.SENSOR_ENTITY_SENSOR_v2 = None
        self.SENSOR_ENTITY_SENSOR_v3 = None
        self.SENSOR_ENTITY_SENSOR_i1 = None
        self.SENSOR_ENTITY_SENSOR_i2 = None
        self.SENSOR_ENTITY_SENSOR_i3 = None
        self.SENSOR_ENTITY_SENSOR_p1 = None
        self.SENSOR_ENTITY_SENSOR_p2 = None
        self.SENSOR_ENTITY_SENSOR_p3 = None
        self.SENSOR_ENTITY_SENSOR_meters_power = None
        self.SENSOR_ENTITY_SENSOR_inverters_power = None
        self.SENSOR_ENTITY_SENSOR_load_power = None
        self.SENSOR_ENTITY_SENSOR_export_limit = None
        self.SENSOR_ENTITY_SENSOR_export_state = None
        self.SENSOR_ENTITY_SENSOR_modul_started = None
        self.SENSOR_ENTITY_SENSOR_export_disable_feedback = None
        self.SENSOR_ENTITY_SENSOR_export_enable_feedback = None
        self.SENSOR_ENTITY_SENSOR_get_export_limit_feedback = None
        self.SENSOR_ENTITY_SENSOR_set_export_limit_feedback = None
        self.SENSOR_ENTITY_SENSOR_set_datetime_feedback = None
        self.SENSOR_ENTITY_SENSOR_get_telemetry_data_feedback = None
        self.SENSOR_ENTITY_SENSOR_reset_export_watchdog_feedback = None

        # Virtualne operacne premenne pre sensory
        self.sensor_v1 = None
        self.sensor_v2 = None
        self.sensor_v3 = None
        self.sensor_i1 = None
        self.sensor_i2 = None
        self.sensor_i3 = None
        self.sensor_p1 = None
        self.sensor_p2 = None
        self.sensor_p3 = None
        self.sensor_meters_power = None
        self.sensor_inverters_power = None
        self.sensor_load_power = None
        self.sensor_export_limit = None
        self.sensor_export_state = None
        self.sensor_modul_started = None
        self.sensor_export_disable_feedback = None
        self.sensor_export_enable_feedback = None
        self.sensor_get_export_limit_feedback = None
        self.sensor_set_export_limit_feedback = None
        self.sensor_set_datetime_feedback = None
        self.sensor_get_telemetry_data_feedback = None
        self.sensor_reset_export_watchdog_feedback = None

    def setup_entity_ids(self):
        """Setup entity IDs after entry_id is set."""
        if self._entry_id:
            from .const import sanitize_device_name
            device_name_sanitized = sanitize_device_name(self.settings.device_name)
            
            self.SENSOR_ENTITY_SENSOR_v1 = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_v1}"
            self.SENSOR_ENTITY_SENSOR_v2 = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_v2}"
            self.SENSOR_ENTITY_SENSOR_v3 = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_v3}"
            self.SENSOR_ENTITY_SENSOR_i1 = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_i1}"
            self.SENSOR_ENTITY_SENSOR_i2 = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_i2}"
            self.SENSOR_ENTITY_SENSOR_i3 = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_i3}"
            self.SENSOR_ENTITY_SENSOR_p1 = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_p1}"
            self.SENSOR_ENTITY_SENSOR_p2 = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_p2}"
            self.SENSOR_ENTITY_SENSOR_p3 = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_p3}"
            self.SENSOR_ENTITY_SENSOR_meters_power = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_meters_power}"
            self.SENSOR_ENTITY_SENSOR_inverters_power = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_inverters_power}"
            self.SENSOR_ENTITY_SENSOR_load_power = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_load_power}"
            self.SENSOR_ENTITY_SENSOR_export_limit = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_export_limit}"
            self.SENSOR_ENTITY_SENSOR_export_state = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_export_state}"
            self.SENSOR_ENTITY_SENSOR_modul_started = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_modul_started}"
            self.SENSOR_ENTITY_SENSOR_export_disable_feedback  = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_export_disable_feedback }"
            self.SENSOR_ENTITY_SENSOR_export_enable_feedback = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_export_enable_feedback}"
            self.SENSOR_ENTITY_SENSOR_get_export_limit_feedback = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_get_export_limit_feedback}"
            self.SENSOR_ENTITY_SENSOR_set_export_limit_feedback  = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_set_export_limit_feedback }"
            self.SENSOR_ENTITY_SENSOR_set_datetime_feedback = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_set_datetime_feedback}"
            self.SENSOR_ENTITY_SENSOR_get_telemetry_data_feedback = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_get_telemetry_data_feedback}"
            self.SENSOR_ENTITY_SENSOR_reset_export_watchdog_feedback = f"sensor.{ENTITY_PREFIX}_{device_name_sanitized}_{ENTITY_SENSOR_reset_export_watchdog_feedback}"
            
    @dataclasses.dataclass
    class sec1000_Data:
        v1: float = 0
        v2: float = 0
        v3: float = 0
        i1: float = 0
        i2: float = 0
        i3: float = 0
        p1: float = 0
        p2: float = 0
        p3: float = 0
        meters_power: float = 0
        inverters_power: float = 0
        load_power: float = 0               # spotreba spotrebicov + bateria (nabijanie / vybijanie)

    @dataclasses.dataclass
    class Settings:
        device_name: str = DEFAULT_DEVICE_NAME                                          # názov zariadenia
        include_device_name_in_entity: bool = DEFAULT_INCLUDE_DEVICE_NAME_IN_ENTITY     # zahrnúť názov zariadenia v entity
        device_display_name: str = DEFAULT_DEVICE_DISPLAY_NAME
        host: str = DEFAULT_HOST
        port: int = DEFAULT_Port
        timeout: float = DEFAULT_Timeout
        num_retries: int = DEFAULT_Num_Retries
        retry_waiting_time: int = DEFAULT_Retry_Waiting_Time
        min_export_limit: float = DEFAULT_MIN_EXPORT_LIMIT
        max_export_limit: float = DEFAULT_MAX_EXPORT_LIMIT
        total_capacity: float = DEFAULT_TOTAL_CAPACITY                          # total installed capacity
        export_limit_control_mode: int = DEFAULT_EXPORT_LIMIT_CONTROL_MODE      # 0=disabled, 1=DRED, 2=RCR, 3=Value (standard)
        scan_three_phases: bool = DEFAULT_SCAN_THREE_PHASES                     # Scan each phase value = x01 (False), Scan total of three phases value = x02 (True)
        ratio_ct: float = 0                                                     # Ratio of CR (measuring coils)
        export_limit: float = 0                                                 # Limit exportu do siete v kW
        export_state: bool = False                                              # Status exportu (True=enabled, False=disabled)
        modul_started: bool = False
        device_initialized: bool = False                                        # Flag indicating if initial communication with device succeeded

        export_disable_feedback: int = FEEDBACK_INIT                            # feedback from called method: export_disable
        export_enable_feedback: int = FEEDBACK_INIT                             # feedback from called method: import_disable
        get_export_limit_feedback: int = FEEDBACK_INIT                          # feedback from called method: get_export_limit
        set_export_limit_feedback: int = FEEDBACK_INIT                          # feedback from called method: set_export_limit_feedback
        set_datetime_feedback: int = FEEDBACK_INIT                              # feedback from called method: set_datetime_feedback
        get_telemetry_data_feedback: int = FEEDBACK_INIT                        # feedback from called method: get_telemetry_data_feedback
        reset_export_watchdog_feedback: int = FEEDBACK_INIT                     # feedback from called method: reset_export_watchdog_feedback

    def set_host(self, host: str = DEFAULT_HOST):
        self.settings.host = host

    def set_port(self, port: int = DEFAULT_Port):
        self.settings.port = port

# ******************************************************************************************
# ************************ System Started (initial functions) ******************************
# ******************************************************************************************

    def system_started(self) -> None:
        try:
            self.get_export_limit()
            LOGGER.info(f"System Started")
            LOGGER.info("Calling get_export_limit service after startup")
        except Exception as e:
            LOGGER.debug(f"Error during System Started")
#            time.sleep(wait_retry)

# ******************************************************************************************
# ********************** Get Telemetry Data ************************************************
# ******************************************************************************************

    def sec1000_get_telemetry_data(self, mode: str = "normal") -> bool:
        # sometimes the returned inverters_power field is 0 unexpectedly. We use a
        # cache file to store past results and if a 0 is returned then we replace
        # inverters_power with the last non 0 value stored in the cache.
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        sec1000_cache_folder = script_path+"/"+"__cache__"
        sec1000_cache_path = sec1000_cache_folder+"/"+"sec1000_cache"
        if not os.path.exists(sec1000_cache_folder):
            os.makedirs(sec1000_cache_folder)
        sec1000_cache_max_items = 10  # 0 or None to disable the cache
        sec1000_cache_max_age = 60  # max age of the cache in seconds
        num_retries = 1
        wait_retry = 5
        self.settings.get_telemetry_data_feedback = FEEDBACK_NONE
        for i in range(1, num_retries + 1):
            try:
                payload = b'\x00\x05\x01\x01\x0b\x00\x0d'
                rx_data = self.sec1000_tx_rx_data(payload, 49)
                if (len(rx_data)):
                    sdata = self.sec1000_Data()
                    sdata.v1 = round(0.1 * struct.unpack(">i", rx_data[0x05:0x09])[0],1)
                    sdata.v2 = round(0.1 * struct.unpack(">i", rx_data[0x09:0x0D])[0],1)
                    sdata.v3 = round(0.1 * struct.unpack(">i", rx_data[0x0D:0x11])[0],1)
                    sdata.i1 = round(1e-2 * struct.unpack(">i", rx_data[0x11:0x15])[0],2)
                    sdata.i2 = round(1e-2 * struct.unpack(">i", rx_data[0x15:0x19])[0],2)
                    sdata.i3 = round(1e-2 * struct.unpack(">i", rx_data[0x19:0x1D])[0],2)
                    sdata.p1 = round(1e-3 * struct.unpack(">i", rx_data[0x1D:0x21])[0],3)
                    sdata.p2 = round(1e-3 * struct.unpack(">i", rx_data[0x21:0x25])[0],3)
                    sdata.p3 = round(1e-3 * struct.unpack(">i", rx_data[0x25:0x29])[0],3)
                    sdata.meters_power = round(1e-3 * struct.unpack(">i", rx_data[0x29:0x2D])[0],3)
                    sdata.inverters_power = round(1e-3 * struct.unpack(">i", rx_data[0x2D:0x31])[0],3)
                    
                    # Calculate load power based on settings
                    if self.settings.scan_three_phases:
                        # Use all three phases
                        sdata.load_power = round((-1 * sdata.meters_power) + sdata.inverters_power,3)
                    else:
                        # Use the calculated value (as before)
                        sdata.load_power = round((-1 * sdata.meters_power) + sdata.inverters_power,3)

                    if mode=="debug":
                        print("Retry: " + "{:d}".format(i))
                    
                    if sec1000_cache_max_items is not None and sec1000_cache_max_items > 0:
                        self.fix_telemetry_data(sdata, sec1000_cache_path, sec1000_cache_max_items, sec1000_cache_max_age)
                        if mode=="debug":
                            self.sec1000_print_telemetry_data(sdata)
                        else:
                            self._telemetrydata = sdata

                    self.settings.get_telemetry_data_feedback |= FEEDBACK_OK
                    return True
                else:
                    self.settings.get_telemetry_data_feedback |= FEEDBACK_COMMUNICATION_ERROR_CRC
                    LOGGER.debug(f"CRC error when reading telemetry data")
                    return False
            
            except socket.error as e:
                self.settings.get_telemetry_data_feedback |= FEEDBACK_COMMUNICATION_ERROR_SOCKET
                LOGGER.debug(f"Socket error during telemetry read (try {i}/{num_retries}): {e}")
                time.sleep(wait_retry)
                return False

            except Exception as e:
                self.settings.get_telemetry_data_feedback |= FEEDBACK_UNKNOWN_ERROR
                LOGGER.debug(f"Error during telemetry read (try {i}/{num_retries}): {e}")
                time.sleep(wait_retry)
                return False

# ******************************************************************************************

    def fix_telemetry_data(self, sdata, cache_path="sec1000_cache", cache_max_items=10, cache_max_age=None):
        # If the received inverters_power field is 0 then it is replaced
        # with the last non 0 value in the cache and update the cache.
        cache_db = shelve.open(str(cache_path))
        
        # get data from the cache
        inverters_power_list = cache_db.get('inverters_power_list', [])
        load_power_list = cache_db.get('load_power_list', [])
        cache_time = cache_db.get('cache_time', None)

        # if the cache has exceeded the maximum age then reinitialize
        # inverters_power_list to an empty list
        if cache_max_age is not None and cache_time is not None:
            cache_age = time.time() - cache_time
            if (cache_age > cache_max_age):
                LOGGER.info(f"Reinitializing cache: cache age is {cache_age:.02f}, but the maximum set age is {cache_max_age:.02f}.")
                inverters_power_list = []
                load_power_list = []
                
        # Update data.inverters_power to last non 0 value from the cache
        inverters_power = sdata.inverters_power
        load_power = sdata.load_power
        if len(inverters_power_list) != 0 and inverters_power == 0.0:
            try:
                sdata.inverters_power = next(filter(lambda x: x != 0, reversed(inverters_power_list)))
                sdata.load_power = next(filter(lambda x: x != 0, reversed(load_power_list)))
                LOGGER.info(f"Possible bad inverted_powers value: a 0 was received, replaced by {sdata.inverters_power:0.3f} from the cache.")
            except StopIteration:
                pass

        # update cache
        inverters_power_list.append(inverters_power)
        inverters_power_list = inverters_power_list[-cache_max_items:]
        cache_db['inverters_power_list'] = inverters_power_list
        load_power_list.append(load_power)
        load_power_list = load_power_list[-cache_max_items:]
        cache_db['load_power_list'] = load_power_list
        cache_db['cache_time'] = time.time()
        cache_db.close()

# ******************************************************************************************
# **************************** Disable Export ***********************************************
# ******************************************************************************************
    """ simple function which disable export following re-setup values and parameters """

    def export_disable(self) -> bool:
        self.settings.export_disable_feedback = FEEDBACK_NONE
        LOGGER.info(
            f"export_disable: setting export limit to {self.settings.min_export_limit}kW, "
            f"control_mode={self.settings.export_limit_control_mode}"
        )
        if self.set_export_limit(self.settings.min_export_limit):
            self.settings.export_disable_feedback |= FEEDBACK_OK
            return True
        else:
            self.settings.export_disable_feedback |= FEEDBACK_UNKNOWN_ERROR
            return False

# ******************************************************************************************
# **************************** Enable Export ***********************************************
# ******************************************************************************************
    """ simple function which enable export following re-setup values and parameters """
    def export_enable(self) -> bool:
        self.settings.export_enable_feedback = FEEDBACK_NONE
        LOGGER.info(
            f"export_enable: setting export limit to {self.settings.max_export_limit}kW, "
            f"control_mode={self.settings.export_limit_control_mode}"
        )
        if self.set_export_limit(self.settings.max_export_limit):
            self.settings.export_enable_feedback |= FEEDBACK_OK
            return True
        else:
            self.settings.export_enable_feedback |= FEEDBACK_UNKNOWN_ERROR
            return False

# ******************************************************************************************
# **************************** Toggle Export ***********************************************
# ******************************************************************************************
    """ simple function which toggles export state """
    def export_toggle(self) -> bool:
        LOGGER.info(f"export_toggle: current export_state={self.settings.export_state}")
        # If export is currently enabled (True), disable it
        # If export is currently disabled (False), enable it
        if self.settings.export_state:
            LOGGER.info("export_toggle: disabling export")
            return self.export_disable()
        else:
            LOGGER.info("export_toggle: enabling export")
            return self.export_enable()

# ******************************************************************************************
# **************************** Get Export Status *******************************************
# ******************************************************************************************
    """ simple function which returns binary value of export status """
# TBD

# ******************************************************************************************
# ********************** Get Export Power Limit ********************************************
# ******************************************************************************************

    def get_export_limit(self) -> bool:
        """Get the export limit value and control mode from the device."""
        try:
            self.settings.get_export_limit_feedback = FEEDBACK_NONE
            if not self.settings.modul_started:
                self.settings.modul_started = True
                return False
            payload = b'\x00\x05\x01\x01\x43\x00\x45'
            rx_data = self.sec1000_tx_rx_data(payload, 18)
            if (len(rx_data)):
                self.settings.export_limit_control_mode = rx_data[5]
                self.settings.total_capacity = round(1e-3 * struct.unpack(">i", rx_data[0x06:0x0A])[0],1)
                self.settings.ratio_ct = round(0 * struct.unpack(">i", rx_data[0x0A:0x0E])[0],1)
                self.settings.export_limit = round(1e-3 * struct.unpack(">i", rx_data[0x0E:0x12])[0],1)

                if (self.settings.export_limit - self.settings.min_export_limit) < 0.01:
                    self.settings.export_state = False
                else:
                    self.settings.export_state = True

                LOGGER.info(f"Read Export Limit Data: Total capacity={self.settings.total_capacity}, " +
                            f"Export Power Limit={self.settings.export_limit}, " +
                            f"Export Limit Control Mode={self.settings.export_limit_control_mode}, " +
                            f"Ratio CT={self.settings.ratio_ct}, " +
                            f"Export State={self.settings.export_state}")

                self.settings.get_export_limit_feedback |= FEEDBACK_OK
                if not self.settings.device_initialized:
                    self.settings.device_initialized = True  # Mark device as initialized after first successful read
                    LOGGER.info("Device initialized successfully - buttons and switch are now available")
                return True
            else:
                self.settings.get_export_limit_feedback |= FEEDBACK_COMMUNICATION_ERROR_CRC
                LOGGER.debug("Failed to read export limit: No data received or CRC error")
                raise Exception("Failed to read export limit: No data received or CRC error")
                return False

        except socket.error as e:
            self.settings.get_export_limit_feedback |= FEEDBACK_COMMUNICATION_ERROR_SOCKET
            LOGGER.debug(f"Socket error during Export Power Limit read: {e}")
            raise
            return False

        except Exception as e:
            self.settings.get_export_limit_feedback |= FEEDBACK_UNKNOWN_ERROR
            LOGGER.debug(f"Error during Export Power Limit read: {e}")
            raise
            return False

# ******************************************************************************************
# ********************** Set Export Power Limit ********************************************
# ******************************************************************************************

    def set_export_limit(self, limit: float) -> bool:
        """Set the export limit value."""
        try:
            self.settings.set_export_limit_feedback = FEEDBACK_NONE
            if not self.settings.modul_started:
                return False

            # Apply min/max constraints if export limit control is enabled
            x = False
            if limit < self.settings.min_export_limit:
                LOGGER.warning(
                    f"Export limit {limit} kW below minimum {self.settings.min_export_limit} kW, adjusting"
                )
                limit = self.settings.min_export_limit
                x = True

            elif limit > self.settings.max_export_limit:
                LOGGER.warning(
                    f"Export limit {limit} kW above maximum {self.settings.max_export_limit} kW, adjusting"
                )
                limit = self.settings.max_export_limit
                x = True
            
            # Make sure the limit doesn't exceed total capacity
            if limit > self.settings.total_capacity:
                LOGGER.warning(
                    f"Export limit {limit} kW above total capacity {self.settings.total_capacity} kW, adjusting"
                )
                limit = self.settings.total_capacity
                x = True

            self.settings.export_limit = limit
            total_capacity = self.settings.total_capacity
            export_limit_control_mode = self.settings.export_limit_control_mode
            scan_three_phases_int = mode_value = 2 if self.settings.scan_three_phases else 1
            LOGGER.info(
                f"set_export_limit: limit={limit}kW, total_capacity={total_capacity}kW, "
                f"export_limit_control_mode={export_limit_control_mode}, scan_three_phases={self.settings.scan_three_phases}"
            )
            payload = bytearray(16)
            payload[0:5] = b'\x00\x0e\x01\x01\x42'
            payload[5:9] = struct.pack('!i', int(total_capacity * 1000))
            payload[9:13] = struct.pack('!i', int(limit * 1000))
            payload[13] = scan_three_phases_int
            payload[14:16] = self.get_goodwe_sec1000_crc(payload)
            rx_data = self.sec1000_tx_rx_data(payload, 6)
            if (limit - self.settings.min_export_limit) < 0.01:
                self.settings.export_state = False
            else:
                self.settings.export_state = True

            if (len(rx_data)):
                expected_bytes_1 = b'\x00\x06\x01\x01\x42\x06\x00\x4A'
                expected_bytes_2 = b'\x00\x06\x01\x01\x42\x15\x00\x59'

                if (rx_data == expected_bytes_1) or (rx_data == expected_bytes_2):
                    if self.set_export_limit_control_mode(export_limit_control_mode):
                        scan_three_phases_txt = ("ON" if self.settings.scan_three_phases else "OFF")
                        export_limit_control_mode_txt = ""
                        if self.settings.export_limit_control_mode == 0:
                            export_limit_control_mode_txt = "Deactivated"
                        elif self.settings.export_limit_control_mode == 1:
                            export_limit_control_mode_txt = "by DRED"
                        elif self.settings.export_limit_control_mode == 2:
                            export_limit_control_mode_txt = "by RCR"
                        elif self.settings.export_limit_control_mode == 3:
                            export_limit_control_mode_txt = "by VALUE"
                        LOGGER.info(f"Set Export Limit: Data sucessfully save to device. "
                                    f"Total capacity={total_capacity}, "
                                    f"Export Power Limit={limit}, "
                                    f"Sumary scan for all 3 phases={scan_three_phases_txt}, "
                                    f"Export Limit Control Mode={export_limit_control_mode_txt}, "
                                    f"Export State={self.settings.export_state}")
                        if x:
                            self.settings.set_export_limit_feedback |= FEEDBACK_OK | FEEDBACK_INVALID_INPUT_PARAMETER
                        else:
                            self.settings.set_export_limit_feedback |= FEEDBACK_OK
                        return True
                    else:
                        self.settings.set_export_limit_feedback |= FEEDBACK_GENERAL_ERROR
                        return False
                else:
                    self.settings.set_export_limit_feedback |= FEEDBACK_COMMUNICATION_ERROR_UNEXPECTED_RETURNED_PACKET
                    LOGGER.debug(f"Set Export Limit: Unexpected Error: The device sent an incorrect confirmation of the command execution.")
                    self.print_packet(rx_data)
                    return False
            else:
                self.settings.set_export_limit_feedback |= FEEDBACK_COMMUNICATION_ERROR_CRC
                LOGGER.debug("Failed to set export limit: CRC error")
                raise Exception("Failed to set export limit: CRC error")
                return False

        except (ValueError, TypeError) as e:
            self.settings.set_export_limit_feedback |= FEEDBACK_INVALID_INPUT_PARAMETER
            LOGGER.debug(f"Set Export Limit: Invalid export limit value: {limit}. Error: {e}")
            return False
        except socket.error as e:
            self.settings.set_export_limit_feedback |= FEEDBACK_COMMUNICATION_ERROR_SOCKET
            LOGGER.debug(f"Set Export Limit: Socket error: {e}")
            return False
        except Exception as e:
            self.settings.set_export_limit_feedback |= FEEDBACK_UNKNOWN_ERROR
            LOGGER.debug(f"Set Export Limit: Unexpected error: {e}")
            return False

# ******************************************************************************************
# ******************* Set Export Power Limit Controled by Value ****************************
# ******************************************************************************************

    def set_export_limit_control_mode(self, state: int) -> bool:
        success = 0
        if state == 3:
            if self.set_export_limit_on_dred(False): success += 1
            if self.set_export_limit_on_rcr(False): success += 1
            if self.set_export_limit_on_value(True): success += 1
        elif state == 2:
            if self.set_export_limit_on_value(False): success += 1
            if self.set_export_limit_on_dred(False): success += 1
            if self.set_export_limit_on_rcr(True): success += 1
        elif state == 1:
            if self.set_export_limit_on_value(False): success += 1
            if self.set_export_limit_on_rcr(False): success += 1
            if self.set_export_limit_on_dred(True): success += 1
        else:
            if self.set_export_limit_on_value(False): success += 1
            if self.set_export_limit_on_dred(False): success += 1
            if self.set_export_limit_on_rcr(False): success += 1
        if success == 3:
            return True
        else:
            return False

# ******************************************************************************************
# ******************* Set Export Power Limit Controled by Value ****************************
# ******************************************************************************************

    def set_export_limit_on_value(self, state: bool) -> bool:
        try:
            payload = bytearray(8)
            if state:
                payload[0:8] = b'\x00\x06\x01\x01\x40\x01\x00\x43'
            else:
                payload[0:8] = b'\x00\x06\x01\x01\x40\x02\x00\x44'

            rx_data = self.sec1000_tx_rx_data(payload, 6)
            if (len(rx_data)):
                expected_bytes_1 = b'\x00\x06\x01\x01\x40\x06\x00\x48'
                expected_bytes_2 = b'\x00\x06\x01\x01\x40\x15\x00\x57'
                if (rx_data == expected_bytes_1) or (rx_data == expected_bytes_2):
                    msgstate = "ON" if state else "OFF"
                    LOGGER.info(f"Set Export Limit Controlled by Value is {msgstate}. Data sucessfully save to device.")
                    return True
                else:
                    LOGGER.debug(f"Set Export Limit Controlled by Value: Unexpected Error: The device sent an incorrect confirmation of the command execution.")
                    self.print_packet(rx_data)
                    return False

        except socket.error as e:
            LOGGER.debug(f"Set Export Limit Controlled by Value: Socket error: {e}")
        except Exception as e:
            LOGGER.debug(f"Set Export Limit Controlled by Value: Unexpected error: {e}")

# ******************************************************************************************
# ******************* Set Export Power Limit Controled by DRED *****************************
# ******************************************************************************************

    def set_export_limit_on_dred(self, state: bool) -> bool:
        try:
            payload = bytearray(8)
            if state:
                payload[0:8] = b'\x00\x06\x01\x01\x33\x01\x00\x36'
            else:
                payload[0:8] = b'\x00\x06\x01\x01\x33\x02\x00\x37'

            rx_data = self.sec1000_tx_rx_data(payload, 6)
            if (len(rx_data)):
                expected_bytes_1 = b'\x00\x06\x01\x01\x33\x06\x00\x3B'
                expected_bytes_2 = b'\x00\x06\x01\x01\x33\x15\x00\x4A'
                if (rx_data == expected_bytes_1) or (rx_data == expected_bytes_2):
                    msgstate = "ON" if state else "OFF"
                    LOGGER.info(f"Set Export Limit Controlled by DRED is {msgstate}. Data sucessfully save to device.")
                    return True
                else:
                    LOGGER.debug(f"Set Export Limit Controlled by DRED: Unexpected Error: The device sent an incorrect confirmation of the command execution.")
                    self.print_packet(rx_data)
                    return False

        except socket.error as e:
            LOGGER.debug(f"Set Export Limit Controlled by DRED: Socket error: {e}")
        except Exception as e:
            LOGGER.debug(f"Set Export Limit Controlled by DRED: Unexpected error: {e}")

# ******************************************************************************************
# ******************* Set Export Power Limit Controled by RCR ******************************
# ******************************************************************************************

    def set_export_limit_on_rcr(self, state: bool) -> bool:
        try:
            payload = bytearray(8)
            if state:
                payload[0:8] = b'\x00\x06\x01\x01\x28\x01\x00\x2b'
            else:
                payload[0:8] = b'\x00\x06\x01\x01\x28\x02\x00\x2c'

            rx_data = self.sec1000_tx_rx_data(payload, 6)
            if (len(rx_data)):
                expected_bytes_1 = b'\x00\x06\x01\x01\x28\x06\x00\x30'
                expected_bytes_2 = b'\x00\x06\x01\x01\x28\x15\x00\x3F'
                if (rx_data == expected_bytes_1) or (rx_data == expected_bytes_2):
                    msgstate = "ON" if state else "OFF"
                    LOGGER.info(f"Set Export Limit Controlled by RCR is {msgstate}. Data sucessfully save to device.")
                    return True
                else:
                    LOGGER.debug(f"Set Export Limit Controlled by RCR: Unexpected Error: The device sent an incorrect confirmation of the command execution.")
                    self.print_packet(rx_data)
                    return False

        except socket.error as e:
            LOGGER.debug(f"Set Export Limit Controlled by RCR: Socket error: {e}")
        except Exception as e:
            LOGGER.debug(f"Set Export Limit Controlled by RCR: Unexpected error: {e}")

# ******************************************************************************************
# ************************** Set Date/Time *************************************************
# ******************************************************************************************

    def set_datetime(self) -> bool:
        self.settings.set_datetime_feedback = FEEDBACK_NONE
        """Set current datetime in the device"""
        try:
            t = time.localtime()
            payload = bytearray([
                0x00,
                0x0C,             # Packet Length
                0x01,
                0x01,
                0x05,             # Command
                t.tm_year % 100,  # Rok (posledné 2 číslice)
                t.tm_mon,         # Mesiac
                0x00,             # Statická hodnota 0
                t.tm_mday,        # Deň
                t.tm_hour,        # Hodina
                t.tm_min,         # Minúta
                t.tm_sec,         # Sekunda
                0x00,             # Empty CRC
                0x00              # Empty CRC
            ])
            payload[12:14] = self.get_goodwe_sec1000_crc(payload)
            rx_data = self.sec1000_tx_rx_data(payload, 6)
            if (len(rx_data)):
                expected_bytes_1 = b'\x00\x06\x01\x01\x05\x03\x00\x0A'
                expected_bytes_2 = b'\x00\x06\x01\x01\x05\x15\x00\x00'  # NEOVERENY !!!
                if (rx_data == expected_bytes_1) or (rx_data == expected_bytes_2):
                    self.settings.set_datetime_feedback |= FEEDBACK_OK
                    LOGGER.info(f"Date Time sucessfully saved to the device. ")
                    return True
                else:
                    self.settings.set_datetime_feedback |= FEEDBACK_COMMUNICATION_ERROR_UNEXPECTED_RETURNED_PACKET
                    LOGGER.debug(f"Set Date Time: Unexpected Error: The device sent an incorrect confirmation of the command execution.")
                    self.print_packet(rx_data)
                    return False
            else:
                self.settings.set_datetime_feedback |= FEEDBACK_COMMUNICATION_ERROR_CRC
                LOGGER.debug("Failed to set date time: CRC error")
                raise Exception("Failed to set date time: CRC error")
                return False

        except socket.error as e:
            self.settings.set_datetime_feedback |= FEEDBACK_COMMUNICATION_ERROR_SOCKET
            LOGGER.debug(f"Set Date Time: Socket error: {e}")
            return False
        except Exception as e:
            self.settings.set_datetime_feedback |= FEEDBACK_UNKNOWN_ERROR
            LOGGER.debug(f"Set Date Time: Unexpected error: {e}")
            return False

# ******************************************************************************************
# ************************** Reset Export Watchdog *****************************************
# ******************************************************************************************

    def reset_export_watchdog(self) -> bool:
        """Reset Export Watchdog"""
        try:
            self.settings.reset_export_watchdog_feedback = FEEDBACK_NONE
            ret = 0
            if self.set_export_limit_control_mode(EXPORT_LIMIT_CONTROL_MODE_DISABLED):
                ret += 1
            time.sleep(5)
            if self.set_export_limit_control_mode(self.settings.export_limit_control_mode):
                ret += 1
                time.sleep(1)
                if self.set_export_limit(self.settings.export_limit):
                    ret += 1
            if ret == 3:
                self.settings.reset_export_watchdog_feedback |= FEEDBACK_OK
                LOGGER.info(f"Reset Export Watchdog has been performed sucessfully")
                return True
            else:
                self.settings.reset_export_watchdog_feedback |= FEEDBACK_UNKNOWN_ERROR
                LOGGER.debug(f"Reset Export Watchdog: Unexpected error")
                return False

        except Exception as e:
            self.settings.reset_export_watchdog_feedback |= FEEDBACK_UNKNOWN_ERROR
            LOGGER.debug(f"Reset Export Watchdog: Unexpected error: {e}")
            return False

# ******************************************************************************************
# ********************** Tools *************************************************************
# ******************************************************************************************

    def sec1000_tx_rx_data(self, payload:bytes = b'', response_length:int = 0) -> bytes:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.settings.timeout)
                s.connect((self.settings.host, self.settings.port))
                s.sendall(payload)
                data = b''
                while len(data) < 7:
                    recv_data = s.recv(7 - len(data))
                    data += recv_data
                    if len(recv_data) == 0:
                        raise Exception("Bad response: no data received.")
                if response_length >= 0:
                    response_size = data[6]
                    if response_size != response_length:
                        raise Exception(f"Bad response size! Expected size: {response_length}, Received size: {response_size}.")
                    
                    data += s.recv(response_size)
                    rx_payload = data[5:len(data)]
                    if self.check_goodwe_sec1000_crc(rx_payload):
                        return rx_payload
                    else:
                        LOGGER.debug(f"CRC error on packet: " + ' '.join([f'{byte:02X}' for byte in rx_payload]))
                        return b""
                else:
                    return b""

        except Exception as e:
            LOGGER.debug(f"Error in sec1000_tx_rx_data: {e}")
            raise

# ******************************************************************************************

    # Validation of CRC for SEC1000/S
    def check_goodwe_sec1000_crc(self, crcdata) -> bool:
        crc = self.get_goodwe_sec1000_crc(crcdata)
        return (crc[0] == crcdata[len(crcdata)-2]) and (crc[1] == crcdata[len(crcdata)-1])

# ******************************************************************************************

    # Calculation CRC for SEC1000/S
    def get_goodwe_sec1000_crc(self, crcdata):
        byte_sum = sum(crcdata[2:len(crcdata)-2]) & 0xFFFF
        crc = bytearray(2)
        crc[1] = byte_sum & 0xFF
        crc[0] = (byte_sum >> 8) & 0xFF
        return bytes(crc)

# ******************************************************************************************
    # Set of Methods for reseting feedbacks

    def reset_get_telemetry_data_feedback(self) -> None:
        self.settings.get_telemetry_data_feedback = FEEDBACK_NONE

    def reset_export_disable_feedback(self) -> None:
        self.settings.export_disable_feedback = FEEDBACK_NONE

    def reset_export_enable_feedback(self) -> None:
        self.settings.export_enable_feedback = FEEDBACK_NONE

    def reset_get_export_limit_feedback(self) -> None:
        self.settings.get_export_limit_feedback = FEEDBACK_NONE

    def reset_set_export_limit_feedback(self) -> None:
        self.settings.set_export_limit_feedback = FEEDBACK_NONE

    def reset_set_datetime_feedback(self) -> None:
        self.settings.set_datetime_feedback = FEEDBACK_NONE

    def reset_reset_export_watchdog_feedback(self) -> None:
        self.settings.reset_export_watchdog_feedback = FEEDBACK_NONE

# ******************************************************************************************

    # Print data in a HEX format
    # example: self.print_packet(rx_data)
    def print_packet(self, pckdata):
        LOGGER.warning(f"Packet data: " + " ".join(f"{byte:02X}" for byte in pckdata))

# ******************************************************************************************

    def sec1000_print_telemetry_data(self, sdata: sec1000_Data):
        print("\n* * * * * * * SEC1000 - TELEMETRY DATA * * * * * * * \n")
        print("Voltage on P1:     " + "{:.01f}".format(sdata.v1) + "V")
        print("Voltage on P2:     " + "{:.01f}".format(sdata.v2) + "V")
        print("Voltage on P3:     " + "{:.01f}".format(sdata.v3) + "V")
        print("")
        print("Current on P1:     " + "{:.02f}".format(sdata.i1) + "A")
        print("Current on P2:     " + "{:.02f}".format(sdata.i2) + "A")
        print("Current on P3:     " + "{:.02f}".format(sdata.i3) + "A")
        print("")
        print("Meter Power on P1: " + "{:.03f}".format((sdata.v1 * sdata.i1)/1000) + "kW")
        print("Meter Power on P2: " + "{:.03f}".format((sdata.v2 * sdata.i2)/1000) + "kW")
        print("Meter Power on P3: " + "{:.03f}".format((sdata.v3 * sdata.i3)/1000) + "kW")
        print("Meter Power ???:   " + "{:.03f}".format(((sdata.v1 * sdata.i1)+(sdata.v2 * sdata.i2)+(sdata.v3 * sdata.i3))/1000) + "kW")
        print("")
        print("Meter Power on P1: " + "{:.03f}".format(sdata.p1) + "kW")
        print("Meter Power on P2: " + "{:.03f}".format(sdata.p2) + "kW")
        print("Meter Power on P3: " + "{:.03f}".format(sdata.p3) + "kW")
        print("Meter Power:       " + "{:.03f}".format((sdata.p1+sdata.p2+sdata.p3)) + "kW")
        print("")
        print("Meters Power:      " + "{:.03f}".format(sdata.meters_power) + "kW")
        print("Inverters Power:   " + "{:.03f}".format(sdata.inverters_power) + "kW")
        print("Load Power:        " + "{:.03f}".format(sdata.load_power) + "kW")
        print("")
        print("Export limit:      " + "{:.03f}".format(self.settings.export_limit) + "kW")
        print("Min Export limit:  " + "{:.03f}".format(self.settings.min_export_limit) + "kW")
        print("Max Export limit:  " + "{:.03f}".format(self.settings.max_export_limit) + "kW")
        print("Total Capacity:    " + "{:.03f}".format(self.settings.total_capacity) + "kW")
        
        # Export limit control mode with text label
        mode_text = "Unknown"
        if self.settings.export_limit_control_mode == 0:
            mode_text = "Disabled"
        elif self.settings.export_limit_control_mode == 1:
            mode_text = "DRED"
        elif self.settings.export_limit_control_mode == 2:
            mode_text = "RCR"
        elif self.settings.export_limit_control_mode == 3:
            mode_text = "Value"
            
        print(f"Export Control Mode: {self.settings.export_limit_control_mode} ({mode_text})")
        print("Scan Three Phases: " + ("Enabled" if self.settings.scan_three_phases else "Disabled"))
        print("")

# ******************************************************************************************
# ********* for testing and debugging purpose **********************************************
# ******************************************************************************************

def SEC1000S_read_telemetry_data(host: str = DEFAULT_HOST):
    SEC1000S = Goodwe_SEC1000_Instance(host)
    SEC1000S.sec1000_get_telemetry_data(mode="normal")

def SEC1000S_test_telemetry_data(host: str = DEFAULT_HOST):
    SEC1000S = Goodwe_SEC1000_Instance(host)
    SEC1000S.sec1000_get_telemetry_data(mode="debug")

#SEC1000S_test_telemetry_data("192.168.1.200")
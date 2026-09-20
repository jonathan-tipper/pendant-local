from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EnumC11639b(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DISCHARGING: _ClassVar[EnumC11639b]
    CHARGING: _ClassVar[EnumC11639b]
    FULL: _ClassVar[EnumC11639b]

class Usb(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    USB_DISCONNECTED: _ClassVar[Usb]
    USB_CONNECTED: _ClassVar[Usb]

class Button(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BUTTON_NOT_PRESSED: _ClassVar[Button]
    BUTTON_SHORT_PRESS: _ClassVar[Button]
    BUTTON_LONG_PRESS: _ClassVar[Button]
    BUTTON_DOUBLE_PRESS: _ClassVar[Button]
    BUTTON_SHORT_AND_SUPER_LONG_PRESS: _ClassVar[Button]

class EnumC11642e(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BUTTON: _ClassVar[EnumC11642e]
    AMBIENT_SOUND: _ClassVar[EnumC11642e]

class EnumC11643f(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NOT_RECORDING: _ClassVar[EnumC11643f]
    RECORDING: _ClassVar[EnumC11643f]
    LISTENING: _ClassVar[EnumC11643f]

class EnumC11645h(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BAND_UNSPECIFIED: _ClassVar[EnumC11645h]
    FREQ_2_4_GHZ: _ClassVar[EnumC11645h]
    FREQ_5_GHZ: _ClassVar[EnumC11645h]
    FREQ_6_GHZ: _ClassVar[EnumC11645h]

class EnumC11646i(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MFP_UNSPECIFIED: _ClassVar[EnumC11646i]
    DISABLED: _ClassVar[EnumC11646i]
    REQUIRED: _ClassVar[EnumC11646i]

class EnumC11647j(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NONE: _ClassVar[EnumC11647j]
    WPA2_PSK: _ClassVar[EnumC11647j]
    WPA2_PSK_SHA256: _ClassVar[EnumC11647j]
    WPA3_SAE: _ClassVar[EnumC11647j]
    WAPI: _ClassVar[EnumC11647j]
    EAP: _ClassVar[EnumC11647j]
    WEP: _ClassVar[EnumC11647j]
    WPA_PSK: _ClassVar[EnumC11647j]
    WPA_AUTO_PERSONAL: _ClassVar[EnumC11647j]

class Wifi(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WIFI_DISCONNECTED: _ClassVar[Wifi]
    WIFI_CONNECTING: _ClassVar[Wifi]
    WIFI_CONNECTED: _ClassVar[Wifi]
    WIFI_INIT_ERROR: _ClassVar[Wifi]
DISCHARGING: EnumC11639b
CHARGING: EnumC11639b
FULL: EnumC11639b
USB_DISCONNECTED: Usb
USB_CONNECTED: Usb
BUTTON_NOT_PRESSED: Button
BUTTON_SHORT_PRESS: Button
BUTTON_LONG_PRESS: Button
BUTTON_DOUBLE_PRESS: Button
BUTTON_SHORT_AND_SUPER_LONG_PRESS: Button
BUTTON: EnumC11642e
AMBIENT_SOUND: EnumC11642e
NOT_RECORDING: EnumC11643f
RECORDING: EnumC11643f
LISTENING: EnumC11643f
BAND_UNSPECIFIED: EnumC11645h
FREQ_2_4_GHZ: EnumC11645h
FREQ_5_GHZ: EnumC11645h
FREQ_6_GHZ: EnumC11645h
MFP_UNSPECIFIED: EnumC11646i
DISABLED: EnumC11646i
REQUIRED: EnumC11646i
NONE: EnumC11647j
WPA2_PSK: EnumC11647j
WPA2_PSK_SHA256: EnumC11647j
WPA3_SAE: EnumC11647j
WAPI: EnumC11647j
EAP: EnumC11647j
WEP: EnumC11647j
WPA_PSK: EnumC11647j
WPA_AUTO_PERSONAL: EnumC11647j
WIFI_DISCONNECTED: Wifi
WIFI_CONNECTING: Wifi
WIFI_CONNECTED: Wifi
WIFI_INIT_ERROR: Wifi

class BatteryStatus(_message.Message):
    __slots__ = ("state", "voltage", "current", "temperature", "soc", "capacity", "over_operating_temperature", "under_operating_temperature", "usb_state")
    STATE_FIELD_NUMBER: _ClassVar[int]
    VOLTAGE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    SOC_FIELD_NUMBER: _ClassVar[int]
    CAPACITY_FIELD_NUMBER: _ClassVar[int]
    OVER_OPERATING_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    UNDER_OPERATING_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    USB_STATE_FIELD_NUMBER: _ClassVar[int]
    state: EnumC11639b
    voltage: int
    current: int
    temperature: int
    soc: int
    capacity: int
    over_operating_temperature: bool
    under_operating_temperature: bool
    usb_state: Usb
    def __init__(self, state: _Optional[_Union[EnumC11639b, str]] = ..., voltage: _Optional[int] = ..., current: _Optional[int] = ..., temperature: _Optional[int] = ..., soc: _Optional[int] = ..., capacity: _Optional[int] = ..., over_operating_temperature: _Optional[bool] = ..., under_operating_temperature: _Optional[bool] = ..., usb_state: _Optional[_Union[Usb, str]] = ...) -> None: ...

class ButtonStatus(_message.Message):
    __slots__ = ("button_event", "physical_button", "num_short_presses_since_boot", "num_long_presses_since_boot", "num_double_presses_since_boot", "button_event_absolute_timestamp_ms", "short_press_duration_ms", "long_press_duration_ms")
    BUTTON_EVENT_FIELD_NUMBER: _ClassVar[int]
    PHYSICAL_BUTTON_FIELD_NUMBER: _ClassVar[int]
    NUM_SHORT_PRESSES_SINCE_BOOT_FIELD_NUMBER: _ClassVar[int]
    NUM_LONG_PRESSES_SINCE_BOOT_FIELD_NUMBER: _ClassVar[int]
    NUM_DOUBLE_PRESSES_SINCE_BOOT_FIELD_NUMBER: _ClassVar[int]
    BUTTON_EVENT_ABSOLUTE_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    SHORT_PRESS_DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    LONG_PRESS_DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    button_event: Button
    physical_button: bool
    num_short_presses_since_boot: int
    num_long_presses_since_boot: int
    num_double_presses_since_boot: int
    button_event_absolute_timestamp_ms: int
    short_press_duration_ms: int
    long_press_duration_ms: int
    def __init__(self, button_event: _Optional[_Union[Button, str]] = ..., physical_button: _Optional[bool] = ..., num_short_presses_since_boot: _Optional[int] = ..., num_long_presses_since_boot: _Optional[int] = ..., num_double_presses_since_boot: _Optional[int] = ..., button_event_absolute_timestamp_ms: _Optional[int] = ..., short_press_duration_ms: _Optional[int] = ..., long_press_duration_ms: _Optional[int] = ...) -> None: ...

class RecordingStatus(_message.Message):
    __slots__ = ("recording_state", "recording_source", "vad_level")
    RECORDING_STATE_FIELD_NUMBER: _ClassVar[int]
    RECORDING_SOURCE_FIELD_NUMBER: _ClassVar[int]
    VAD_LEVEL_FIELD_NUMBER: _ClassVar[int]
    recording_state: EnumC11643f
    recording_source: EnumC11642e
    vad_level: int
    def __init__(self, recording_state: _Optional[_Union[EnumC11643f, str]] = ..., recording_source: _Optional[_Union[EnumC11642e, str]] = ..., vad_level: _Optional[int] = ...) -> None: ...

class UsbStatus(_message.Message):
    __slots__ = ("state",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    state: Usb
    def __init__(self, state: _Optional[_Union[Usb, str]] = ...) -> None: ...

class WiFiCredentials(_message.Message):
    __slots__ = ("ssid", "security", "password", "bssid", "band", "channel", "mfp", "priority")
    SSID_FIELD_NUMBER: _ClassVar[int]
    SECURITY_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    BSSID_FIELD_NUMBER: _ClassVar[int]
    BAND_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    MFP_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    ssid: str
    security: EnumC11647j
    password: bytes
    bssid: bytes
    band: EnumC11645h
    channel: int
    mfp: EnumC11646i
    priority: int
    def __init__(self, ssid: _Optional[str] = ..., security: _Optional[_Union[EnumC11647j, str]] = ..., password: _Optional[bytes] = ..., bssid: _Optional[bytes] = ..., band: _Optional[_Union[EnumC11645h, str]] = ..., channel: _Optional[int] = ..., mfp: _Optional[_Union[EnumC11646i, str]] = ..., priority: _Optional[int] = ...) -> None: ...

class WifiStatus(_message.Message):
    __slots__ = ("state", "rssi", "uptime", "ssid")
    STATE_FIELD_NUMBER: _ClassVar[int]
    RSSI_FIELD_NUMBER: _ClassVar[int]
    UPTIME_FIELD_NUMBER: _ClassVar[int]
    SSID_FIELD_NUMBER: _ClassVar[int]
    state: Wifi
    rssi: int
    uptime: int
    ssid: str
    def __init__(self, state: _Optional[_Union[Wifi, str]] = ..., rssi: _Optional[int] = ..., uptime: _Optional[int] = ..., ssid: _Optional[str] = ...) -> None: ...

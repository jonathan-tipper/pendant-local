import real_time_audio_pb2 as _real_time_audio_pb2
import shared_pb2 as _shared_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PendantSyncMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PENDANT_SYNC_MODE_OFF: _ClassVar[PendantSyncMode]
    PENDANT_SYNC_MODE_BLE_BATCH: _ClassVar[PendantSyncMode]
    PENDANT_SYNC_MODE_BLE_REALTIME: _ClassVar[PendantSyncMode]
    PENDANT_SYNC_MODE_WIFI: _ClassVar[PendantSyncMode]

class ServerCommandErrorCategory(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SERVER_COMMAND_ERROR_CATEGORY_NONE: _ClassVar[ServerCommandErrorCategory]
    SERVER_COMMAND_ERROR_CATEGORY_FAILED_TO_EXECUTE: _ClassVar[ServerCommandErrorCategory]

class BeamformDirection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BEAMFORM_DIRECTION_FRONT: _ClassVar[BeamformDirection]
    BEAMFORM_DIRECTION_LEFT: _ClassVar[BeamformDirection]
    BEAMFORM_DIRECTION_BACK: _ClassVar[BeamformDirection]
    BEAMFORM_DIRECTION_RIGHT: _ClassVar[BeamformDirection]

class FlashPageError(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    FLASH_PAGE_ERROR_NONE: _ClassVar[FlashPageError]
    FLASH_PAGE_ERROR_CRC: _ClassVar[FlashPageError]
    FLASH_PAGE_ERROR_IO: _ClassVar[FlashPageError]

class DeviceIngestType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DEVICE_INGEST_TYPE_UNSPECIFIED: _ClassVar[DeviceIngestType]
    DEVICE_INGEST_TYPE_REAL_TIME: _ClassVar[DeviceIngestType]
    DEVICE_INGEST_TYPE_BATCH: _ClassVar[DeviceIngestType]
    DEVICE_INGEST_TYPE_COMMAND: _ClassVar[DeviceIngestType]

class EnumC11446e(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    IDLE: _ClassVar[EnumC11446e]
    PREPARING_FOR_UPDATE: _ClassVar[EnumC11446e]
    UPLOADING_IMAGE: _ClassVar[EnumC11446e]
PENDANT_SYNC_MODE_OFF: PendantSyncMode
PENDANT_SYNC_MODE_BLE_BATCH: PendantSyncMode
PENDANT_SYNC_MODE_BLE_REALTIME: PendantSyncMode
PENDANT_SYNC_MODE_WIFI: PendantSyncMode
SERVER_COMMAND_ERROR_CATEGORY_NONE: ServerCommandErrorCategory
SERVER_COMMAND_ERROR_CATEGORY_FAILED_TO_EXECUTE: ServerCommandErrorCategory
BEAMFORM_DIRECTION_FRONT: BeamformDirection
BEAMFORM_DIRECTION_LEFT: BeamformDirection
BEAMFORM_DIRECTION_BACK: BeamformDirection
BEAMFORM_DIRECTION_RIGHT: BeamformDirection
FLASH_PAGE_ERROR_NONE: FlashPageError
FLASH_PAGE_ERROR_CRC: FlashPageError
FLASH_PAGE_ERROR_IO: FlashPageError
DEVICE_INGEST_TYPE_UNSPECIFIED: DeviceIngestType
DEVICE_INGEST_TYPE_REAL_TIME: DeviceIngestType
DEVICE_INGEST_TYPE_BATCH: DeviceIngestType
DEVICE_INGEST_TYPE_COMMAND: DeviceIngestType
IDLE: EnumC11446e
PREPARING_FOR_UPDATE: EnumC11446e
UPLOADING_IMAGE: EnumC11446e

class AddWifiCredentials(_message.Message):
    __slots__ = ("cred",)
    CRED_FIELD_NUMBER: _ClassVar[int]
    cred: _shared_pb2.WiFiCredentials
    def __init__(self, cred: _Optional[_Union[_shared_pb2.WiFiCredentials, _Mapping]] = ...) -> None: ...

class AuthenticateIngestMessage(_message.Message):
    __slots__ = ("ingest_token", "language")
    INGEST_TOKEN_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    ingest_token: str
    language: str
    def __init__(self, ingest_token: _Optional[str] = ..., language: _Optional[str] = ...) -> None: ...

class AuthenticateSuccessAckMessage(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class BatchIngestRequest(_message.Message):
    __slots__ = ("messages", "ble_identifier")
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    BLE_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    messages: _containers.RepeatedCompositeFieldContainer[PendantAllMsg]
    ble_identifier: str
    def __init__(self, messages: _Optional[_Iterable[_Union[PendantAllMsg, _Mapping]]] = ..., ble_identifier: _Optional[str] = ...) -> None: ...

class ClearPendantStorage(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ConnectToBackend(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ConnectToWifi(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DeleteFlashPage(_message.Message):
    __slots__ = ("older_than_or_equal_to_index",)
    OLDER_THAN_OR_EQUAL_TO_INDEX_FIELD_NUMBER: _ClassVar[int]
    older_than_or_equal_to_index: int
    def __init__(self, older_than_or_equal_to_index: _Optional[int] = ...) -> None: ...

class DeviceInfoMsg(_message.Message):
    __slots__ = ("device_id", "serial_num", "firmware_ver", "storage_version", "storage_instance", "storage_run", "wifi_mac_address1", "wifi_mac_address2", "ble_mac_address", "oldest_flash_page", "newest_flash_page", "battery_percent", "debug_features", "device_status", "device_audio_encryption_pub_key", "factory_reset_id")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    SERIAL_NUM_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_VER_FIELD_NUMBER: _ClassVar[int]
    STORAGE_VERSION_FIELD_NUMBER: _ClassVar[int]
    STORAGE_INSTANCE_FIELD_NUMBER: _ClassVar[int]
    STORAGE_RUN_FIELD_NUMBER: _ClassVar[int]
    WIFI_MAC_ADDRESS1_FIELD_NUMBER: _ClassVar[int]
    WIFI_MAC_ADDRESS2_FIELD_NUMBER: _ClassVar[int]
    BLE_MAC_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    OLDEST_FLASH_PAGE_FIELD_NUMBER: _ClassVar[int]
    NEWEST_FLASH_PAGE_FIELD_NUMBER: _ClassVar[int]
    BATTERY_PERCENT_FIELD_NUMBER: _ClassVar[int]
    DEBUG_FEATURES_FIELD_NUMBER: _ClassVar[int]
    DEVICE_STATUS_FIELD_NUMBER: _ClassVar[int]
    DEVICE_AUDIO_ENCRYPTION_PUB_KEY_FIELD_NUMBER: _ClassVar[int]
    FACTORY_RESET_ID_FIELD_NUMBER: _ClassVar[int]
    device_id: int
    serial_num: str
    firmware_ver: str
    storage_version: int
    storage_instance: int
    storage_run: int
    wifi_mac_address1: bytes
    wifi_mac_address2: bytes
    ble_mac_address: bytes
    oldest_flash_page: int
    newest_flash_page: int
    battery_percent: int
    debug_features: SetDebugFeatures
    device_status: DeviceStatus
    device_audio_encryption_pub_key: bytes
    factory_reset_id: int
    def __init__(self, device_id: _Optional[int] = ..., serial_num: _Optional[str] = ..., firmware_ver: _Optional[str] = ..., storage_version: _Optional[int] = ..., storage_instance: _Optional[int] = ..., storage_run: _Optional[int] = ..., wifi_mac_address1: _Optional[bytes] = ..., wifi_mac_address2: _Optional[bytes] = ..., ble_mac_address: _Optional[bytes] = ..., oldest_flash_page: _Optional[int] = ..., newest_flash_page: _Optional[int] = ..., battery_percent: _Optional[int] = ..., debug_features: _Optional[_Union[SetDebugFeatures, _Mapping]] = ..., device_status: _Optional[_Union[DeviceStatus, _Mapping]] = ..., device_audio_encryption_pub_key: _Optional[bytes] = ..., factory_reset_id: _Optional[int] = ...) -> None: ...

class DeviceStatus(_message.Message):
    __slots__ = ("wifi_status", "server_info", "vad_threshold", "led_brightness", "storage_state", "sync_mode", "recording_status", "has_all_fields", "battery_status")
    WIFI_STATUS_FIELD_NUMBER: _ClassVar[int]
    SERVER_INFO_FIELD_NUMBER: _ClassVar[int]
    VAD_THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    LED_BRIGHTNESS_FIELD_NUMBER: _ClassVar[int]
    STORAGE_STATE_FIELD_NUMBER: _ClassVar[int]
    SYNC_MODE_FIELD_NUMBER: _ClassVar[int]
    RECORDING_STATUS_FIELD_NUMBER: _ClassVar[int]
    HAS_ALL_FIELDS_FIELD_NUMBER: _ClassVar[int]
    BATTERY_STATUS_FIELD_NUMBER: _ClassVar[int]
    wifi_status: _shared_pb2.WifiStatus
    server_info: SetServerInfo
    vad_threshold: SetVADThreshold
    led_brightness: int
    storage_state: StorageState
    sync_mode: PendantSyncMode
    recording_status: _shared_pb2.RecordingStatus
    has_all_fields: bool
    battery_status: _shared_pb2.BatteryStatus
    def __init__(self, wifi_status: _Optional[_Union[_shared_pb2.WifiStatus, _Mapping]] = ..., server_info: _Optional[_Union[SetServerInfo, _Mapping]] = ..., vad_threshold: _Optional[_Union[SetVADThreshold, _Mapping]] = ..., led_brightness: _Optional[int] = ..., storage_state: _Optional[_Union[StorageState, _Mapping]] = ..., sync_mode: _Optional[_Union[PendantSyncMode, str]] = ..., recording_status: _Optional[_Union[_shared_pb2.RecordingStatus, _Mapping]] = ..., has_all_fields: _Optional[bool] = ..., battery_status: _Optional[_Union[_shared_pb2.BatteryStatus, _Mapping]] = ...) -> None: ...

class DisconnectWifi(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DownloadFlashPages(_message.Message):
    __slots__ = ("batch_mode_enabled", "real_time_mode_enabled")
    BATCH_MODE_ENABLED_FIELD_NUMBER: _ClassVar[int]
    REAL_TIME_MODE_ENABLED_FIELD_NUMBER: _ClassVar[int]
    batch_mode_enabled: bool
    real_time_mode_enabled: bool
    def __init__(self, batch_mode_enabled: _Optional[bool] = ..., real_time_mode_enabled: _Optional[bool] = ...) -> None: ...

class FactoryResetPendant(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetDeviceInfo(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetDeviceStatus(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PendantAllMsg(_message.Message):
    __slots__ = ("response_data", "device_info", "storage_buffer", "set_current_time_response", "authenticate_ingest", "device_status", "battery_status", "button_status", "real_time_audio_data", "real_time_audio_ack")
    RESPONSE_DATA_FIELD_NUMBER: _ClassVar[int]
    DEVICE_INFO_FIELD_NUMBER: _ClassVar[int]
    STORAGE_BUFFER_FIELD_NUMBER: _ClassVar[int]
    SET_CURRENT_TIME_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    AUTHENTICATE_INGEST_FIELD_NUMBER: _ClassVar[int]
    DEVICE_STATUS_FIELD_NUMBER: _ClassVar[int]
    BATTERY_STATUS_FIELD_NUMBER: _ClassVar[int]
    BUTTON_STATUS_FIELD_NUMBER: _ClassVar[int]
    REAL_TIME_AUDIO_DATA_FIELD_NUMBER: _ClassVar[int]
    REAL_TIME_AUDIO_ACK_FIELD_NUMBER: _ClassVar[int]
    response_data: ResponseData
    device_info: DeviceInfoMsg
    storage_buffer: StorageBufferMsg
    set_current_time_response: SetCurrentTimeResponse
    authenticate_ingest: AuthenticateIngestMessage
    device_status: DeviceStatus
    battery_status: _shared_pb2.BatteryStatus
    button_status: _shared_pb2.ButtonStatus
    real_time_audio_data: _real_time_audio_pb2.RealTimeAudioData
    real_time_audio_ack: _real_time_audio_pb2.RealTimeAudioAck
    def __init__(self, response_data: _Optional[_Union[ResponseData, _Mapping]] = ..., device_info: _Optional[_Union[DeviceInfoMsg, _Mapping]] = ..., storage_buffer: _Optional[_Union[StorageBufferMsg, _Mapping]] = ..., set_current_time_response: _Optional[_Union[SetCurrentTimeResponse, _Mapping]] = ..., authenticate_ingest: _Optional[_Union[AuthenticateIngestMessage, _Mapping]] = ..., device_status: _Optional[_Union[DeviceStatus, _Mapping]] = ..., battery_status: _Optional[_Union[_shared_pb2.BatteryStatus, _Mapping]] = ..., button_status: _Optional[_Union[_shared_pb2.ButtonStatus, _Mapping]] = ..., real_time_audio_data: _Optional[_Union[_real_time_audio_pb2.RealTimeAudioData, _Mapping]] = ..., real_time_audio_ack: _Optional[_Union[_real_time_audio_pb2.RealTimeAudioAck, _Mapping]] = ...) -> None: ...

class PrepareForFirmwareUpdate(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PushOpusFrames(_message.Message):
    __slots__ = ("opus_packet", "frame_sizes", "first_frame_index")
    OPUS_PACKET_FIELD_NUMBER: _ClassVar[int]
    FRAME_SIZES_FIELD_NUMBER: _ClassVar[int]
    FIRST_FRAME_INDEX_FIELD_NUMBER: _ClassVar[int]
    opus_packet: bytes
    frame_sizes: _containers.RepeatedScalarFieldContainer[int]
    first_frame_index: int
    def __init__(self, opus_packet: _Optional[bytes] = ..., frame_sizes: _Optional[_Iterable[int]] = ..., first_frame_index: _Optional[int] = ...) -> None: ...

class RequestData(_message.Message):
    __slots__ = ("request_id", "do_not_ack")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    DO_NOT_ACK_FIELD_NUMBER: _ClassVar[int]
    request_id: int
    do_not_ack: bool
    def __init__(self, request_id: _Optional[int] = ..., do_not_ack: _Optional[bool] = ...) -> None: ...

class ResetDevice(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ResponseData(_message.Message):
    __slots__ = ("request_id", "error")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    request_id: int
    error: ServerCommandRequestError
    def __init__(self, request_id: _Optional[int] = ..., error: _Optional[_Union[ServerCommandRequestError, _Mapping]] = ...) -> None: ...

class ServerCommandMsg(_message.Message):
    __slots__ = ("request_data", "set_manufacturing_mode", "set_mac_address", "set_led", "add_wifi_credentials", "set_ble_pair", "set_current_time", "delete_flash_page", "download_flash_pages", "set_ingest_token", "factory_reset_pendant", "reset_device", "authenticate_success_ack", "set_device_name", "get_device_info", "unpair_bluetooth", "set_debug_features", "start_recording", "stop_recording", "connect_to_wifi", "connect_to_backend", "get_device_status", "set_server_info", "disconnect_wifi", "set_vad_threshold", "clear_pendant_storage", "set_led_brightness", "set_device_on_shipping_mode", "set_audio_encryption_server_public_key", "prepare_for_firmware_update", "sync_firmware_update_state", "push_opus_frames", "real_time_audio_ack", "real_time_audio_data")
    REQUEST_DATA_FIELD_NUMBER: _ClassVar[int]
    SET_MANUFACTURING_MODE_FIELD_NUMBER: _ClassVar[int]
    SET_MAC_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    SET_LED_FIELD_NUMBER: _ClassVar[int]
    ADD_WIFI_CREDENTIALS_FIELD_NUMBER: _ClassVar[int]
    SET_BLE_PAIR_FIELD_NUMBER: _ClassVar[int]
    SET_CURRENT_TIME_FIELD_NUMBER: _ClassVar[int]
    DELETE_FLASH_PAGE_FIELD_NUMBER: _ClassVar[int]
    DOWNLOAD_FLASH_PAGES_FIELD_NUMBER: _ClassVar[int]
    SET_INGEST_TOKEN_FIELD_NUMBER: _ClassVar[int]
    FACTORY_RESET_PENDANT_FIELD_NUMBER: _ClassVar[int]
    RESET_DEVICE_FIELD_NUMBER: _ClassVar[int]
    AUTHENTICATE_SUCCESS_ACK_FIELD_NUMBER: _ClassVar[int]
    SET_DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    GET_DEVICE_INFO_FIELD_NUMBER: _ClassVar[int]
    UNPAIR_BLUETOOTH_FIELD_NUMBER: _ClassVar[int]
    SET_DEBUG_FEATURES_FIELD_NUMBER: _ClassVar[int]
    START_RECORDING_FIELD_NUMBER: _ClassVar[int]
    STOP_RECORDING_FIELD_NUMBER: _ClassVar[int]
    CONNECT_TO_WIFI_FIELD_NUMBER: _ClassVar[int]
    CONNECT_TO_BACKEND_FIELD_NUMBER: _ClassVar[int]
    GET_DEVICE_STATUS_FIELD_NUMBER: _ClassVar[int]
    SET_SERVER_INFO_FIELD_NUMBER: _ClassVar[int]
    DISCONNECT_WIFI_FIELD_NUMBER: _ClassVar[int]
    SET_VAD_THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    CLEAR_PENDANT_STORAGE_FIELD_NUMBER: _ClassVar[int]
    SET_LED_BRIGHTNESS_FIELD_NUMBER: _ClassVar[int]
    SET_DEVICE_ON_SHIPPING_MODE_FIELD_NUMBER: _ClassVar[int]
    SET_AUDIO_ENCRYPTION_SERVER_PUBLIC_KEY_FIELD_NUMBER: _ClassVar[int]
    PREPARE_FOR_FIRMWARE_UPDATE_FIELD_NUMBER: _ClassVar[int]
    SYNC_FIRMWARE_UPDATE_STATE_FIELD_NUMBER: _ClassVar[int]
    PUSH_OPUS_FRAMES_FIELD_NUMBER: _ClassVar[int]
    REAL_TIME_AUDIO_ACK_FIELD_NUMBER: _ClassVar[int]
    REAL_TIME_AUDIO_DATA_FIELD_NUMBER: _ClassVar[int]
    request_data: RequestData
    set_manufacturing_mode: SetManufacturingMode
    set_mac_address: SetMacAddress
    set_led: SetLed
    add_wifi_credentials: AddWifiCredentials
    set_ble_pair: SetBLEPair
    set_current_time: SetCurrentTime
    delete_flash_page: DeleteFlashPage
    download_flash_pages: DownloadFlashPages
    set_ingest_token: SetIngestToken
    factory_reset_pendant: FactoryResetPendant
    reset_device: ResetDevice
    authenticate_success_ack: AuthenticateSuccessAckMessage
    set_device_name: SetDeviceName
    get_device_info: GetDeviceInfo
    unpair_bluetooth: UnpairBluetooth
    set_debug_features: SetDebugFeatures
    start_recording: StartRecording
    stop_recording: StopRecording
    connect_to_wifi: ConnectToWifi
    connect_to_backend: ConnectToBackend
    get_device_status: GetDeviceStatus
    set_server_info: SetServerInfo
    disconnect_wifi: DisconnectWifi
    set_vad_threshold: SetVADThreshold
    clear_pendant_storage: ClearPendantStorage
    set_led_brightness: SetLEDBrightness
    set_device_on_shipping_mode: SetDeviceOnShippingMode
    set_audio_encryption_server_public_key: SetServerPublicKey
    prepare_for_firmware_update: PrepareForFirmwareUpdate
    sync_firmware_update_state: SyncFirmwareUpdateState
    push_opus_frames: PushOpusFrames
    real_time_audio_ack: _real_time_audio_pb2.RealTimeAudioAck
    real_time_audio_data: _real_time_audio_pb2.RealTimeAudioData
    def __init__(self, request_data: _Optional[_Union[RequestData, _Mapping]] = ..., set_manufacturing_mode: _Optional[_Union[SetManufacturingMode, _Mapping]] = ..., set_mac_address: _Optional[_Union[SetMacAddress, _Mapping]] = ..., set_led: _Optional[_Union[SetLed, _Mapping]] = ..., add_wifi_credentials: _Optional[_Union[AddWifiCredentials, _Mapping]] = ..., set_ble_pair: _Optional[_Union[SetBLEPair, _Mapping]] = ..., set_current_time: _Optional[_Union[SetCurrentTime, _Mapping]] = ..., delete_flash_page: _Optional[_Union[DeleteFlashPage, _Mapping]] = ..., download_flash_pages: _Optional[_Union[DownloadFlashPages, _Mapping]] = ..., set_ingest_token: _Optional[_Union[SetIngestToken, _Mapping]] = ..., factory_reset_pendant: _Optional[_Union[FactoryResetPendant, _Mapping]] = ..., reset_device: _Optional[_Union[ResetDevice, _Mapping]] = ..., authenticate_success_ack: _Optional[_Union[AuthenticateSuccessAckMessage, _Mapping]] = ..., set_device_name: _Optional[_Union[SetDeviceName, _Mapping]] = ..., get_device_info: _Optional[_Union[GetDeviceInfo, _Mapping]] = ..., unpair_bluetooth: _Optional[_Union[UnpairBluetooth, _Mapping]] = ..., set_debug_features: _Optional[_Union[SetDebugFeatures, _Mapping]] = ..., start_recording: _Optional[_Union[StartRecording, _Mapping]] = ..., stop_recording: _Optional[_Union[StopRecording, _Mapping]] = ..., connect_to_wifi: _Optional[_Union[ConnectToWifi, _Mapping]] = ..., connect_to_backend: _Optional[_Union[ConnectToBackend, _Mapping]] = ..., get_device_status: _Optional[_Union[GetDeviceStatus, _Mapping]] = ..., set_server_info: _Optional[_Union[SetServerInfo, _Mapping]] = ..., disconnect_wifi: _Optional[_Union[DisconnectWifi, _Mapping]] = ..., set_vad_threshold: _Optional[_Union[SetVADThreshold, _Mapping]] = ..., clear_pendant_storage: _Optional[_Union[ClearPendantStorage, _Mapping]] = ..., set_led_brightness: _Optional[_Union[SetLEDBrightness, _Mapping]] = ..., set_device_on_shipping_mode: _Optional[_Union[SetDeviceOnShippingMode, _Mapping]] = ..., set_audio_encryption_server_public_key: _Optional[_Union[SetServerPublicKey, _Mapping]] = ..., prepare_for_firmware_update: _Optional[_Union[PrepareForFirmwareUpdate, _Mapping]] = ..., sync_firmware_update_state: _Optional[_Union[SyncFirmwareUpdateState, _Mapping]] = ..., push_opus_frames: _Optional[_Union[PushOpusFrames, _Mapping]] = ..., real_time_audio_ack: _Optional[_Union[_real_time_audio_pb2.RealTimeAudioAck, _Mapping]] = ..., real_time_audio_data: _Optional[_Union[_real_time_audio_pb2.RealTimeAudioData, _Mapping]] = ...) -> None: ...

class ServerCommandRequestError(_message.Message):
    __slots__ = ("category", "error_message")
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    category: ServerCommandErrorCategory
    error_message: str
    def __init__(self, category: _Optional[_Union[ServerCommandErrorCategory, str]] = ..., error_message: _Optional[str] = ...) -> None: ...

class SetBLEPair(_message.Message):
    __slots__ = ("ble_pair",)
    BLE_PAIR_FIELD_NUMBER: _ClassVar[int]
    ble_pair: str
    def __init__(self, ble_pair: _Optional[str] = ...) -> None: ...

class SetCurrentTime(_message.Message):
    __slots__ = ("unix_timestamp_ms",)
    UNIX_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    unix_timestamp_ms: int
    def __init__(self, unix_timestamp_ms: _Optional[int] = ...) -> None: ...

class SetCurrentTimeResponse(_message.Message):
    __slots__ = ("rtc_sync_relative_timestamp", "invalid_rtc_reset_count", "rtc_sync_session_number")
    RTC_SYNC_RELATIVE_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    INVALID_RTC_RESET_COUNT_FIELD_NUMBER: _ClassVar[int]
    RTC_SYNC_SESSION_NUMBER_FIELD_NUMBER: _ClassVar[int]
    rtc_sync_relative_timestamp: int
    invalid_rtc_reset_count: int
    rtc_sync_session_number: int
    def __init__(self, rtc_sync_relative_timestamp: _Optional[int] = ..., invalid_rtc_reset_count: _Optional[int] = ..., rtc_sync_session_number: _Optional[int] = ...) -> None: ...

class SetDebugFeatures(_message.Message):
    __slots__ = ("should_output_raw_omni_data", "should_output_raw_pdm_data", "should_output_raw_beamforming", "should_manually_beamform", "manual_beamform_direction", "allow_recording_on_usb", "print_stopwatch_times", "print_ble_connection_info", "show_debug_led", "should_use_omni_and_skip_beamforming")
    SHOULD_OUTPUT_RAW_OMNI_DATA_FIELD_NUMBER: _ClassVar[int]
    SHOULD_OUTPUT_RAW_PDM_DATA_FIELD_NUMBER: _ClassVar[int]
    SHOULD_OUTPUT_RAW_BEAMFORMING_FIELD_NUMBER: _ClassVar[int]
    SHOULD_MANUALLY_BEAMFORM_FIELD_NUMBER: _ClassVar[int]
    MANUAL_BEAMFORM_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    ALLOW_RECORDING_ON_USB_FIELD_NUMBER: _ClassVar[int]
    PRINT_STOPWATCH_TIMES_FIELD_NUMBER: _ClassVar[int]
    PRINT_BLE_CONNECTION_INFO_FIELD_NUMBER: _ClassVar[int]
    SHOW_DEBUG_LED_FIELD_NUMBER: _ClassVar[int]
    SHOULD_USE_OMNI_AND_SKIP_BEAMFORMING_FIELD_NUMBER: _ClassVar[int]
    should_output_raw_omni_data: bool
    should_output_raw_pdm_data: bool
    should_output_raw_beamforming: bool
    should_manually_beamform: bool
    manual_beamform_direction: BeamformDirection
    allow_recording_on_usb: bool
    print_stopwatch_times: bool
    print_ble_connection_info: bool
    show_debug_led: bool
    should_use_omni_and_skip_beamforming: bool
    def __init__(self, should_output_raw_omni_data: _Optional[bool] = ..., should_output_raw_pdm_data: _Optional[bool] = ..., should_output_raw_beamforming: _Optional[bool] = ..., should_manually_beamform: _Optional[bool] = ..., manual_beamform_direction: _Optional[_Union[BeamformDirection, str]] = ..., allow_recording_on_usb: _Optional[bool] = ..., print_stopwatch_times: _Optional[bool] = ..., print_ble_connection_info: _Optional[bool] = ..., show_debug_led: _Optional[bool] = ..., should_use_omni_and_skip_beamforming: _Optional[bool] = ...) -> None: ...

class SetDeviceName(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class SetDeviceOnShippingMode(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SetIngestToken(_message.Message):
    __slots__ = ("ingest_token",)
    INGEST_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ingest_token: str
    def __init__(self, ingest_token: _Optional[str] = ...) -> None: ...

class SetLed(_message.Message):
    __slots__ = ("red_enabled", "green_enabled", "blue_enabled")
    RED_ENABLED_FIELD_NUMBER: _ClassVar[int]
    GREEN_ENABLED_FIELD_NUMBER: _ClassVar[int]
    BLUE_ENABLED_FIELD_NUMBER: _ClassVar[int]
    red_enabled: bool
    green_enabled: bool
    blue_enabled: bool
    def __init__(self, red_enabled: _Optional[bool] = ..., green_enabled: _Optional[bool] = ..., blue_enabled: _Optional[bool] = ...) -> None: ...

class SetLEDBrightness(_message.Message):
    __slots__ = ("brightness",)
    BRIGHTNESS_FIELD_NUMBER: _ClassVar[int]
    brightness: int
    def __init__(self, brightness: _Optional[int] = ...) -> None: ...

class SetMacAddress(_message.Message):
    __slots__ = ("mac_address1", "mac_address2")
    MAC_ADDRESS1_FIELD_NUMBER: _ClassVar[int]
    MAC_ADDRESS2_FIELD_NUMBER: _ClassVar[int]
    mac_address1: bytes
    mac_address2: bytes
    def __init__(self, mac_address1: _Optional[bytes] = ..., mac_address2: _Optional[bytes] = ...) -> None: ...

class SetManufacturingMode(_message.Message):
    __slots__ = ("enabled",)
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    enabled: bool
    def __init__(self, enabled: _Optional[bool] = ...) -> None: ...

class SetServerInfo(_message.Message):
    __slots__ = ("server_url", "server_port")
    SERVER_URL_FIELD_NUMBER: _ClassVar[int]
    SERVER_PORT_FIELD_NUMBER: _ClassVar[int]
    server_url: str
    server_port: str
    def __init__(self, server_url: _Optional[str] = ..., server_port: _Optional[str] = ...) -> None: ...

class SetServerPublicKey(_message.Message):
    __slots__ = ("server_pub_key",)
    SERVER_PUB_KEY_FIELD_NUMBER: _ClassVar[int]
    server_pub_key: bytes
    def __init__(self, server_pub_key: _Optional[bytes] = ...) -> None: ...

class SetVADThreshold(_message.Message):
    __slots__ = ("vad_threshold_ms",)
    VAD_THRESHOLD_MS_FIELD_NUMBER: _ClassVar[int]
    vad_threshold_ms: int
    def __init__(self, vad_threshold_ms: _Optional[int] = ...) -> None: ...

class StartRecording(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StopRecording(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StorageBufferMsg(_message.Message):
    __slots__ = ("ingest_type", "session", "run", "seq", "index", "flash_page", "flash_page_error")
    INGEST_TYPE_FIELD_NUMBER: _ClassVar[int]
    SESSION_FIELD_NUMBER: _ClassVar[int]
    RUN_FIELD_NUMBER: _ClassVar[int]
    SEQ_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    FLASH_PAGE_FIELD_NUMBER: _ClassVar[int]
    FLASH_PAGE_ERROR_FIELD_NUMBER: _ClassVar[int]
    ingest_type: DeviceIngestType
    session: int
    run: int
    seq: int
    index: int
    flash_page: bytes
    flash_page_error: FlashPageError
    def __init__(self, ingest_type: _Optional[_Union[DeviceIngestType, str]] = ..., session: _Optional[int] = ..., run: _Optional[int] = ..., seq: _Optional[int] = ..., index: _Optional[int] = ..., flash_page: _Optional[bytes] = ..., flash_page_error: _Optional[_Union[FlashPageError, str]] = ...) -> None: ...

class StorageState(_message.Message):
    __slots__ = ("oldest_flash_page", "newest_flash_page", "current_storage_session", "free_capture_pages", "total_capture_pages")
    OLDEST_FLASH_PAGE_FIELD_NUMBER: _ClassVar[int]
    NEWEST_FLASH_PAGE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_STORAGE_SESSION_FIELD_NUMBER: _ClassVar[int]
    FREE_CAPTURE_PAGES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_CAPTURE_PAGES_FIELD_NUMBER: _ClassVar[int]
    oldest_flash_page: int
    newest_flash_page: int
    current_storage_session: int
    free_capture_pages: int
    total_capture_pages: int
    def __init__(self, oldest_flash_page: _Optional[int] = ..., newest_flash_page: _Optional[int] = ..., current_storage_session: _Optional[int] = ..., free_capture_pages: _Optional[int] = ..., total_capture_pages: _Optional[int] = ...) -> None: ...

class SyncFirmwareUpdateState(_message.Message):
    __slots__ = ("state",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    state: EnumC11446e
    def __init__(self, state: _Optional[_Union[EnumC11446e, str]] = ...) -> None: ...

class UnpairBluetooth(_message.Message):
    __slots__ = ("do_not_reset_device",)
    DO_NOT_RESET_DEVICE_FIELD_NUMBER: _ClassVar[int]
    do_not_reset_device: bool
    def __init__(self, do_not_reset_device: _Optional[bool] = ...) -> None: ...

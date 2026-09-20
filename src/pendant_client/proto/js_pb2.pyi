import common_pb2 as _common_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AppLifecycleState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN: _ClassVar[AppLifecycleState]
    FOREGROUND: _ClassVar[AppLifecycleState]
    BACKGROUND: _ClassVar[AppLifecycleState]

class BluetoothDisconnectedReason(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NOT_PAIRED: _ClassVar[BluetoothDisconnectedReason]
    UNAVAILABLE: _ClassVar[BluetoothDisconnectedReason]
    USER_UNPAIRED_IN_SETTINGS: _ClassVar[BluetoothDisconnectedReason]
    CONNECTION_FAILURE: _ClassVar[BluetoothDisconnectedReason]
    BLUETOOTH_DISABLED: _ClassVar[BluetoothDisconnectedReason]
    BLUETOOTH_NEEDS_TOGGLE: _ClassVar[BluetoothDisconnectedReason]
    BLUETOOTH_PERMISSION_DENIED: _ClassVar[BluetoothDisconnectedReason]

class BluetoothState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BLUETOOTH_STATE_UNKNOWN: _ClassVar[BluetoothState]
    BLUETOOTH_STATE_POWERED_OFF: _ClassVar[BluetoothState]
    BLUETOOTH_STATE_POWERED_ON: _ClassVar[BluetoothState]
    BLUETOOTH_STATE_UNSUPPORTED: _ClassVar[BluetoothState]
    BLUETOOTH_STATE_UNAUTHORIZED: _ClassVar[BluetoothState]
    BLUETOOTH_STATE_RESETTING: _ClassVar[BluetoothState]

class FirmwareUpdateStep(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    FIRMWARE_UPDATE_STEP_UNSPECIFIED: _ClassVar[FirmwareUpdateStep]
    FIRMWARE_UPDATE_STEP_IDLE: _ClassVar[FirmwareUpdateStep]
    FIRMWARE_UPDATE_STEP_SYNCING: _ClassVar[FirmwareUpdateStep]
    FIRMWARE_UPDATE_STEP_DOWNLOADING: _ClassVar[FirmwareUpdateStep]
    FIRMWARE_UPDATE_STEP_VALIDATING: _ClassVar[FirmwareUpdateStep]
    FIRMWARE_UPDATE_STEP_SENDING_TO_DEVICE: _ClassVar[FirmwareUpdateStep]
    FIRMWARE_UPDATE_STEP_INSTALLING: _ClassVar[FirmwareUpdateStep]
    FIRMWARE_UPDATE_STEP_RESTARTING_DEVICE: _ClassVar[FirmwareUpdateStep]
    FIRMWARE_UPDATE_STEP_COMPLETED: _ClassVar[FirmwareUpdateStep]
    FIRMWARE_UPDATE_STEP_FAILED: _ClassVar[FirmwareUpdateStep]
    FIRMWARE_UPDATE_STEP_CANCELLED: _ClassVar[FirmwareUpdateStep]
UNKNOWN: AppLifecycleState
FOREGROUND: AppLifecycleState
BACKGROUND: AppLifecycleState
NOT_PAIRED: BluetoothDisconnectedReason
UNAVAILABLE: BluetoothDisconnectedReason
USER_UNPAIRED_IN_SETTINGS: BluetoothDisconnectedReason
CONNECTION_FAILURE: BluetoothDisconnectedReason
BLUETOOTH_DISABLED: BluetoothDisconnectedReason
BLUETOOTH_NEEDS_TOGGLE: BluetoothDisconnectedReason
BLUETOOTH_PERMISSION_DENIED: BluetoothDisconnectedReason
BLUETOOTH_STATE_UNKNOWN: BluetoothState
BLUETOOTH_STATE_POWERED_OFF: BluetoothState
BLUETOOTH_STATE_POWERED_ON: BluetoothState
BLUETOOTH_STATE_UNSUPPORTED: BluetoothState
BLUETOOTH_STATE_UNAUTHORIZED: BluetoothState
BLUETOOTH_STATE_RESETTING: BluetoothState
FIRMWARE_UPDATE_STEP_UNSPECIFIED: FirmwareUpdateStep
FIRMWARE_UPDATE_STEP_IDLE: FirmwareUpdateStep
FIRMWARE_UPDATE_STEP_SYNCING: FirmwareUpdateStep
FIRMWARE_UPDATE_STEP_DOWNLOADING: FirmwareUpdateStep
FIRMWARE_UPDATE_STEP_VALIDATING: FirmwareUpdateStep
FIRMWARE_UPDATE_STEP_SENDING_TO_DEVICE: FirmwareUpdateStep
FIRMWARE_UPDATE_STEP_INSTALLING: FirmwareUpdateStep
FIRMWARE_UPDATE_STEP_RESTARTING_DEVICE: FirmwareUpdateStep
FIRMWARE_UPDATE_STEP_COMPLETED: FirmwareUpdateStep
FIRMWARE_UPDATE_STEP_FAILED: FirmwareUpdateStep
FIRMWARE_UPDATE_STEP_CANCELLED: FirmwareUpdateStep

class AnalyticsTrackMessage(_message.Message):
    __slots__ = ("event_name", "properties_json")
    EVENT_NAME_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_JSON_FIELD_NUMBER: _ClassVar[int]
    event_name: str
    properties_json: str
    def __init__(self, event_name: _Optional[str] = ..., properties_json: _Optional[str] = ...) -> None: ...

class BluetoothPermissionDeniedMessage(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class BluetoothReceivedFragmentGroupMessage(_message.Message):
    __slots__ = ("fragment_count", "largest_session_id", "newest_flash_page", "newest_chunk_timestamp_ms")
    FRAGMENT_COUNT_FIELD_NUMBER: _ClassVar[int]
    LARGEST_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    NEWEST_FLASH_PAGE_FIELD_NUMBER: _ClassVar[int]
    NEWEST_CHUNK_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    fragment_count: int
    largest_session_id: int
    newest_flash_page: int
    newest_chunk_timestamp_ms: int
    def __init__(self, fragment_count: _Optional[int] = ..., largest_session_id: _Optional[int] = ..., newest_flash_page: _Optional[int] = ..., newest_chunk_timestamp_ms: _Optional[int] = ...) -> None: ...

class BluetoothReceivedFragmentMessage(_message.Message):
    __slots__ = ("index", "data", "peripheral_id")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    PERIPHERAL_ID_FIELD_NUMBER: _ClassVar[int]
    index: int
    data: bytes
    peripheral_id: str
    def __init__(self, index: _Optional[int] = ..., data: _Optional[bytes] = ..., peripheral_id: _Optional[str] = ...) -> None: ...

class BluetoothStateDidChange(_message.Message):
    __slots__ = ("state",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    state: BluetoothState
    def __init__(self, state: _Optional[_Union[BluetoothState, str]] = ...) -> None: ...

class CheckForUpdateMessage(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class FirmwareUpdateState(_message.Message):
    __slots__ = ("step", "step_details", "is_update_in_progress")
    STEP_FIELD_NUMBER: _ClassVar[int]
    STEP_DETAILS_FIELD_NUMBER: _ClassVar[int]
    IS_UPDATE_IN_PROGRESS_FIELD_NUMBER: _ClassVar[int]
    step: FirmwareUpdateStep
    step_details: str
    is_update_in_progress: bool
    def __init__(self, step: _Optional[_Union[FirmwareUpdateStep, str]] = ..., step_details: _Optional[str] = ..., is_update_in_progress: _Optional[bool] = ...) -> None: ...

class FragmentDidUploadMessage(_message.Message):
    __slots__ = ("file_name",)
    FILE_NAME_FIELD_NUMBER: _ClassVar[int]
    file_name: str
    def __init__(self, file_name: _Optional[str] = ...) -> None: ...

class FragmentStorageSizeDidChange(_message.Message):
    __slots__ = ("size",)
    SIZE_FIELD_NUMBER: _ClassVar[int]
    size: int
    def __init__(self, size: _Optional[int] = ...) -> None: ...

class GetIngestTokenMessage(_message.Message):
    __slots__ = ("peripheral_id",)
    PERIPHERAL_ID_FIELD_NUMBER: _ClassVar[int]
    peripheral_id: str
    def __init__(self, peripheral_id: _Optional[str] = ...) -> None: ...

class GetIngestTokenResponse(_message.Message):
    __slots__ = ("ingest_token",)
    INGEST_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ingest_token: str
    def __init__(self, ingest_token: _Optional[str] = ...) -> None: ...

class JSBridgeMessage(_message.Message):
    __slots__ = ("bluetooth_received_fragment", "get_ingest_token", "app_lifecycle_did_change", "firmware_update_state_did_change", "fragment_storage_size_did_change", "bluetooth_received_fragment_group", "fragment_did_upload", "user_defaults", "check_for_update", "pendant_status", "pendant_characteristic_value", "analytics_track", "bluetooth_permission_denied")
    BLUETOOTH_RECEIVED_FRAGMENT_FIELD_NUMBER: _ClassVar[int]
    GET_INGEST_TOKEN_FIELD_NUMBER: _ClassVar[int]
    APP_LIFECYCLE_DID_CHANGE_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_UPDATE_STATE_DID_CHANGE_FIELD_NUMBER: _ClassVar[int]
    FRAGMENT_STORAGE_SIZE_DID_CHANGE_FIELD_NUMBER: _ClassVar[int]
    BLUETOOTH_RECEIVED_FRAGMENT_GROUP_FIELD_NUMBER: _ClassVar[int]
    FRAGMENT_DID_UPLOAD_FIELD_NUMBER: _ClassVar[int]
    USER_DEFAULTS_FIELD_NUMBER: _ClassVar[int]
    CHECK_FOR_UPDATE_FIELD_NUMBER: _ClassVar[int]
    PENDANT_STATUS_FIELD_NUMBER: _ClassVar[int]
    PENDANT_CHARACTERISTIC_VALUE_FIELD_NUMBER: _ClassVar[int]
    ANALYTICS_TRACK_FIELD_NUMBER: _ClassVar[int]
    BLUETOOTH_PERMISSION_DENIED_FIELD_NUMBER: _ClassVar[int]
    bluetooth_received_fragment: BluetoothReceivedFragmentMessage
    get_ingest_token: GetIngestTokenMessage
    app_lifecycle_did_change: AppLifecycleState
    firmware_update_state_did_change: FirmwareUpdateState
    fragment_storage_size_did_change: FragmentStorageSizeDidChange
    bluetooth_received_fragment_group: BluetoothReceivedFragmentGroupMessage
    fragment_did_upload: FragmentDidUploadMessage
    user_defaults: UserDefaultsMessage
    check_for_update: CheckForUpdateMessage
    pendant_status: PendantStatus
    pendant_characteristic_value: PendantCharacteristicValue
    analytics_track: AnalyticsTrackMessage
    bluetooth_permission_denied: BluetoothPermissionDeniedMessage
    def __init__(self, bluetooth_received_fragment: _Optional[_Union[BluetoothReceivedFragmentMessage, _Mapping]] = ..., get_ingest_token: _Optional[_Union[GetIngestTokenMessage, _Mapping]] = ..., app_lifecycle_did_change: _Optional[_Union[AppLifecycleState, str]] = ..., firmware_update_state_did_change: _Optional[_Union[FirmwareUpdateState, _Mapping]] = ..., fragment_storage_size_did_change: _Optional[_Union[FragmentStorageSizeDidChange, _Mapping]] = ..., bluetooth_received_fragment_group: _Optional[_Union[BluetoothReceivedFragmentGroupMessage, _Mapping]] = ..., fragment_did_upload: _Optional[_Union[FragmentDidUploadMessage, _Mapping]] = ..., user_defaults: _Optional[_Union[UserDefaultsMessage, _Mapping]] = ..., check_for_update: _Optional[_Union[CheckForUpdateMessage, _Mapping]] = ..., pendant_status: _Optional[_Union[PendantStatus, _Mapping]] = ..., pendant_characteristic_value: _Optional[_Union[PendantCharacteristicValue, _Mapping]] = ..., analytics_track: _Optional[_Union[AnalyticsTrackMessage, _Mapping]] = ..., bluetooth_permission_denied: _Optional[_Union[BluetoothPermissionDeniedMessage, _Mapping]] = ...) -> None: ...

class PendantCharacteristicValue(_message.Message):
    __slots__ = ("battery_level", "rssi")
    BATTERY_LEVEL_FIELD_NUMBER: _ClassVar[int]
    RSSI_FIELD_NUMBER: _ClassVar[int]
    battery_level: int
    rssi: int
    def __init__(self, battery_level: _Optional[int] = ..., rssi: _Optional[int] = ...) -> None: ...

class PendantStatus(_message.Message):
    __slots__ = ("saved_peripheral_id", "disconnect_reason", "peripheral")
    SAVED_PERIPHERAL_ID_FIELD_NUMBER: _ClassVar[int]
    DISCONNECT_REASON_FIELD_NUMBER: _ClassVar[int]
    PERIPHERAL_FIELD_NUMBER: _ClassVar[int]
    saved_peripheral_id: str
    disconnect_reason: BluetoothDisconnectedReason
    peripheral: _common_pb2.BluetoothPeripheral
    def __init__(self, saved_peripheral_id: _Optional[str] = ..., disconnect_reason: _Optional[_Union[BluetoothDisconnectedReason, str]] = ..., peripheral: _Optional[_Union[_common_pb2.BluetoothPeripheral, _Mapping]] = ...) -> None: ...

class SendMessageResponse(_message.Message):
    __slots__ = ("data", "error_message")
    DATA_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    error_message: str
    def __init__(self, data: _Optional[bytes] = ..., error_message: _Optional[str] = ...) -> None: ...

class UploadAllLocalDataResponse(_message.Message):
    __slots__ = ("error", "most_recent_data_timestamp_ms")
    ERROR_FIELD_NUMBER: _ClassVar[int]
    MOST_RECENT_DATA_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    error: str
    most_recent_data_timestamp_ms: int
    def __init__(self, error: _Optional[str] = ..., most_recent_data_timestamp_ms: _Optional[int] = ...) -> None: ...

class UserDefaultsMessage(_message.Message):
    __slots__ = ("firmware_update_channel", "firmware_code_signing_method")
    FIRMWARE_UPDATE_CHANNEL_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_CODE_SIGNING_METHOD_FIELD_NUMBER: _ClassVar[int]
    firmware_update_channel: _common_pb2.FirmwareChannel
    firmware_code_signing_method: _common_pb2.FirmwareCodeSigningMethod
    def __init__(self, firmware_update_channel: _Optional[_Union[_common_pb2.FirmwareChannel, str]] = ..., firmware_code_signing_method: _Optional[_Union[_common_pb2.FirmwareCodeSigningMethod, str]] = ...) -> None: ...

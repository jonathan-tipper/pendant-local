import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AnalyticsIdentifyRequest(_message.Message):
    __slots__ = ("id", "email")
    ID_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    id: str
    email: str
    def __init__(self, id: _Optional[str] = ..., email: _Optional[str] = ...) -> None: ...

class AnalyticsUnidentifyRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class BluetoothStartScanningRequest(_message.Message):
    __slots__ = ("hide_paired_pendants",)
    HIDE_PAIRED_PENDANTS_FIELD_NUMBER: _ClassVar[int]
    hide_paired_pendants: bool
    def __init__(self, hide_paired_pendants: _Optional[bool] = ...) -> None: ...

class CleanCodecResourcesRequest(_message.Message):
    __slots__ = ("sample_rate", "channels")
    SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    CHANNELS_FIELD_NUMBER: _ClassVar[int]
    sample_rate: int
    channels: int
    def __init__(self, sample_rate: _Optional[int] = ..., channels: _Optional[int] = ...) -> None: ...

class DecodeAudioRequest(_message.Message):
    __slots__ = ("opus_frames", "sample_rate", "channels")
    OPUS_FRAMES_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    CHANNELS_FIELD_NUMBER: _ClassVar[int]
    opus_frames: _containers.RepeatedScalarFieldContainer[bytes]
    sample_rate: int
    channels: int
    def __init__(self, opus_frames: _Optional[_Iterable[bytes]] = ..., sample_rate: _Optional[int] = ..., channels: _Optional[int] = ...) -> None: ...

class DecodeAudioResponse(_message.Message):
    __slots__ = ("data", "error_message")
    DATA_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    data: DecodedAudioData
    error_message: str
    def __init__(self, data: _Optional[_Union[DecodedAudioData, _Mapping]] = ..., error_message: _Optional[str] = ...) -> None: ...

class DecodedAudioData(_message.Message):
    __slots__ = ("pcm_data", "sample_rate", "channels", "duration_ms")
    PCM_DATA_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    CHANNELS_FIELD_NUMBER: _ClassVar[int]
    DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    pcm_data: bytes
    sample_rate: int
    channels: int
    duration_ms: int
    def __init__(self, pcm_data: _Optional[bytes] = ..., sample_rate: _Optional[int] = ..., channels: _Optional[int] = ..., duration_ms: _Optional[int] = ...) -> None: ...

class DidReceiveDeviceInfoRequest(_message.Message):
    __slots__ = ("device_info",)
    DEVICE_INFO_FIELD_NUMBER: _ClassVar[int]
    device_info: bytes
    def __init__(self, device_info: _Optional[bytes] = ...) -> None: ...

class EncodeAudioRequest(_message.Message):
    __slots__ = ("pcm_data", "sample_rate", "channels")
    PCM_DATA_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    CHANNELS_FIELD_NUMBER: _ClassVar[int]
    pcm_data: str
    sample_rate: int
    channels: int
    def __init__(self, pcm_data: _Optional[str] = ..., sample_rate: _Optional[int] = ..., channels: _Optional[int] = ...) -> None: ...

class EncodeAudioResponse(_message.Message):
    __slots__ = ("data", "error_message")
    DATA_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    data: EncodedAudioData
    error_message: str
    def __init__(self, data: _Optional[_Union[EncodedAudioData, _Mapping]] = ..., error_message: _Optional[str] = ...) -> None: ...

class EncodedAudioData(_message.Message):
    __slots__ = ("frames", "byte_size")
    FRAMES_FIELD_NUMBER: _ClassVar[int]
    BYTE_SIZE_FIELD_NUMBER: _ClassVar[int]
    frames: _containers.RepeatedScalarFieldContainer[bytes]
    byte_size: int
    def __init__(self, frames: _Optional[_Iterable[bytes]] = ..., byte_size: _Optional[int] = ...) -> None: ...

class ExportLogsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetFirebaseDebuggingEnabledRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetFirebaseDebuggingEnabledResponse(_message.Message):
    __slots__ = ("enabled",)
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    enabled: bool
    def __init__(self, enabled: _Optional[bool] = ...) -> None: ...

class GetPendantStatus(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MessageMuxerState(_message.Message):
    __slots__ = ("enabled", "is_connected_to_client")
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    IS_CONNECTED_TO_CLIENT_FIELD_NUMBER: _ClassVar[int]
    enabled: bool
    is_connected_to_client: bool
    def __init__(self, enabled: _Optional[bool] = ..., is_connected_to_client: _Optional[bool] = ...) -> None: ...

class MessageMuxerStateRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class NativeBridgeMessage(_message.Message):
    __slots__ = ("open_url", "bluetooth_start_scanning", "analytics_identify", "analytics_unidentify", "export_logs", "send_message", "get_pendant_status", "set_bridge_is_ready", "set_pairing_and_authentication_completed", "unpair_peripheral", "perform_firmware_update", "did_receive_device_info", "wipe_native_storage", "set_ingest_token", "view_logs", "update_web_server_url", "set_firmware_update_channel", "reset_firmware_update_state", "upload_all_local_data", "toggle_uploading_pendant_data", "update_user_defaults", "get_message_muxer_state", "set_message_muxer_enabled", "set_firebase_debugging_enabled", "get_firebase_debugging_enabled", "set_rssi_interval_enabled", "encode_audio", "decode_audio", "clean_codec_resources")
    OPEN_URL_FIELD_NUMBER: _ClassVar[int]
    BLUETOOTH_START_SCANNING_FIELD_NUMBER: _ClassVar[int]
    ANALYTICS_IDENTIFY_FIELD_NUMBER: _ClassVar[int]
    ANALYTICS_UNIDENTIFY_FIELD_NUMBER: _ClassVar[int]
    EXPORT_LOGS_FIELD_NUMBER: _ClassVar[int]
    SEND_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    GET_PENDANT_STATUS_FIELD_NUMBER: _ClassVar[int]
    SET_BRIDGE_IS_READY_FIELD_NUMBER: _ClassVar[int]
    SET_PAIRING_AND_AUTHENTICATION_COMPLETED_FIELD_NUMBER: _ClassVar[int]
    UNPAIR_PERIPHERAL_FIELD_NUMBER: _ClassVar[int]
    PERFORM_FIRMWARE_UPDATE_FIELD_NUMBER: _ClassVar[int]
    DID_RECEIVE_DEVICE_INFO_FIELD_NUMBER: _ClassVar[int]
    WIPE_NATIVE_STORAGE_FIELD_NUMBER: _ClassVar[int]
    SET_INGEST_TOKEN_FIELD_NUMBER: _ClassVar[int]
    VIEW_LOGS_FIELD_NUMBER: _ClassVar[int]
    UPDATE_WEB_SERVER_URL_FIELD_NUMBER: _ClassVar[int]
    SET_FIRMWARE_UPDATE_CHANNEL_FIELD_NUMBER: _ClassVar[int]
    RESET_FIRMWARE_UPDATE_STATE_FIELD_NUMBER: _ClassVar[int]
    UPLOAD_ALL_LOCAL_DATA_FIELD_NUMBER: _ClassVar[int]
    TOGGLE_UPLOADING_PENDANT_DATA_FIELD_NUMBER: _ClassVar[int]
    UPDATE_USER_DEFAULTS_FIELD_NUMBER: _ClassVar[int]
    GET_MESSAGE_MUXER_STATE_FIELD_NUMBER: _ClassVar[int]
    SET_MESSAGE_MUXER_ENABLED_FIELD_NUMBER: _ClassVar[int]
    SET_FIREBASE_DEBUGGING_ENABLED_FIELD_NUMBER: _ClassVar[int]
    GET_FIREBASE_DEBUGGING_ENABLED_FIELD_NUMBER: _ClassVar[int]
    SET_RSSI_INTERVAL_ENABLED_FIELD_NUMBER: _ClassVar[int]
    ENCODE_AUDIO_FIELD_NUMBER: _ClassVar[int]
    DECODE_AUDIO_FIELD_NUMBER: _ClassVar[int]
    CLEAN_CODEC_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    open_url: OpenUrlRequest
    bluetooth_start_scanning: BluetoothStartScanningRequest
    analytics_identify: AnalyticsIdentifyRequest
    analytics_unidentify: AnalyticsUnidentifyRequest
    export_logs: ExportLogsRequest
    send_message: SendMessageRequest
    get_pendant_status: GetPendantStatus
    set_bridge_is_ready: SetBridgeIsReadyRequest
    set_pairing_and_authentication_completed: SetPairingAndAuthenticationCompletedRequest
    unpair_peripheral: UnpairPeripheralRequest
    perform_firmware_update: PerformFirmwareUpdateRequest
    did_receive_device_info: DidReceiveDeviceInfoRequest
    wipe_native_storage: WipeNativeStorageRequest
    set_ingest_token: SetIngestTokenRequest
    view_logs: ViewLogsRequest
    update_web_server_url: UpdateWebServerURLRequest
    set_firmware_update_channel: SetFirmwareChannelRequest
    reset_firmware_update_state: ResetFirmwareUpdateStateRequest
    upload_all_local_data: UploadAllLocalDataRequest
    toggle_uploading_pendant_data: ToggleUploadingPendantDataRequest
    update_user_defaults: UpdateUserDefaultsRequest
    get_message_muxer_state: MessageMuxerStateRequest
    set_message_muxer_enabled: bool
    set_firebase_debugging_enabled: bool
    get_firebase_debugging_enabled: GetFirebaseDebuggingEnabledRequest
    set_rssi_interval_enabled: SetRSSIIntervalEnabledRequest
    encode_audio: EncodeAudioRequest
    decode_audio: DecodeAudioRequest
    clean_codec_resources: CleanCodecResourcesRequest
    def __init__(self, open_url: _Optional[_Union[OpenUrlRequest, _Mapping]] = ..., bluetooth_start_scanning: _Optional[_Union[BluetoothStartScanningRequest, _Mapping]] = ..., analytics_identify: _Optional[_Union[AnalyticsIdentifyRequest, _Mapping]] = ..., analytics_unidentify: _Optional[_Union[AnalyticsUnidentifyRequest, _Mapping]] = ..., export_logs: _Optional[_Union[ExportLogsRequest, _Mapping]] = ..., send_message: _Optional[_Union[SendMessageRequest, _Mapping]] = ..., get_pendant_status: _Optional[_Union[GetPendantStatus, _Mapping]] = ..., set_bridge_is_ready: _Optional[_Union[SetBridgeIsReadyRequest, _Mapping]] = ..., set_pairing_and_authentication_completed: _Optional[_Union[SetPairingAndAuthenticationCompletedRequest, _Mapping]] = ..., unpair_peripheral: _Optional[_Union[UnpairPeripheralRequest, _Mapping]] = ..., perform_firmware_update: _Optional[_Union[PerformFirmwareUpdateRequest, _Mapping]] = ..., did_receive_device_info: _Optional[_Union[DidReceiveDeviceInfoRequest, _Mapping]] = ..., wipe_native_storage: _Optional[_Union[WipeNativeStorageRequest, _Mapping]] = ..., set_ingest_token: _Optional[_Union[SetIngestTokenRequest, _Mapping]] = ..., view_logs: _Optional[_Union[ViewLogsRequest, _Mapping]] = ..., update_web_server_url: _Optional[_Union[UpdateWebServerURLRequest, _Mapping]] = ..., set_firmware_update_channel: _Optional[_Union[SetFirmwareChannelRequest, _Mapping]] = ..., reset_firmware_update_state: _Optional[_Union[ResetFirmwareUpdateStateRequest, _Mapping]] = ..., upload_all_local_data: _Optional[_Union[UploadAllLocalDataRequest, _Mapping]] = ..., toggle_uploading_pendant_data: _Optional[_Union[ToggleUploadingPendantDataRequest, _Mapping]] = ..., update_user_defaults: _Optional[_Union[UpdateUserDefaultsRequest, _Mapping]] = ..., get_message_muxer_state: _Optional[_Union[MessageMuxerStateRequest, _Mapping]] = ..., set_message_muxer_enabled: _Optional[bool] = ..., set_firebase_debugging_enabled: _Optional[bool] = ..., get_firebase_debugging_enabled: _Optional[_Union[GetFirebaseDebuggingEnabledRequest, _Mapping]] = ..., set_rssi_interval_enabled: _Optional[_Union[SetRSSIIntervalEnabledRequest, _Mapping]] = ..., encode_audio: _Optional[_Union[EncodeAudioRequest, _Mapping]] = ..., decode_audio: _Optional[_Union[DecodeAudioRequest, _Mapping]] = ..., clean_codec_resources: _Optional[_Union[CleanCodecResourcesRequest, _Mapping]] = ...) -> None: ...

class OpenUrlRequest(_message.Message):
    __slots__ = ("url",)
    URL_FIELD_NUMBER: _ClassVar[int]
    url: str
    def __init__(self, url: _Optional[str] = ...) -> None: ...

class OpenUrlResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: _Optional[bool] = ...) -> None: ...

class PerformFirmwareUpdateRequest(_message.Message):
    __slots__ = ("ble_identifier", "signed_url", "update_sha256")
    BLE_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    SIGNED_URL_FIELD_NUMBER: _ClassVar[int]
    UPDATE_SHA256_FIELD_NUMBER: _ClassVar[int]
    ble_identifier: str
    signed_url: str
    update_sha256: str
    def __init__(self, ble_identifier: _Optional[str] = ..., signed_url: _Optional[str] = ..., update_sha256: _Optional[str] = ...) -> None: ...

class ResetFirmwareUpdateStateRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SendMessageRequest(_message.Message):
    __slots__ = ("message", "peripheral", "timeout")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    PERIPHERAL_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    message: bytes
    peripheral: _common_pb2.BluetoothPeripheral
    timeout: float
    def __init__(self, message: _Optional[bytes] = ..., peripheral: _Optional[_Union[_common_pb2.BluetoothPeripheral, _Mapping]] = ..., timeout: _Optional[float] = ...) -> None: ...

class SetBridgeIsReadyRequest(_message.Message):
    __slots__ = ("is_ready",)
    IS_READY_FIELD_NUMBER: _ClassVar[int]
    is_ready: bool
    def __init__(self, is_ready: _Optional[bool] = ...) -> None: ...

class SetFirmwareChannelRequest(_message.Message):
    __slots__ = ("channel", "code_signing_method")
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    CODE_SIGNING_METHOD_FIELD_NUMBER: _ClassVar[int]
    channel: _common_pb2.FirmwareChannel
    code_signing_method: _common_pb2.FirmwareCodeSigningMethod
    def __init__(self, channel: _Optional[_Union[_common_pb2.FirmwareChannel, str]] = ..., code_signing_method: _Optional[_Union[_common_pb2.FirmwareCodeSigningMethod, str]] = ...) -> None: ...

class SetIngestTokenRequest(_message.Message):
    __slots__ = ("ble_identifier", "ingest_token", "get_ingest_token_request_id", "error_message")
    BLE_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    INGEST_TOKEN_FIELD_NUMBER: _ClassVar[int]
    GET_INGEST_TOKEN_REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ble_identifier: str
    ingest_token: str
    get_ingest_token_request_id: int
    error_message: str
    def __init__(self, ble_identifier: _Optional[str] = ..., ingest_token: _Optional[str] = ..., get_ingest_token_request_id: _Optional[int] = ..., error_message: _Optional[str] = ...) -> None: ...

class SetPairingAndAuthenticationCompletedRequest(_message.Message):
    __slots__ = ("ble_identifier",)
    BLE_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    ble_identifier: str
    def __init__(self, ble_identifier: _Optional[str] = ...) -> None: ...

class SetRSSIIntervalEnabledRequest(_message.Message):
    __slots__ = ("enabled", "interval_in_seconds")
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    INTERVAL_IN_SECONDS_FIELD_NUMBER: _ClassVar[int]
    enabled: bool
    interval_in_seconds: float
    def __init__(self, enabled: _Optional[bool] = ..., interval_in_seconds: _Optional[float] = ...) -> None: ...

class SetRSSIIntervalEnabledResponse(_message.Message):
    __slots__ = ("success", "error_message", "is_monitoring_enabled", "current_interval")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    IS_MONITORING_ENABLED_FIELD_NUMBER: _ClassVar[int]
    CURRENT_INTERVAL_FIELD_NUMBER: _ClassVar[int]
    success: bool
    error_message: str
    is_monitoring_enabled: bool
    current_interval: float
    def __init__(self, success: _Optional[bool] = ..., error_message: _Optional[str] = ..., is_monitoring_enabled: _Optional[bool] = ..., current_interval: _Optional[float] = ...) -> None: ...

class ToggleUploadingPendantDataRequest(_message.Message):
    __slots__ = ("is_enabled",)
    IS_ENABLED_FIELD_NUMBER: _ClassVar[int]
    is_enabled: bool
    def __init__(self, is_enabled: _Optional[bool] = ...) -> None: ...

class UnpairPeripheralRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class UpdateUserDefaultsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class UpdateWebServerURLRequest(_message.Message):
    __slots__ = ("host",)
    HOST_FIELD_NUMBER: _ClassVar[int]
    host: str
    def __init__(self, host: _Optional[str] = ...) -> None: ...

class UploadAllLocalDataRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ViewLogsRequest(_message.Message):
    __slots__ = ("ble_identifier",)
    BLE_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    ble_identifier: str
    def __init__(self, ble_identifier: _Optional[str] = ...) -> None: ...

class WipeNativeStorageRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

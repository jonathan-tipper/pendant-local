import shared_pb2 as _shared_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EncryptedBytes(_message.Message):
    __slots__ = ("nonce", "ciphertext", "authentication_tag", "packet_offsets")
    NONCE_FIELD_NUMBER: _ClassVar[int]
    CIPHERTEXT_FIELD_NUMBER: _ClassVar[int]
    AUTHENTICATION_TAG_FIELD_NUMBER: _ClassVar[int]
    PACKET_OFFSETS_FIELD_NUMBER: _ClassVar[int]
    nonce: bytes
    ciphertext: bytes
    authentication_tag: bytes
    packet_offsets: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, nonce: _Optional[bytes] = ..., ciphertext: _Optional[bytes] = ..., authentication_tag: _Optional[bytes] = ..., packet_offsets: _Optional[_Iterable[int]] = ...) -> None: ...

class PendantAudioData(_message.Message):
    __slots__ = ("pcm_omni_mic_data", "pcm_directional_mic_data", "pcm_beamforming_data", "codec_beamforming_data", "codec_manual_beamforming_data", "reserved_1", "pcm_manual_beamforming_data", "did_start_recording", "did_stop_recording", "codec_type", "num_frames", "degree_of_arrival", "encrypted_codec_beamforming_data")
    PCM_OMNI_MIC_DATA_FIELD_NUMBER: _ClassVar[int]
    PCM_DIRECTIONAL_MIC_DATA_FIELD_NUMBER: _ClassVar[int]
    PCM_BEAMFORMING_DATA_FIELD_NUMBER: _ClassVar[int]
    CODEC_BEAMFORMING_DATA_FIELD_NUMBER: _ClassVar[int]
    CODEC_MANUAL_BEAMFORMING_DATA_FIELD_NUMBER: _ClassVar[int]
    RESERVED_1_FIELD_NUMBER: _ClassVar[int]
    PCM_MANUAL_BEAMFORMING_DATA_FIELD_NUMBER: _ClassVar[int]
    DID_START_RECORDING_FIELD_NUMBER: _ClassVar[int]
    DID_STOP_RECORDING_FIELD_NUMBER: _ClassVar[int]
    CODEC_TYPE_FIELD_NUMBER: _ClassVar[int]
    NUM_FRAMES_FIELD_NUMBER: _ClassVar[int]
    DEGREE_OF_ARRIVAL_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTED_CODEC_BEAMFORMING_DATA_FIELD_NUMBER: _ClassVar[int]
    pcm_omni_mic_data: bytes
    pcm_directional_mic_data: bytes
    pcm_beamforming_data: bytes
    codec_beamforming_data: bytes
    codec_manual_beamforming_data: bytes
    reserved_1: bytes
    pcm_manual_beamforming_data: bytes
    did_start_recording: bool
    did_stop_recording: bool
    codec_type: int
    num_frames: int
    degree_of_arrival: int
    encrypted_codec_beamforming_data: EncryptedBytes
    def __init__(self, pcm_omni_mic_data: _Optional[bytes] = ..., pcm_directional_mic_data: _Optional[bytes] = ..., pcm_beamforming_data: _Optional[bytes] = ..., codec_beamforming_data: _Optional[bytes] = ..., codec_manual_beamforming_data: _Optional[bytes] = ..., reserved_1: _Optional[bytes] = ..., pcm_manual_beamforming_data: _Optional[bytes] = ..., did_start_recording: _Optional[bool] = ..., did_stop_recording: _Optional[bool] = ..., codec_type: _Optional[int] = ..., num_frames: _Optional[int] = ..., degree_of_arrival: _Optional[int] = ..., encrypted_codec_beamforming_data: _Optional[_Union[EncryptedBytes, _Mapping]] = ...) -> None: ...

class Chunk(_message.Message):
    __slots__ = ("time_offset_ms", "audio_data", "button_status", "wifi_status", "ble_status", "battery_status", "usb_status", "imu_data", "recording_status", "log_output", "runtime_status", "storage_status", "cpu_status")
    TIME_OFFSET_MS_FIELD_NUMBER: _ClassVar[int]
    AUDIO_DATA_FIELD_NUMBER: _ClassVar[int]
    BUTTON_STATUS_FIELD_NUMBER: _ClassVar[int]
    WIFI_STATUS_FIELD_NUMBER: _ClassVar[int]
    BLE_STATUS_FIELD_NUMBER: _ClassVar[int]
    BATTERY_STATUS_FIELD_NUMBER: _ClassVar[int]
    USB_STATUS_FIELD_NUMBER: _ClassVar[int]
    IMU_DATA_FIELD_NUMBER: _ClassVar[int]
    RECORDING_STATUS_FIELD_NUMBER: _ClassVar[int]
    LOG_OUTPUT_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_STATUS_FIELD_NUMBER: _ClassVar[int]
    STORAGE_STATUS_FIELD_NUMBER: _ClassVar[int]
    CPU_STATUS_FIELD_NUMBER: _ClassVar[int]
    time_offset_ms: int
    audio_data: PendantAudioData
    button_status: _shared_pb2.ButtonStatus
    wifi_status: _shared_pb2.WifiStatus
    ble_status: BleStatus
    battery_status: _shared_pb2.BatteryStatus
    usb_status: _shared_pb2.UsbStatus
    imu_data: ImuData
    recording_status: _shared_pb2.RecordingStatus
    log_output: LogOutput
    runtime_status: RuntimeStatus
    storage_status: StorageStatus
    cpu_status: CpuStatus
    def __init__(self, time_offset_ms: _Optional[int] = ..., audio_data: _Optional[_Union[PendantAudioData, _Mapping]] = ..., button_status: _Optional[_Union[_shared_pb2.ButtonStatus, _Mapping]] = ..., wifi_status: _Optional[_Union[_shared_pb2.WifiStatus, _Mapping]] = ..., ble_status: _Optional[_Union[BleStatus, _Mapping]] = ..., battery_status: _Optional[_Union[_shared_pb2.BatteryStatus, _Mapping]] = ..., usb_status: _Optional[_Union[_shared_pb2.UsbStatus, _Mapping]] = ..., imu_data: _Optional[_Union[ImuData, _Mapping]] = ..., recording_status: _Optional[_Union[_shared_pb2.RecordingStatus, _Mapping]] = ..., log_output: _Optional[_Union[LogOutput, _Mapping]] = ..., runtime_status: _Optional[_Union[RuntimeStatus, _Mapping]] = ..., storage_status: _Optional[_Union[StorageStatus, _Mapping]] = ..., cpu_status: _Optional[_Union[CpuStatus, _Mapping]] = ...) -> None: ...

class FlashPage(_message.Message):
    __slots__ = ("absolute_timestamp_ms", "boot_uptime_ms", "chunks")
    ABSOLUTE_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    BOOT_UPTIME_MS_FIELD_NUMBER: _ClassVar[int]
    CHUNKS_FIELD_NUMBER: _ClassVar[int]
    absolute_timestamp_ms: int
    boot_uptime_ms: int
    chunks: _containers.RepeatedCompositeFieldContainer[Chunk]
    def __init__(self, absolute_timestamp_ms: _Optional[int] = ..., boot_uptime_ms: _Optional[int] = ..., chunks: _Optional[_Iterable[_Union[Chunk, _Mapping]]] = ...) -> None: ...

class StorageStatus(_message.Message):
    __slots__ = ("did_start_storage_session", "did_stop_storage_session")
    DID_START_STORAGE_SESSION_FIELD_NUMBER: _ClassVar[int]
    DID_STOP_STORAGE_SESSION_FIELD_NUMBER: _ClassVar[int]
    did_start_storage_session: bool
    did_stop_storage_session: bool
    def __init__(self, did_start_storage_session: _Optional[bool] = ..., did_stop_storage_session: _Optional[bool] = ...) -> None: ...

class BleStatus(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ImuData(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class LogOutput(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RuntimeStatus(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CpuStatus(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

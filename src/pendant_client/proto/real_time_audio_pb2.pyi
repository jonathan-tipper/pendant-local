from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class RealTimeAudioAck(_message.Message):
    __slots__ = ("stream_id", "ack_index", "missing_indices", "free_amplifier_queue_slots", "free_speaker_queue_slots", "free_ble_queue_slots")
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    ACK_INDEX_FIELD_NUMBER: _ClassVar[int]
    MISSING_INDICES_FIELD_NUMBER: _ClassVar[int]
    FREE_AMPLIFIER_QUEUE_SLOTS_FIELD_NUMBER: _ClassVar[int]
    FREE_SPEAKER_QUEUE_SLOTS_FIELD_NUMBER: _ClassVar[int]
    FREE_BLE_QUEUE_SLOTS_FIELD_NUMBER: _ClassVar[int]
    stream_id: int
    ack_index: int
    missing_indices: _containers.RepeatedScalarFieldContainer[int]
    free_amplifier_queue_slots: int
    free_speaker_queue_slots: int
    free_ble_queue_slots: int
    def __init__(self, stream_id: _Optional[int] = ..., ack_index: _Optional[int] = ..., missing_indices: _Optional[_Iterable[int]] = ..., free_amplifier_queue_slots: _Optional[int] = ..., free_speaker_queue_slots: _Optional[int] = ..., free_ble_queue_slots: _Optional[int] = ...) -> None: ...

class RealTimeAudioData(_message.Message):
    __slots__ = ("stream_id", "first_frame_index", "ts_ms", "opus_packet", "frame_sizes")
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    FIRST_FRAME_INDEX_FIELD_NUMBER: _ClassVar[int]
    TS_MS_FIELD_NUMBER: _ClassVar[int]
    OPUS_PACKET_FIELD_NUMBER: _ClassVar[int]
    FRAME_SIZES_FIELD_NUMBER: _ClassVar[int]
    stream_id: int
    first_frame_index: int
    ts_ms: int
    opus_packet: bytes
    frame_sizes: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, stream_id: _Optional[int] = ..., first_frame_index: _Optional[int] = ..., ts_ms: _Optional[int] = ..., opus_packet: _Optional[bytes] = ..., frame_sizes: _Optional[_Iterable[int]] = ...) -> None: ...

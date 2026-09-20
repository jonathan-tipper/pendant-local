from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class FirmwareChannel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PRODUCTION: _ClassVar[FirmwareChannel]
    DEVELOPMENT: _ClassVar[FirmwareChannel]

class FirmwareCodeSigningMethod(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RELEASE_CODE_SIGNING: _ClassVar[FirmwareCodeSigningMethod]
    DEVELOPMENT_CODE_SIGNING: _ClassVar[FirmwareCodeSigningMethod]
PRODUCTION: FirmwareChannel
DEVELOPMENT: FirmwareChannel
RELEASE_CODE_SIGNING: FirmwareCodeSigningMethod
DEVELOPMENT_CODE_SIGNING: FirmwareCodeSigningMethod

class BLEMessageFromNativeToPendant(_message.Message):
    __slots__ = ("index", "ble_fragment_seq", "num_fragments", "payload")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    BLE_FRAGMENT_SEQ_FIELD_NUMBER: _ClassVar[int]
    NUM_FRAGMENTS_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    index: int
    ble_fragment_seq: int
    num_fragments: int
    payload: bytes
    def __init__(self, index: _Optional[int] = ..., ble_fragment_seq: _Optional[int] = ..., num_fragments: _Optional[int] = ..., payload: _Optional[bytes] = ...) -> None: ...

class BLEMessageFromPendantToNative(_message.Message):
    __slots__ = ("index", "ble_fragment_seq", "num_fragments", "payload")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    BLE_FRAGMENT_SEQ_FIELD_NUMBER: _ClassVar[int]
    NUM_FRAGMENTS_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    index: int
    ble_fragment_seq: int
    num_fragments: int
    payload: bytes
    def __init__(self, index: _Optional[int] = ..., ble_fragment_seq: _Optional[int] = ..., num_fragments: _Optional[int] = ..., payload: _Optional[bytes] = ...) -> None: ...

class BluetoothPeripheral(_message.Message):
    __slots__ = ("identifier", "name", "is_paired")
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    IS_PAIRED_FIELD_NUMBER: _ClassVar[int]
    identifier: str
    name: str
    is_paired: bool
    def __init__(self, identifier: _Optional[str] = ..., name: _Optional[str] = ..., is_paired: _Optional[bool] = ...) -> None: ...

class GenericResponse(_message.Message):
    __slots__ = ("ack",)
    ACK_FIELD_NUMBER: _ClassVar[int]
    ack: str
    def __init__(self, ack: _Optional[str] = ...) -> None: ...

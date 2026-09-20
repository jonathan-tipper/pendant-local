"""Small, local-only adapter over the pinned Pendant BLE client."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from bleak import BleakScanner
from bleak.exc import BleakError
from cryptography.hazmat.primitives import serialization

from pendant_client import SERVICE_UUID, WRITE_CHAR_UUID
from pendant_client.ble import PendantNotPairedError
from pendant_client.crypto import generate_keyset, keyset_from_existing
from pendant_client.session import PendantSession
from pendant_client.proto import server_pb2


def key_id(address: str) -> str:
    return hashlib.sha256(address.strip().upper().encode()).hexdigest()[:24]


def sync_directory(path: Path) -> None:
    """Persist directory entries on POSIX; Windows has no directory fsync."""
    if os.name == "nt":
        return
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def durable_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    sync_directory(path.parent)


def durable_json(path: Path, obj: dict) -> None:
    durable_write(path, (json.dumps(obj, indent=2) + "\n").encode())


@asynccontextmanager
async def connected(address: str):
    """Upstream's failed __aenter__ otherwise leaves its client connected."""
    for attempt in range(2):
        session = PendantSession(address)
        try:
            await session.__aenter__()
            session.connection_attempts = attempt + 1
            break
        except BaseException as exc:
            try:
                await session._client.disconnect()
            except Exception:
                pass
            if isinstance(exc, PendantNotPairedError):
                raise RuntimeError(_PAIRING_HELP) from exc
            transient = isinstance(exc, TimeoutError) or (
                isinstance(exc, BleakError) and any(part in str(exc).lower() for part in
                    ("timed out", "timeout", "failed to encrypt", "connection abort")))
            if attempt == 0 and transient:
                await asyncio.sleep(1.5)
                continue
            raise
    try:
        # The pinned upstream applies a 150-byte minimum even if MTU is 23.
        # Respect the actual characteristic/ATT budget and reserve wrapper space.
        transport = session._transport
        if transport is not None:
            client = session._client
            mtu = getattr(client, "mtu_size", 23)
            capacity = max(20, mtu - 3) if isinstance(mtu, int) else 20
            if not transport._write_with_response:
                characteristic = client.services.get_characteristic(WRITE_CHAR_UUID)
                capacity = getattr(characteristic, "max_write_without_response_size", capacity)
            transport._fragment_payload = max(1, min(transport._fragment_payload, capacity - 20))
        yield session
    except PendantNotPairedError as exc:
        raise RuntimeError(_PAIRING_HELP) from exc
    finally:
        await session.__aexit__(None, None, None)


_PAIRING_HELP = (
    "Bluetooth pairing is required. Pair the Pendant in this computer's Bluetooth "
    "settings, close other Pendant apps, and retry. An existing bond may block pairing. "
    "Preserve any unsynced recordings before clearing bonds or resetting the device."
)


def info_dict(di, address: str) -> dict:
    return {
        "address": address,
        "key_id": key_id(address),
        "device_id": str(di.device_id),
        "serial_num": di.serial_num,
        "firmware_ver": di.firmware_ver,
        "battery_percent": di.battery_percent,
        "oldest_flash_page": di.oldest_flash_page,
        "newest_flash_page": di.newest_flash_page,
        "pendant_public_key_hex": di.audio_encryption_pub_key.hex(),
        "storage_instance": str(getattr(di.raw, "storage_instance", 0)),
        "storage_run": getattr(di.raw, "storage_run", 0),
        "factory_reset_id": getattr(di.raw, "factory_reset_id", 0),
    }


async def scan(timeout: float = 8) -> list[dict]:
    found = await BleakScanner.discover(timeout=timeout, return_adv=True)
    return [
        {"address": dev.address, "name": adv.local_name or dev.name,
         "rssi": adv.rssi, "service_uuids": list(adv.service_uuids or [])}
        for dev, adv in found.values()
        if SERVICE_UUID.lower() in [u.lower() for u in adv.service_uuids or []]
    ]


async def info(address: str) -> dict:
    async with connected(address) as session:
        di = await session.get_device_info()
        result = info_dict(di, address)
        result["connection_attempts"] = getattr(session, "connection_attempts", 1)
        result["checked_at"] = datetime.now(timezone.utc).isoformat()
        # Optional telemetry must not turn a successful basic check into a failure.
        # Prefer the explicit snapshot; older firmware may only include it in info.
        status = None
        source = None
        if di.raw.HasField("device_status"):
            status, source = di.raw.device_status, "device_info"
        try:
            snapshot = await asyncio.wait_for(session.get_device_status(), timeout=8)
            if snapshot.ListFields():
                status, source = snapshot, "device_status"
        except Exception as exc:
            result["status_warning"] = f"Extended status request failed ({type(exc).__name__})."
        result["telemetry"] = status_dict(status)
        result["telemetry_source"] = source
        return result


def status_dict(status) -> dict:
    """Expose a safe subset, preserving absent messages as null, not zero readings.

    Proto3 scalar defaults within a present snapshot are meaningful (e.g. stopped
    is enum zero). Missing submessages are not evidence of those default states.
    Power scaling is undocumented, so raw numbers have no invented units.
    """
    result = {"recording": None, "battery": None, "storage": None, "wifi": None}
    if status is None:
        return result
    if status.HasField("recording_status"):
        value = status.recording_status
        result["recording"] = {
            "state": {0: "stopped", 1: "recording", 2: "listening"}.get(value.recording_state, "unknown"),
            "source": {0: "button", 1: "ambient_sound"}.get(value.recording_source, "unknown"),
            "voice_activity_raw": value.vad_level,
        }
    if status.HasField("battery_status"):
        value = status.battery_status
        result["battery"] = {
            "state": {0: "discharging", 1: "charging", 2: "full"}.get(value.state, "unknown"),
            "usb": {0: "disconnected", 1: "connected"}.get(value.usb_state, "unknown"),
            "voltage_raw": value.voltage, "current_raw": value.current,
            "temperature_raw": value.temperature, "capacity_raw": value.capacity,
            "over_operating_temperature": value.over_operating_temperature,
            "under_operating_temperature": value.under_operating_temperature,
        }
    if status.HasField("storage_state"):
        value = status.storage_state
        free, total = value.free_capture_pages, value.total_capture_pages
        result["storage"] = {"free_pages": free, "total_pages": total,
                             "used_pages": total - free if total > 0 and 0 <= free <= total else None}
    if status.HasField("wifi_status"):
        value = status.wifi_status
        result["wifi"] = {
            "state": {0: "disconnected", 1: "connecting", 2: "connected", 3: "initialisation_error"}.get(value.state, "unknown"),
            "rssi": value.rssi if value.state == 2 and value.rssi < 0 else None,
        }
    return result


async def sync_clock(session) -> dict:
    """Require a device acknowledgement before attempting to arm recording.

    Three red flashes repeated twice indicate an unsynchronised clock on this
    firmware. The upstream one-way clock helper suppresses acknowledgements.
    """
    response = await asyncio.wait_for(session._request(
        expected_oneof="set_current_time_response",
        set_current_time=server_pb2.SetCurrentTime(unix_timestamp_ms=int(time.time() * 1000)),
    ), timeout=10)
    if response.HasField("response_data") and response.response_data.error.category:
        raise RuntimeError("The Pendant rejected clock synchronisation. Recording was not started.")
    if not (response.HasField("set_current_time_response") or response.HasField("response_data")):
        raise RuntimeError("The Pendant did not acknowledge clock synchronisation. Recording was not started.")
    return {"acknowledged": True}


async def set_clock(address: str) -> dict:
    async with connected(address) as session:
        await sync_clock(session)
    return {"address": address, "command_sent": "set_current_time",
            "device_execution_verified": True, "verification": "device_acknowledgement"}


async def recording(address: str, enabled: bool) -> dict:
    async with connected(address) as session:
        if enabled:
            try:
                await sync_clock(session)
            except TimeoutError as exc:
                raise RuntimeError("Clock synchronisation was not acknowledged. Recording was not started; retry when the Pendant is nearby.") from exc
        await (session.start_recording() if enabled else session.stop_recording())
        observed = None
        matched = False
        for attempt in range(2):
            await asyncio.sleep(0.5)
            try:
                snapshot = await asyncio.wait_for(session.get_device_status(), timeout=8)
                observed = status_dict(snapshot)["recording"]
            except Exception:
                break
            state = observed["state"] if observed else None
            matched = state in ("recording", "listening") if enabled else state == "stopped"
            if matched:
                break
    return {"address": address, "command_sent": "start_recording" if enabled else "stop_recording",
            "device_execution_verified": matched, "recording": observed,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "clock_synchronised": enabled,
            "connection_attempts": getattr(session, "connection_attempts", 1),
            "warning": None if matched else "Command sent, but the requested recording state was not confirmed. Check the Pendant before continuing."}


async def provision_key(address: str, keys_dir: Path) -> dict:
    """Save a reusable private key before changing the device's public key."""
    keys_dir = Path(keys_dir)
    kid = key_id(address)
    folder = keys_dir / kid
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    sync_directory(folder.parent)
    private_path = folder / "server-key.pem"
    async with connected(address) as session:
        di = await session.get_device_info()
        if private_path.exists():
            keys = keyset_from_existing(private_path.read_bytes(), di.audio_encryption_pub_key)
            created = False
        else:
            keys = generate_keyset(di.audio_encryption_pub_key)
            durable_write(private_path, keys.server_priv.private_bytes(
                serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption()))
            created = True
        # Persist the pairing's public context as well before the BLE mutation.
        durable_json(folder / "device.json", info_dict(di, address))
        await session.set_server_public_key(keys.server_pub_bytes)
    return {"address": address, "key_id": kid, "new_key_created": created,
            "public_key_fingerprint": hashlib.sha256(keys.server_pub_bytes).hexdigest(),
            "command_sent": "set_server_public_key", "device_execution_verified": False,
            "scope": "Future recordings only; existing ciphertext retains its original key."}

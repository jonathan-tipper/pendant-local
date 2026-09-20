"""Optional telemetry uses protobuf presence and never prevents basic status."""
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest

from pendant_api import device
from pendant_client.proto import server_pb2


def test_missing_submessages_are_not_false_readings():
    assert device.status_dict(server_pb2.DeviceStatus()) == {
        "recording": None, "battery": None, "storage": None, "wifi": None,
    }


def test_present_zero_enums_mean_stopped_and_discharging():
    status = server_pb2.DeviceStatus()
    status.recording_status.SetInParent()
    status.battery_status.SetInParent()
    parsed = device.status_dict(status)
    assert parsed["recording"]["state"] == "stopped"
    assert parsed["battery"]["state"] == "discharging"
    assert parsed["battery"]["usb"] == "disconnected"
    assert parsed["storage"] is None


def test_telemetry_is_allowlisted_and_power_units_are_not_invented():
    status = server_pb2.DeviceStatus()
    status.recording_status.recording_state = 1
    status.battery_status.state = 1
    status.battery_status.usb_state = 1
    status.battery_status.temperature = 2981
    status.wifi_status.state = 2
    status.wifi_status.rssi = -60
    status.wifi_status.ssid = "private-network"
    status.storage_state.total_capture_pages = 100
    status.storage_state.free_capture_pages = 75
    parsed = device.status_dict(status)
    assert parsed["recording"]["state"] == "recording"
    assert parsed["battery"]["temperature_raw"] == 2981
    assert parsed["battery"]["usb"] == "connected"
    assert parsed["storage"]["used_pages"] == 25
    assert parsed["wifi"] == {"state": "connected", "rssi": -60}
    assert "private-network" not in str(parsed)


@pytest.mark.parametrize("free,total", [(0, 0), (101, 100)])
def test_unusable_storage_counts_do_not_produce_usage(free, total):
    status = server_pb2.DeviceStatus()
    status.storage_state.free_capture_pages = free
    status.storage_state.total_capture_pages = total
    assert device.status_dict(status)["storage"]["used_pages"] is None


@pytest.mark.parametrize("extended", ["success", "timeout", "empty"])
async def test_info_prefers_snapshot_and_falls_back_to_embedded_status(monkeypatch, extended):
    raw = server_pb2.DeviceInfoMsg()
    raw.device_status.recording_status.recording_state = 2
    di = SimpleNamespace(device_id=1, serial_num="test", firmware_ver="test",
                         battery_percent=25, oldest_flash_page=0, newest_flash_page=0,
                         audio_encryption_pub_key=b"", raw=raw)
    closed = []

    class Session:
        async def get_device_info(self):
            return di

        async def get_device_status(self):
            if extended == "timeout":
                raise TimeoutError()
            value = server_pb2.DeviceStatus()
            if extended == "success":
                value.recording_status.recording_state = 1
            return value

    @asynccontextmanager
    async def connected(address):
        try:
            yield Session()
        finally:
            closed.append(True)

    monkeypatch.setattr(device, "connected", connected)
    result = await device.info("test-address")
    assert result["battery_percent"] == 25
    assert result["telemetry"]["recording"]["state"] == ("recording" if extended == "success" else "listening")
    assert result["telemetry_source"] == ("device_status" if extended == "success" else "device_info")
    assert ("status_warning" in result) == (extended == "timeout")
    assert result["checked_at"]
    assert closed == [True]

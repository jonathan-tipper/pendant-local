"""Clock gating, observed state and bounded BLE connection recovery."""
import asyncio
from contextlib import asynccontextmanager

from bleak.exc import BleakError
import pytest

from pendant_api import device
from pendant_client.proto import server_pb2


@pytest.fixture
def no_delay(monkeypatch):
    async def sleep(seconds):
        pass
    monkeypatch.setattr(device.asyncio, "sleep", sleep)


def control_session(monkeypatch, state=1, clock_error=None, status_error=False):
    events = []

    class Session:
        async def _request(self, **kwargs):
            events.append("clock")
            assert kwargs["set_current_time"].unix_timestamp_ms > 1700000000000
            if isinstance(clock_error, Exception):
                raise clock_error
            response = server_pb2.PendantAllMsg()
            if clock_error == "rejected":
                response.response_data.error.category = 1
            else:
                response.set_current_time_response.rtc_sync_session_number = 1
            return response

        async def start_recording(self):
            events.append("start")

        async def stop_recording(self):
            events.append("stop")

        async def get_device_status(self):
            events.append("status")
            if status_error:
                raise TimeoutError()
            response = server_pb2.DeviceStatus()
            response.recording_status.recording_state = state
            return response

    @asynccontextmanager
    async def connected(address):
        yield Session()

    monkeypatch.setattr(device, "connected", connected)
    return events


@pytest.mark.parametrize("state,label", [(1, "recording"), (2, "listening")])
async def test_start_syncs_clock_then_reports_observed_state(monkeypatch, no_delay, state, label):
    events = control_session(monkeypatch, state)
    result = await device.recording("TEST", True)
    assert events == ["clock", "start", "status"]
    assert result["device_execution_verified"] is True
    assert result["recording"]["state"] == label
    assert result["clock_synchronised"] is True


@pytest.mark.parametrize("failure", [TimeoutError(), "rejected"])
async def test_unconfirmed_clock_prevents_start(monkeypatch, no_delay, failure):
    events = control_session(monkeypatch, clock_error=failure)
    with pytest.raises(RuntimeError, match="not started"):
        await device.recording("TEST", True)
    assert events == ["clock"]


async def test_stop_does_not_depend_on_clock_sync(monkeypatch, no_delay):
    events = control_session(monkeypatch, state=0, clock_error=TimeoutError())
    result = await device.recording("TEST", False)
    assert events == ["stop", "status"]
    assert result["device_execution_verified"] is True
    assert result["recording"]["state"] == "stopped"


@pytest.mark.parametrize("state,status_error", [(0, False), (1, True)])
async def test_unconfirmed_start_is_not_reported_as_success(monkeypatch, no_delay, state, status_error):
    events = control_session(monkeypatch, state=state, status_error=status_error)
    result = await device.recording("TEST", True)
    assert events.count("start") == 1
    assert result["device_execution_verified"] is False
    assert result["warning"]


def connection_sessions(monkeypatch, failures):
    sessions = []

    class Session:
        def __init__(self, address):
            self.index = len(sessions)
            self._transport = None
            self._client = self
            self.disconnected = False
            sessions.append(self)

        async def __aenter__(self):
            if self.index < len(failures):
                raise failures[self.index]
            return self

        async def disconnect(self):
            self.disconnected = True

        async def __aexit__(self, *args):
            await self.disconnect()

    monkeypatch.setattr(device, "PendantSession", Session)
    return sessions


async def test_transient_connect_failure_is_cleaned_and_retried_once(monkeypatch, no_delay):
    sessions = connection_sessions(monkeypatch, [BleakError("Failed to encrypt the connection: timed out")])
    async with device.connected("TEST") as session:
        assert sessions[0].disconnected
        assert session.connection_attempts == 2
    assert len(sessions) == 2
    assert all(s.disconnected for s in sessions)


async def test_repeated_connect_failure_has_a_bound(monkeypatch, no_delay):
    sessions = connection_sessions(monkeypatch, [TimeoutError(), TimeoutError()])
    with pytest.raises(TimeoutError):
        async with device.connected("TEST"):
            pytest.fail("Should not enter operation")
    assert len(sessions) == 2
    assert all(s.disconnected for s in sessions)


@pytest.mark.parametrize("error", [BleakError("Bluetooth permission denied"), asyncio.CancelledError()])
async def test_permissions_and_cancellation_are_not_retried(monkeypatch, no_delay, error):
    sessions = connection_sessions(monkeypatch, [error])
    with pytest.raises(type(error)):
        async with device.connected("TEST"):
            pytest.fail("Should not enter operation")
    assert len(sessions) == 1
    assert sessions[0].disconnected


async def test_failure_after_connect_never_replays_the_operation(monkeypatch, no_delay):
    sessions = connection_sessions(monkeypatch, [])
    calls = 0
    with pytest.raises(BleakError):
        async with device.connected("TEST"):
            calls += 1
            raise BleakError("timed out after a command was sent")
    assert calls == 1
    assert len(sessions) == 1
    assert sessions[0].disconnected

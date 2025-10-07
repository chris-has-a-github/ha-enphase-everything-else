import pytest

pytest.importorskip("homeassistant")


def test_vpp_sensor_with_events():
    """Test VPP Events sensor shows event count with valid data."""
    from unittest.mock import MagicMock
    from custom_components.enphase_ev.coordinator import EnphaseCoordinator
    from custom_components.enphase_ev.sensor import EnphaseVPPEventsSensor

    # Create minimal coordinator stub
    coord = EnphaseCoordinator.__new__(EnphaseCoordinator)
    coord.site_id = "1234321"
    coord.vpp_program_id = "11ff22ee333ddd4444444c5b"
    coord.vpp_events_data = {
        "meta": {
            "serverTimeStamp": "2025-10-03T16:21:05.992+00:00",
            "rowCount": 2,
        },
        "data": [
            {
                "id": "68d061804996471ee129fa8a",
                "name": "Event 202509230000",
                "type": "battery_discharge",
                "status": "completed",
                "start_time": "2025-09-23T00:00:00.000+00:00",
                "end_time": "2025-09-23T03:00:00.000+00:00",
                "avg_kw_discharged": 3.525,
                "avg_kw_charged": 0.013,
            },
            {
                "id": "68d0617b4996471ee129f748",
                "name": "Event 202509222300",
                "type": "idle",
                "status": "completed",
                "start_time": "2025-09-22T23:00:00.000+00:00",
                "end_time": "2025-09-23T00:00:00.000+00:00",
                "avg_kw_discharged": 0.234,
                "avg_kw_charged": 0.027,
            },
        ],
        "error": {},
    }

    entry = MagicMock()
    entry.options = {}

    sensor = EnphaseVPPEventsSensor(coord, entry)
    assert sensor.native_value == 2
    assert sensor.extra_state_attributes["total_events"] == 2
    assert sensor.extra_state_attributes["program_id"] == "11ff22ee333ddd4444444c5b"
    assert sensor.extra_state_attributes["row_count"] == 2
    assert len(sensor.extra_state_attributes["recent_events"]) == 2
    assert sensor.extra_state_attributes["status_summary"]["completed"] == 2
    assert sensor.extra_state_attributes["type_summary"]["battery_discharge"] == 1
    assert sensor.extra_state_attributes["type_summary"]["idle"] == 1


def test_vpp_sensor_no_events():
    """Test VPP Events sensor when no events are present."""
    from unittest.mock import MagicMock
    from custom_components.enphase_ev.coordinator import EnphaseCoordinator
    from custom_components.enphase_ev.sensor import EnphaseVPPEventsSensor

    coord = EnphaseCoordinator.__new__(EnphaseCoordinator)
    coord.site_id = "1234321"
    coord.vpp_program_id = "11ff22ee333ddd4444444c5b"
    coord.vpp_events_data = {
        "meta": {"serverTimeStamp": "2025-10-03T16:21:05.992+00:00", "rowCount": 0},
        "data": [],
        "error": {},
    }

    entry = MagicMock()
    entry.options = {}

    sensor = EnphaseVPPEventsSensor(coord, entry)
    assert sensor.native_value == 0
    assert sensor.extra_state_attributes["total_events"] == 0


def test_vpp_sensor_no_data():
    """Test VPP Events sensor when no data is available."""
    from unittest.mock import MagicMock
    from custom_components.enphase_ev.coordinator import EnphaseCoordinator
    from custom_components.enphase_ev.sensor import EnphaseVPPEventsSensor

    coord = EnphaseCoordinator.__new__(EnphaseCoordinator)
    coord.site_id = "1234321"
    coord.vpp_program_id = "11ff22ee333ddd4444444c5b"
    coord.vpp_events_data = None

    entry = MagicMock()
    entry.options = {}

    sensor = EnphaseVPPEventsSensor(coord, entry)
    assert sensor.native_value == 0
    assert sensor.extra_state_attributes == {}


def test_vpp_sensor_status_summary():
    """Test VPP Events sensor creates status and type summaries."""
    from unittest.mock import MagicMock
    from custom_components.enphase_ev.coordinator import EnphaseCoordinator
    from custom_components.enphase_ev.sensor import EnphaseVPPEventsSensor

    coord = EnphaseCoordinator.__new__(EnphaseCoordinator)
    coord.site_id = "1234321"
    coord.vpp_program_id = "11ff22ee333ddd4444444c5b"
    coord.vpp_events_data = {
        "meta": {"rowCount": 4},
        "data": [
            {"id": "1", "status": "completed", "type": "battery_discharge"},
            {"id": "2", "status": "completed", "type": "battery_charge"},
            {"id": "3", "status": "failed", "type": "battery_discharge"},
            {"id": "4", "status": "completed", "type": "idle"},
        ],
    }

    entry = MagicMock()
    entry.options = {}

    sensor = EnphaseVPPEventsSensor(coord, entry)
    assert sensor.native_value == 4
    attrs = sensor.extra_state_attributes
    assert attrs["status_summary"]["completed"] == 3
    assert attrs["status_summary"]["failed"] == 1
    assert attrs["type_summary"]["battery_discharge"] == 2
    assert attrs["type_summary"]["battery_charge"] == 1
    assert attrs["type_summary"]["idle"] == 1


def test_vpp_event_today_binary_sensor():
    """Test VPP Event Today binary sensor."""
    from datetime import datetime, timezone
    from unittest.mock import MagicMock
    from custom_components.enphase_ev.binary_sensor import VPPEventTodayBinarySensor
    from custom_components.enphase_ev.coordinator import EnphaseCoordinator

    coord = EnphaseCoordinator.__new__(EnphaseCoordinator)
    coord.site_id = "1234321"
    coord.vpp_program_id = "11ff22ee333ddd4444444c5b"

    # Get today's date for testing
    today = datetime.now(timezone.utc)
    today_str = today.strftime("%Y-%m-%d")

    coord.vpp_events_data = {
        "data": [
            {
                "id": "event_today",
                "name": "Event Today",
                "type": "battery_discharge",
                "status": "scheduled",
                "start_time": f"{today_str}T18:00:00.000+00:00",
                "end_time": f"{today_str}T21:00:00.000+00:00",
                "target_soc": 10,
                "avg_kw_discharged": 3.5,
                "avg_kw_charged": 0.01,
            },
            {
                "id": "event_past",
                "name": "Event Past",
                "type": "battery_charge",
                "status": "completed",
                "start_time": "2025-01-01T00:00:00.000+00:00",
                "end_time": "2025-01-01T01:00:00.000+00:00",
            },
        ],
    }

    entry = MagicMock()
    entry.options = {}

    binary_sensor = VPPEventTodayBinarySensor(coord, entry)

    # Should be ON because there's an event today
    assert binary_sensor.is_on is True

    # Check attributes
    attrs = binary_sensor.extra_state_attributes
    assert attrs["event_count"] == 1
    assert len(attrs["events"]) == 1
    assert attrs["events"][0]["id"] == "event_today"
    assert attrs["events"][0]["name"] == "Event Today"


def test_vpp_event_today_binary_sensor_no_events():
    """Test VPP Event Today binary sensor with no events today."""
    from unittest.mock import MagicMock
    from custom_components.enphase_ev.binary_sensor import VPPEventTodayBinarySensor
    from custom_components.enphase_ev.coordinator import EnphaseCoordinator

    coord = EnphaseCoordinator.__new__(EnphaseCoordinator)
    coord.site_id = "1234321"
    coord.vpp_program_id = "11ff22ee333ddd4444444c5b"
    coord.vpp_events_data = {
        "data": [
            {
                "id": "event_past",
                "name": "Event Past",
                "type": "battery_charge",
                "status": "completed",
                "start_time": "2025-01-01T00:00:00.000+00:00",
                "end_time": "2025-01-01T01:00:00.000+00:00",
            },
        ],
    }

    entry = MagicMock()
    entry.options = {}

    binary_sensor = VPPEventTodayBinarySensor(coord, entry)

    # Should be OFF because there's no event today
    assert binary_sensor.is_on is False

    # Check attributes
    attrs = binary_sensor.extra_state_attributes
    assert attrs["event_count"] == 0
    assert len(attrs["events"]) == 0

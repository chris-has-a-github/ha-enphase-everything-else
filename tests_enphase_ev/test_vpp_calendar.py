from datetime import datetime, timezone

import pytest

pytest.importorskip("homeassistant")


def test_vpp_calendar_next_event():
    """Test VPP Calendar returns the next upcoming event."""
    from unittest.mock import MagicMock
    from custom_components.enphase_ev.calendar import EnphaseVPPCalendar
    from custom_components.enphase_ev.coordinator import EnphaseCoordinator

    coord = EnphaseCoordinator.__new__(EnphaseCoordinator)
    coord.site_id = "1234321"
    coord.vpp_program_id = "11ff22ee333ddd4444444c5b"
    coord.last_update_success = True
    coord.vpp_events_data = {
        "meta": {"rowCount": 2},
        "data": [
            {
                "id": "event1",
                "name": "Event Future",
                "type": "battery_discharge",
                "status": "scheduled",
                "start_time": "2025-12-01T00:00:00.000+00:00",
                "end_time": "2025-12-01T03:00:00.000+00:00",
                "target_soc": 10,
                "rate_watt": 11520,
                "avg_kw_discharged": 3.5,
                "avg_kw_charged": 0.01,
            },
            {
                "id": "event2",
                "name": "Event Past",
                "type": "battery_charge",
                "status": "completed",
                "start_time": "2025-09-01T00:00:00.000+00:00",
                "end_time": "2025-09-01T01:00:00.000+00:00",
                "target_soc": 100,
                "rate_watt": 11520,
            },
        ],
    }

    entry = MagicMock()
    entry.options = {}

    calendar = EnphaseVPPCalendar(coord, entry)
    event = calendar.event

    # Should return the future event, not the past one
    assert event is not None
    assert event.summary == "Battery Discharge - scheduled"
    assert "Event Future" in event.description
    assert event.uid == "event1"


async def test_vpp_calendar_get_events():
    """Test VPP Calendar async_get_events within date range."""
    from custom_components.enphase_ev.calendar import EnphaseVPPCalendar
    from custom_components.enphase_ev.coordinator import EnphaseCoordinator

    coord = EnphaseCoordinator.__new__(EnphaseCoordinator)
    coord.site_id = "1234321"
    coord.vpp_program_id = "11ff22ee333ddd4444444c5b"
    coord.last_update_success = True
    coord.vpp_events_data = {
        "meta": {"rowCount": 3},
        "data": [
            {
                "id": "event1",
                "name": "Event 1",
                "type": "battery_discharge",
                "status": "completed",
                "start_time": "2025-09-01T00:00:00.000+00:00",
                "end_time": "2025-09-01T03:00:00.000+00:00",
            },
            {
                "id": "event2",
                "name": "Event 2",
                "type": "battery_charge",
                "status": "completed",
                "start_time": "2025-09-15T00:00:00.000+00:00",
                "end_time": "2025-09-15T01:00:00.000+00:00",
            },
            {
                "id": "event3",
                "name": "Event 3",
                "type": "idle",
                "status": "scheduled",
                "start_time": "2025-10-01T00:00:00.000+00:00",
                "end_time": "2025-10-01T01:00:00.000+00:00",
            },
        ],
    }

    entry = MagicMock()
    entry.options = {}

    calendar = EnphaseVPPCalendar(coord, entry)

    # Request events for September 2025
    start = datetime(2025, 9, 1, tzinfo=timezone.utc)
    end = datetime(2025, 9, 30, tzinfo=timezone.utc)

    events = await calendar.async_get_events(None, start, end)

    # Should return 2 events from September
    assert len(events) == 2
    assert events[0].summary == "Battery Discharge - completed"
    assert events[1].summary == "Battery Charge - completed"


def test_vpp_calendar_no_data():
    """Test VPP Calendar with no data."""
    from unittest.mock import MagicMock
    from custom_components.enphase_ev.calendar import EnphaseVPPCalendar
    from custom_components.enphase_ev.coordinator import EnphaseCoordinator

    coord = EnphaseCoordinator.__new__(EnphaseCoordinator)
    coord.site_id = "1234321"
    coord.vpp_program_id = "11ff22ee333ddd4444444c5b"
    coord.last_update_success = True
    coord.vpp_events_data = None

    entry = MagicMock()
    entry.options = {}

    calendar = EnphaseVPPCalendar(coord, entry)
    event = calendar.event

    assert event is None


def test_vpp_calendar_event_description():
    """Test VPP Calendar event description includes details."""
    from unittest.mock import MagicMock
    from custom_components.enphase_ev.calendar import EnphaseVPPCalendar
    from custom_components.enphase_ev.coordinator import EnphaseCoordinator

    coord = EnphaseCoordinator.__new__(EnphaseCoordinator)
    coord.site_id = "1234321"
    coord.vpp_program_id = "11ff22ee333ddd4444444c5b"
    coord.last_update_success = True
    coord.vpp_events_data = {
        "data": [
            {
                "id": "event1",
                "name": "Test Event",
                "type": "battery_discharge",
                "subtype": "Discharge_To_Load_Grid",
                "status": "completed",
                "start_time": "2025-12-01T00:00:00.000+00:00",
                "end_time": "2025-12-01T03:00:00.000+00:00",
                "target_soc": 10,
                "rate_watt": 11520,
                "mode": "GS_TOU_MODE",
                "avg_kw_discharged": 3.525,
                "avg_kw_charged": 0.013,
            },
        ],
    }

    entry = MagicMock()
    entry.options = {}

    calendar = EnphaseVPPCalendar(coord, entry)
    event = calendar.event

    assert event is not None
    assert "Test Event" in event.description
    assert "Target SOC: 10%" in event.description
    assert "Rate: 11.5 kW" in event.description
    assert "Avg Discharged: 3.53 kW" in event.description
    assert "Avg Charged: 0.01 kW" in event.description
    assert "Mode: GS_TOU_MODE" in event.description
    assert "Type: Discharge_To_Load_Grid" in event.description

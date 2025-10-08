import pytest

pytest.importorskip("homeassistant")


def test_savings_imported_sensor():
    """Test Savings Imported Today sensor with valid data."""
    from unittest.mock import MagicMock
    from custom_components.enphase_cloud_things.coordinator import EnphaseCoordinator
    from custom_components.enphase_cloud_things.sensor import EnphaseSavingsImportedTodaySensor

    coord = EnphaseCoordinator.__new__(EnphaseCoordinator)
    coord.site_id = "1234321"
    coord.savings_data = {
        "type": "monetary-data",
        "timestamp": "2025-10-03T16:08:26.382643491Z",
        "data": {
            "startDate": "2025-10-03",
            "endDate": "2025-10-03",
            "energy": {"imported": 1990, "exported": 105},
            "monetary": {"imported": 0.671, "exported": 0.007},
        },
    }

    entry = MagicMock()
    entry.options = {}

    sensor = EnphaseSavingsImportedTodaySensor(coord, entry)
    assert sensor.native_value == 0.67
    assert sensor.native_unit_of_measurement == "USD"
    assert sensor.extra_state_attributes["energy_imported_wh"] == 1990
    assert sensor.extra_state_attributes["date"] == "2025-10-03"


def test_savings_imported_sensor_rounding():
    """Test Savings Imported Today sensor rounds to 2 decimals."""
    from unittest.mock import MagicMock
    from custom_components.enphase_cloud_things.coordinator import EnphaseCoordinator
    from custom_components.enphase_cloud_things.sensor import EnphaseSavingsImportedTodaySensor

    coord = EnphaseCoordinator.__new__(EnphaseCoordinator)
    coord.site_id = "1234321"
    coord.savings_data = {
        "data": {
            "monetary": {"imported": 15.6789},
        },
    }

    entry = MagicMock()
    entry.options = {}

    sensor = EnphaseSavingsImportedTodaySensor(coord, entry)
    assert sensor.native_value == 15.68


def test_savings_imported_sensor_no_data():
    """Test Savings Imported Today sensor with no data."""
    from unittest.mock import MagicMock
    from custom_components.enphase_cloud_things.coordinator import EnphaseCoordinator
    from custom_components.enphase_cloud_things.sensor import EnphaseSavingsImportedTodaySensor

    coord = EnphaseCoordinator.__new__(EnphaseCoordinator)
    coord.site_id = "1234321"
    coord.savings_data = None

    entry = MagicMock()
    entry.options = {}

    sensor = EnphaseSavingsImportedTodaySensor(coord, entry)
    assert sensor.native_value is None


def test_savings_exported_sensor():
    """Test Savings Exported Today sensor with valid data."""
    from unittest.mock import MagicMock
    from custom_components.enphase_cloud_things.coordinator import EnphaseCoordinator
    from custom_components.enphase_cloud_things.sensor import EnphaseSavingsExportedTodaySensor

    coord = EnphaseCoordinator.__new__(EnphaseCoordinator)
    coord.site_id = "1234321"
    coord.savings_data = {
        "type": "monetary-data",
        "timestamp": "2025-10-03T16:08:26.382643491Z",
        "data": {
            "startDate": "2025-10-03",
            "endDate": "2025-10-03",
            "energy": {"imported": 1990, "exported": 105},
            "monetary": {"imported": 0.671, "exported": 0.007},
        },
    }

    entry = MagicMock()
    entry.options = {}

    sensor = EnphaseSavingsExportedTodaySensor(coord, entry)
    assert sensor.native_value == 0.01
    assert sensor.native_unit_of_measurement == "USD"
    assert sensor.extra_state_attributes["energy_exported_wh"] == 105
    assert sensor.extra_state_attributes["date"] == "2025-10-03"


def test_savings_exported_sensor_rounding():
    """Test Savings Exported Today sensor rounds to 2 decimals."""
    from unittest.mock import MagicMock
    from custom_components.enphase_cloud_things.coordinator import EnphaseCoordinator
    from custom_components.enphase_cloud_things.sensor import EnphaseSavingsExportedTodaySensor

    coord = EnphaseCoordinator.__new__(EnphaseCoordinator)
    coord.site_id = "1234321"
    coord.savings_data = {
        "data": {
            "monetary": {"exported": 5.256},
        },
    }

    entry = MagicMock()
    entry.options = {}

    sensor = EnphaseSavingsExportedTodaySensor(coord, entry)
    assert sensor.native_value == 5.26


def test_savings_exported_sensor_no_data():
    """Test Savings Exported Today sensor with no data."""
    from unittest.mock import MagicMock
    from custom_components.enphase_cloud_things.coordinator import EnphaseCoordinator
    from custom_components.enphase_cloud_things.sensor import EnphaseSavingsExportedTodaySensor

    coord = EnphaseCoordinator.__new__(EnphaseCoordinator)
    coord.site_id = "1234321"
    coord.savings_data = None

    entry = MagicMock()
    entry.options = {}

    sensor = EnphaseSavingsExportedTodaySensor(coord, entry)
    assert sensor.native_value is None

import json
import pathlib


def test_manifest_keys_present():
    manifest_path = pathlib.Path(__file__).parents[1] / "custom_components" / "enphase_cloud_things" / "manifest.json"
    raw = manifest_path.read_text()
    data = json.loads(raw)

    assert data.get("version"), "manifest must include version"
    assert data.get("config_flow") is True, "config_flow must be true"
    assert data.get("integration_type") == "hub", "integration_type should be 'hub'"
    assert data.get("iot_class") == "cloud_polling", "iot_class should be 'cloud_polling'"

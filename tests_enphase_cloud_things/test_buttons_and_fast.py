import pytest


@pytest.mark.asyncio
async def test_start_stop_buttons_press(hass, monkeypatch):
    from custom_components.enphase_cloud_things.button import StartChargeButton, StopChargeButton
    from custom_components.enphase_cloud_things.const import (
        CONF_COOKIE,
        CONF_EAUTH,
        CONF_SCAN_INTERVAL,
        CONF_SERIALS,
        CONF_SITE_ID,
    )
    from custom_components.enphase_cloud_things.coordinator import EnphaseCoordinator

    cfg = {
        CONF_SITE_ID: "3381244",
        CONF_SERIALS: ["482522020944"],
        CONF_EAUTH: "EAUTH",
        CONF_COOKIE: "COOKIE",
        CONF_SCAN_INTERVAL: 30,
    }
    from custom_components.enphase_cloud_things import coordinator as coord_mod
    monkeypatch.setattr(coord_mod, "async_get_clientsession", lambda *args, **kwargs: object())
    coord = EnphaseCoordinator(hass, cfg)
    sn = "482522020944"
    coord.data = {sn: {"name": "Garage EV", "charging": False}}
    coord.last_set_amps = {}

    class StubClient:
        def __init__(self):
            self.start_calls = []
            self.stop_calls = []
        async def start_charging(self, s, amps, connector_id=1):
            self.start_calls.append((s, amps, connector_id))
            return {"status": "ok"}
        async def stop_charging(self, s):
            self.stop_calls.append(s)
            return {"status": "ok"}

    coord.client = StubClient()

    # Avoid debouncer refresh
    async def _noop():
        return None
    coord.async_request_refresh = _noop  # type: ignore

    start_btn = StartChargeButton(coord, sn)
    stop_btn = StopChargeButton(coord, sn)

    # Start button uses default 32A when none set
    await start_btn.async_press()
    assert coord.client.start_calls[-1] == (sn, 32, 1)
    # Stop button calls API
    await stop_btn.async_press()
    assert coord.client.stop_calls[-1] == sn


@pytest.mark.asyncio
async def test_kick_fast_window(hass, monkeypatch):
    from custom_components.enphase_cloud_things.const import (
        CONF_COOKIE,
        CONF_EAUTH,
        CONF_SCAN_INTERVAL,
        CONF_SERIALS,
        CONF_SITE_ID,
        OPT_FAST_POLL_INTERVAL,
        OPT_SLOW_POLL_INTERVAL,
    )
    from custom_components.enphase_cloud_things.coordinator import EnphaseCoordinator

    cfg = {
        CONF_SITE_ID: "3381244",
        CONF_SERIALS: ["482522020944"],
        CONF_EAUTH: "EAUTH",
        CONF_COOKIE: "COOKIE",
        CONF_SCAN_INTERVAL: 15,
    }

    class DummyEntry:
        def __init__(self, options):
            self.options = options
        def async_on_unload(self, cb):
            return None

    options = {OPT_FAST_POLL_INTERVAL: 5, OPT_SLOW_POLL_INTERVAL: 20}
    entry = DummyEntry(options)
    from custom_components.enphase_cloud_things import coordinator as coord_mod
    monkeypatch.setattr(coord_mod, "async_get_clientsession", lambda *args, **kwargs: object())
    coord = EnphaseCoordinator(hass, cfg, config_entry=entry)

    class StubClient:
        def __init__(self, payload):
            self._payload = payload
        async def status(self):
            return self._payload

    # Idle payload (would normally be slow)
    payload_idle = {
        "evChargerData": [
            {"sn": "482522020944", "name": "Garage EV", "charging": False, "pluggedIn": True}
        ]
    }
    coord.client = StubClient(payload_idle)

    # Trigger fast window explicitly
    coord.kick_fast(60)
    await coord._async_update_data()
    assert int(coord.update_interval.total_seconds()) == 5

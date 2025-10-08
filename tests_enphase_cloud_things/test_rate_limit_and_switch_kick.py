import aiohttp
import pytest


@pytest.mark.asyncio
async def test_rate_limit_issue_created_on_repeated_429(hass, monkeypatch):
    from homeassistant.helpers.update_coordinator import UpdateFailed

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
        CONF_SCAN_INTERVAL: 15,
    }
    from custom_components.enphase_cloud_things import coordinator as coord_mod
    # Stub HA session
    monkeypatch.setattr(coord_mod, "async_get_clientsession", lambda *args, **kwargs: object())
    coord = EnphaseCoordinator(hass, cfg)

    # Stub ClientResponseError for 429
    class StubRespErr(aiohttp.ClientResponseError):
        def __init__(self, status, headers=None):
            req = aiohttp.RequestInfo(url=aiohttp.client.URL("https://example"), method="GET", headers={}, real_url=aiohttp.client.URL("https://example"))
            super().__init__(request_info=req, history=(), status=status, message="", headers=headers or {})

    class StubClient:
        async def status(self):
            raise StubRespErr(429, headers={"Retry-After": "1"})

    coord.client = StubClient()

    # Capture issue creation calls
    created = []
    monkeypatch.setattr(coord_mod.ir, "async_create_issue", lambda *args, **kwargs: created.append(kwargs))

    # First 429 -> backoff, no issue yet
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()
    assert created == []

    # Second 429 -> create rate_limited issue
    # Clear backoff to force a second call that hits 429 again
    coord._backoff_until = None
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()
    assert any(k.get("translation_key") == "rate_limited" for k in created)


@pytest.mark.asyncio
async def test_backoff_blocks_updates(hass, monkeypatch):
    import time

    from homeassistant.helpers.update_coordinator import UpdateFailed

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
        CONF_SCAN_INTERVAL: 15,
    }
    from custom_components.enphase_cloud_things import coordinator as coord_mod
    monkeypatch.setattr(coord_mod, "async_get_clientsession", lambda *args, **kwargs: object())
    coord = EnphaseCoordinator(hass, cfg)

    # Force a backoff window
    coord._backoff_until = time.monotonic() + 100

    with pytest.raises(UpdateFailed):
        # Should raise immediately due to backoff without calling client
        await coord._async_update_data()


@pytest.mark.asyncio
async def test_latency_ms_set_on_success_and_failure(hass, monkeypatch):
    import asyncio

    from homeassistant.helpers.update_coordinator import UpdateFailed

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
        CONF_SCAN_INTERVAL: 15,
    }
    from custom_components.enphase_cloud_things import coordinator as coord_mod
    monkeypatch.setattr(coord_mod, "async_get_clientsession", lambda *args, **kwargs: object())
    coord = EnphaseCoordinator(hass, cfg)

    class GoodClient:
        async def status(self):
            return {"evChargerData": []}

    coord.client = GoodClient()
    await coord._async_update_data()
    assert isinstance(coord.latency_ms, int)
    assert coord.latency_ms >= 0

    class BadClient:
        async def status(self):
            await asyncio.sleep(0)
            raise asyncio.TimeoutError()

    coord.client = BadClient()
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()
    # latency should still be set in finally
    assert isinstance(coord.latency_ms, int)

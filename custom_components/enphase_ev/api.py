
from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from typing import Any, Iterable

import aiohttp
import async_timeout

from .const import (
    BASE_URL,
    DEFAULT_AUTH_TIMEOUT,
    ENTREZ_URL,
    LOGIN_URL,
)

_LOGGER = logging.getLogger(__name__)


class Unauthorized(Exception):
    pass


class EnlightenAuthError(Exception):
    """Base exception for Enlighten authentication failures."""


class EnlightenAuthInvalidCredentials(EnlightenAuthError):
    """Raised when credentials are rejected."""


class EnlightenAuthMFARequired(EnlightenAuthError):
    """Raised when the API signals multi-factor authentication is required."""


class EnlightenAuthUnavailable(EnlightenAuthError):
    """Raised when the service is temporarily unavailable."""


class EnlightenTokenUnavailable(EnlightenAuthError):
    """Raised when a bearer token cannot be obtained for the account."""


@dataclass
class AuthTokens:
    """Container for Enlighten authentication state."""

    cookie: str
    session_id: str | None = None
    access_token: str | None = None
    token_expires_at: int | None = None
    raw_cookies: dict[str, str] | None = None


@dataclass
class SiteInfo:
    """Basic representation of an Enlighten site."""

    site_id: str
    name: str | None = None


@dataclass
class ChargerInfo:
    """Metadata about a charger discovered for a site."""

    serial: str
    name: str | None = None


def _serialize_cookie_jar(jar: aiohttp.CookieJar, urls: Iterable[str]) -> tuple[str, dict[str, str]]:
    """Return a Cookie header string and mapping extracted from the jar."""

    cookies: dict[str, str] = {}
    for url in urls:
        try:
            filtered = jar.filter_cookies(url)
        except Exception:  # noqa: BLE001 - defensive: filter_cookies may raise
            continue
        for key, morsel in filtered.items():
            cookies[key] = morsel.value
    header = "; ".join(f"{k}={v}" for k, v in cookies.items())
    return header, cookies


def _decode_jwt_exp(token: str) -> int | None:
    """Decode the exp claim from a JWT-like token without validation."""

    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1]
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
    except Exception:  # noqa: BLE001 - defensive parsing
        return None
    exp = payload.get("exp")
    if isinstance(exp, (int, float)):
        return int(exp)
    return None


async def _request_json(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    *,
    timeout: int,
    headers: dict[str, str] | None = None,
    data: Any | None = None,
    json_data: Any | None = None,
) -> Any:
    """Perform an HTTP request returning JSON with timeout handling."""

    req_kwargs: dict[str, Any] = {}
    if headers is not None:
        req_kwargs["headers"] = headers
    if data is not None:
        req_kwargs["data"] = data
    if json_data is not None:
        req_kwargs["json"] = json_data

    async with async_timeout.timeout(timeout):
        async with session.request(method, url, allow_redirects=True, **req_kwargs) as resp:
            if resp.status >= 500:
                raise EnlightenAuthUnavailable(f"Server error {resp.status} at {url}")
            resp.raise_for_status()
            ctype = resp.headers.get("Content-Type", "")
            if "json" not in ctype:
                text = await resp.text()
                raise EnlightenAuthUnavailable(
                    f"Unexpected response content-type {ctype!r} at {url}: {text[:120]}"
                )
            return await resp.json()


def _normalize_sites(payload: Any) -> list[SiteInfo]:
    """Normalize site payloads from various Enlighten APIs."""

    sites: list[SiteInfo] = []

    if isinstance(payload, dict):
        for key in ("sites", "data", "items"):
            nested = payload.get(key)
            if isinstance(nested, list):
                payload = nested
                break

    if isinstance(payload, list):
        items = payload
    else:
        items = []

    for item in items:
        if not isinstance(item, dict):
            continue
        site_id = item.get("site_id") or item.get("siteId") or item.get("id")
        name = item.get("name") or item.get("site_name") or item.get("siteName")
        if site_id is None:
            continue
        sites.append(SiteInfo(site_id=str(site_id), name=str(name) if name else None))
    return sites


def _normalize_chargers(payload: Any) -> list[ChargerInfo]:
    """Normalize charger list payloads into ChargerInfo entries."""

    chargers: list[ChargerInfo] = []

    if isinstance(payload, dict):
        payload = payload.get("data") or payload

    if isinstance(payload, dict):
        # Some responses use { "chargers": [...] }
        payload = payload.get("chargers") or payload.get("evChargerData") or payload

    if isinstance(payload, list):
        items = payload
    else:
        items = []

    for item in items:
        if not isinstance(item, dict):
            continue
        serial = (
            item.get("serial")
            or item.get("serialNumber")
            or item.get("sn")
            or item.get("id")
        )
        if not serial:
            continue
        name = item.get("name") or item.get("displayName") or item.get("display_name")
        chargers.append(ChargerInfo(serial=str(serial), name=str(name) if name else None))
    return chargers


async def async_authenticate(
    session: aiohttp.ClientSession,
    email: str,
    password: str,
    *,
    timeout: int = DEFAULT_AUTH_TIMEOUT,
) -> tuple[AuthTokens, list[SiteInfo]]:
    """Authenticate with Enlighten and return auth tokens and accessible sites."""

    payload = {"user[email]": email, "user[password]": password}
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    try:
        data = await _request_json(
            session,
            "POST",
            LOGIN_URL,
            timeout=timeout,
            headers=headers,
            data=payload,
        )
    except aiohttp.ClientResponseError as err:
        if err.status in (401, 403):
            raise EnlightenAuthInvalidCredentials from err
        raise
    except aiohttp.ClientError as err:  # noqa: BLE001
        raise EnlightenAuthUnavailable from err

    if isinstance(data, dict) and data.get("requires_mfa"):
        raise EnlightenAuthMFARequired("Account requires multi-factor authentication")

    session_id = None
    if isinstance(data, dict):
        session_id = (
            data.get("session_id")
            or data.get("sessionId")
            or data.get("session")
        )

    cookie_header, cookie_map = _serialize_cookie_jar(
        session.cookie_jar, (BASE_URL, ENTREZ_URL)
    )
    tokens = AuthTokens(
        cookie=cookie_header,
        session_id=str(session_id) if session_id else None,
        raw_cookies=cookie_map,
    )

    # Attempt to obtain a bearer/e-auth token. If not available, proceed with cookie-only mode.
    token_payload: Any | None = None
    if tokens.session_id:
        try:
            token_payload = await _request_json(
                session,
                "POST",
                f"{ENTREZ_URL}/tokens",
                timeout=timeout,
                headers={"Accept": "application/json"},
                json_data={"session_id": tokens.session_id, "email": email},
            )
        except aiohttp.ClientResponseError as err:  # noqa: BLE001
            if err.status in (401, 403):
                raise EnlightenAuthInvalidCredentials from err
            if err.status in (404, 422, 429):
                _LOGGER.debug("Token endpoint unavailable (%s): %s", err.status, err)
            else:
                _LOGGER.debug("Token endpoint error (%s): %s", err.status, err)
        except EnlightenAuthUnavailable as err:
            _LOGGER.debug("Token endpoint unavailable: %s", err)
        except aiohttp.ClientError as err:  # noqa: BLE001
            _LOGGER.debug("Token endpoint client error: %s", err)

    if isinstance(token_payload, dict):
        token = (
            token_payload.get("token")
            or token_payload.get("auth_token")
            or token_payload.get("access_token")
        )
        if token:
            tokens.access_token = str(token)
            exp = (
                token_payload.get("expires_at")
                or token_payload.get("expiresAt")
                or token_payload.get("expiration")
            )
            if exp is None:
                exp = _decode_jwt_exp(tokens.access_token)
            tokens.token_expires_at = int(exp) if isinstance(exp, (int, float)) else None

    # Collect accessible sites for the authenticated user.
    sites: list[SiteInfo] = []
    for url in (
        f"{BASE_URL}/service/evse_controller/sites",
        f"{BASE_URL}/service/evse_controller/api/v1/sites",
        f"{BASE_URL}/service/evse_controller/sites.json",
    ):
        try:
            site_payload = await _request_json(
                session,
                "GET",
                url,
                timeout=timeout,
                headers={"Accept": "application/json"},
            )
        except aiohttp.ClientResponseError as err:
            if err.status in (401, 403):
                raise EnlightenAuthInvalidCredentials from err
            _LOGGER.debug("Site discovery endpoint error (%s): %s", err.status, err)
            continue
        except EnlightenAuthUnavailable as err:
            _LOGGER.debug("Site discovery unavailable: %s", err)
            continue
        except aiohttp.ClientError as err:  # noqa: BLE001
            _LOGGER.debug("Site discovery client error: %s", err)
            continue
        sites = _normalize_sites(site_payload)
        if sites:
            break

    return tokens, sites


async def async_fetch_chargers(
    session: aiohttp.ClientSession,
    site_id: str,
    tokens: AuthTokens,
    *,
    timeout: int = DEFAULT_AUTH_TIMEOUT,
) -> list[ChargerInfo]:
    """Fetch chargers for a site using the provided authentication tokens."""

    if not site_id:
        return []

    client = EnphaseEVClient(
        session,
        site_id,
        tokens.access_token,
        tokens.cookie,
        timeout=timeout,
    )
    try:
        payload = await client.summary_v2()
    except Exception as err:  # noqa: BLE001 - propagate as empty list for flow UX
        _LOGGER.debug("Failed to fetch charger summary for site %s: %s", site_id, err)
        return []
    return _normalize_chargers(payload)

class EnphaseEVClient:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        site_id: str,
        eauth: str | None,
        cookie: str | None,
        timeout: int = 15,
    ):
        self._timeout = int(timeout)
        self._s = session
        self._site = site_id
        # Cache working API variant indexes per action to avoid retries once discovered
        self._start_variant_idx: int | None = None
        self._stop_variant_idx: int | None = None
        self._cookie = cookie or ""
        self._eauth = eauth or None
        self._h = {
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{BASE_URL}/pv/systems/{site_id}/summary",
        }
        self.update_credentials(eauth=eauth, cookie=cookie)

    def update_credentials(self, *, eauth: str | None = None, cookie: str | None = None) -> None:
        """Update headers when auth credentials change."""

        if eauth is not None:
            self._eauth = eauth or None
        if cookie is not None:
            self._cookie = cookie or ""

        if self._cookie:
            self._h["Cookie"] = self._cookie
        else:
            self._h.pop("Cookie", None)

        if self._eauth:
            self._h["e-auth-token"] = self._eauth
        else:
            self._h.pop("e-auth-token", None)

        # If XSRF-TOKEN cookie is present, add matching CSRF header some endpoints expect
        try:
            xsrf = None
            parts = [p.strip() for p in (self._cookie or "").split(";")]
            for p in parts:
                if p.startswith("XSRF-TOKEN="):
                    xsrf = p.split("=", 1)[1]
                    break
            if xsrf:
                self._h["X-CSRF-Token"] = xsrf
            else:
                self._h.pop("X-CSRF-Token", None)
        except Exception:
            self._h.pop("X-CSRF-Token", None)

    def _bearer(self) -> str | None:
        """Extract Authorization bearer token from cookies if present.

        Enlighten sets an `enlighten_manager_token_production` cookie with a JWT the
        frontend uses as an Authorization Bearer token for some scheduler endpoints.
        """
        try:
            parts = [p.strip() for p in (self._cookie or "").split(";")]
            for p in parts:
                if p.startswith("enlighten_manager_token_production="):
                    return p.split("=", 1)[1]
        except Exception:
            return None
        return None

    async def _json(self, method: str, url: str, **kwargs):
        """Perform an HTTP request returning JSON with sane header handling.

        Accepts optional ``headers`` in kwargs which will be merged with the
        default headers for this client, allowing call-sites to add/override
        fields (e.g. Authorization) without causing duplicate parameter errors.
        """
        # Merge headers: start with client defaults, then apply any overrides
        base_headers = dict(self._h)
        extra_headers = kwargs.pop("headers", None)
        if isinstance(extra_headers, dict):
            base_headers.update(extra_headers)

        async with async_timeout.timeout(self._timeout):
            async with self._s.request(method, url, headers=base_headers, **kwargs) as r:
                if r.status == 401:
                    raise Unauthorized()
                r.raise_for_status()
                return await r.json()

    async def status(self) -> dict:
        url = f"{BASE_URL}/service/evse_controller/{self._site}/ev_chargers/status"
        data = await self._json("GET", url)
        # Normalize alternative shapes
        if not (data.get("evChargerData") or []):
            alt = f"{BASE_URL}/service/evse_controller/{self._site}/ev_charger/status"
            try:
                data2 = await self._json("GET", alt)
                if data2:
                    data = data2
            except Exception:
                pass

        # If response is { data: { chargers: [...] } }, map to evChargerData
        try:
            inner = data.get("data") if isinstance(data, dict) else None
            chargers = inner.get("chargers") if isinstance(inner, dict) else None
            if isinstance(chargers, list) and chargers:
                out = []
                for c in chargers:
                    conn = (c.get("connectors") or [{}])[0]
                    sess = c.get("session_d") or {}
                    # Derive start_time in seconds (strt_chrg appears in ms)
                    start_ms = sess.get("strt_chrg")
                    start_sec = int(int(start_ms) / 1000) if isinstance(start_ms, int) else None
                    out.append(
                        {
                            "sn": c.get("sn"),
                            "name": c.get("name"),
                            "connected": bool(c.get("connected")),
                            "pluggedIn": bool(c.get("pluggedIn") or conn.get("pluggedIn")),
                            "charging": bool(c.get("charging")),
                            "faulted": bool(c.get("faulted")),
                            "connectorStatusType": conn.get("connectorStatusType"),
                            "session_d": {
                                "e_c": sess.get("e_c"),
                                "start_time": start_sec,
                            },
                        }
                    )
                return {"evChargerData": out, "ts": data.get("meta", {}).get("serverTimeStamp")}
        except Exception:
            # If mapping fails, fall back to raw
            pass

        return data

    async def start_charging(self, sn: str, amps: int, connector_id: int = 1) -> dict:
        """Start charging or set the charging level.

        The Enlighten API has variations across deployments (method, path, and payload keys).
        We try a sequence of known variants until one succeeds.
        """
        level = int(amps)
        candidates = [
            (
                "POST",
                f"{BASE_URL}/service/evse_controller/{self._site}/ev_chargers/{sn}/start_charging",
                {"chargingLevel": level, "connectorId": connector_id},
            ),
            (
                "PUT",
                f"{BASE_URL}/service/evse_controller/{self._site}/ev_chargers/{sn}/start_charging",
                {"chargingLevel": level, "connectorId": connector_id},
            ),
            (
                "POST",
                f"{BASE_URL}/service/evse_controller/{self._site}/ev_charger/{sn}/start_charging",
                {"chargingLevel": level, "connectorId": connector_id},
            ),
            (
                "POST",
                f"{BASE_URL}/service/evse_controller/{self._site}/ev_chargers/{sn}/start_charging",
                {"charging_level": level, "connector_id": connector_id},
            ),
            (
                "POST",
                f"{BASE_URL}/service/evse_controller/{self._site}/ev_chargers/{sn}/start_charging",
                {"connectorId": connector_id},
            ),
            (
                "POST",
                f"{BASE_URL}/service/evse_controller/{self._site}/ev_chargers/{sn}/start_charging",
                None,
            ),
            (
                "POST",
                f"{BASE_URL}/service/evse_controller/{self._site}/ev_charger/{sn}/start_charging",
                None,
            ),
            (
                "POST",
                f"{BASE_URL}/service/evse_controller/{self._site}/ev_chargers/{sn}/start_charging",
                {"chargingLevel": level},
            ),
        ]
        # If we have a known working variant, try it first
        order = list(range(len(candidates)))
        if self._start_variant_idx is not None and 0 <= self._start_variant_idx < len(candidates):
            order.remove(self._start_variant_idx)
            order.insert(0, self._start_variant_idx)

        last_exc: Exception | None = None
        for idx in order:
            method, url, payload = candidates[idx]
            try:
                if payload is None:
                    result = await self._json(method, url)
                else:
                    result = await self._json(method, url, json=payload)
                # Cache the working variant index for future calls
                self._start_variant_idx = idx
                return result
            except aiohttp.ClientResponseError as e:
                # 409/422 (and similar) often indicate not plugged in or not ready.
                # Treat these as benign no-ops instead of surfacing as errors.
                if e.status in (409, 422):
                    self._start_variant_idx = idx
                    return {"status": "not_ready"}
                # 400/404/405 variations likely indicate method/path mismatch; try next.
                last_exc = e
                continue
        if last_exc:
            raise last_exc
        # Should not happen, but keep static analyzer happy
        raise aiohttp.ClientError("start_charging failed with all variants")

    async def stop_charging(self, sn: str) -> dict:
        """Stop charging; try multiple endpoint variants."""
        candidates = [
            ("PUT",  f"{BASE_URL}/service/evse_controller/{self._site}/ev_chargers/{sn}/stop_charging", None),
            ("POST", f"{BASE_URL}/service/evse_controller/{self._site}/ev_chargers/{sn}/stop_charging", None),
            ("POST", f"{BASE_URL}/service/evse_controller/{self._site}/ev_charger/{sn}/stop_charging", None),
        ]
        order = list(range(len(candidates)))
        if self._stop_variant_idx is not None and 0 <= self._stop_variant_idx < len(candidates):
            order.remove(self._stop_variant_idx)
            order.insert(0, self._stop_variant_idx)

        last_exc: Exception | None = None
        for idx in order:
            method, url, payload = candidates[idx]
            try:
                if payload is None:
                    result = await self._json(method, url)
                else:
                    result = await self._json(method, url, json=payload)
                self._stop_variant_idx = idx
                return result
            except aiohttp.ClientResponseError as e:
                # If charger is not plugged in or already stopped, some backends
                # respond with 400/404/409. Treat these as benign no-ops.
                if e.status in (400, 404, 409, 422):
                    self._stop_variant_idx = idx  # cache the working path even if no-op
                    return {"status": "not_active"}
                last_exc = e
                continue
        if last_exc:
            raise last_exc
        raise aiohttp.ClientError("stop_charging failed with all variants")

    async def trigger_message(self, sn: str, requested_message: str) -> dict:
        url = f"{BASE_URL}/service/evse_controller/{self._site}/ev_charger/{sn}/trigger_message"
        payload = {"requestedMessage": requested_message}
        return await self._json("POST", url, json=payload)

    async def start_live_stream(self) -> dict:
        url = f"{BASE_URL}/service/evse_controller/{self._site}/ev_chargers/start_live_stream"
        return await self._json("GET", url)

    async def stop_live_stream(self) -> dict:
        url = f"{BASE_URL}/service/evse_controller/{self._site}/ev_chargers/stop_live_stream"
        return await self._json("GET", url)

    async def charge_mode(self, sn: str) -> str | None:
        """Fetch the current charge mode via scheduler API.

        GET /service/evse_scheduler/api/v1/iqevc/charging-mode/<site>/<sn>/preference
        Requires Authorization: Bearer <jwt> in addition to existing cookies.
        Returns one of: GREEN_CHARGING, SCHEDULED_CHARGING, MANUAL_CHARGING when enabled.
        """
        url = f"{BASE_URL}/service/evse_scheduler/api/v1/iqevc/charging-mode/{self._site}/{sn}/preference"
        headers = dict(self._h)
        bearer = self._bearer()
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        data = await self._json("GET", url, headers=headers)
        try:
            modes = (data.get("data") or {}).get("modes") or {}
            # Prefer the mode whose 'enabled' is true
            for key in ("greenCharging", "scheduledCharging", "manualCharging"):
                m = modes.get(key)
                if isinstance(m, dict) and m.get("enabled"):
                    return m.get("chargingMode")
        except Exception:
            return None
        return None

    async def set_charge_mode(self, sn: str, mode: str) -> dict:
        """Set the charging mode via scheduler API.

        PUT /service/evse_scheduler/api/v1/iqevc/charging-mode/<site>/<sn>/preference
        Body: { "mode": "MANUAL_CHARGING" | "SCHEDULED_CHARGING" | "GREEN_CHARGING" }
        """
        url = f"{BASE_URL}/service/evse_scheduler/api/v1/iqevc/charging-mode/{self._site}/{sn}/preference"
        headers = dict(self._h)
        bearer = self._bearer()
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        payload = {"mode": str(mode)}
        return await self._json("PUT", url, json=payload, headers=headers)

    async def summary_v2(self) -> list[dict] | None:
        """Fetch charger summary v2 list.

        GET /service/evse_controller/api/v2/<site_id>/ev_chargers/summary?filter_retired=true
        Returns a list of charger objects with serialNumber and other properties.
        """
        url = f"{BASE_URL}/service/evse_controller/api/v2/{self._site}/ev_chargers/summary?filter_retired=true"
        data = await self._json("GET", url)
        try:
            return data.get("data") or []
        except Exception:
            return None

    async def vpp_events(self, program_id: str, start_date: str = "", end_date: str = "",
                        sort_by: str = "", ascending: str = "", time: str = "") -> dict:
        """Fetch VPP (Virtual Power Plant) events.

        GET https://gs.enphaseenergy.com/vpp-mgr/api/v1/events/get
        Query params: site_id, programId, start_date, end_date, sort_by, ascending, time
        Returns VPP event data for the site.
        Requires Authorization: Bearer token from cookies.
        """
        url = f"https://gs.enphaseenergy.com/vpp-mgr/api/v1/events/get"
        params = {
            "site_id": self._site,
            "programId": program_id,
            "start_date": start_date,
            "end_date": end_date,
            "sort_by": sort_by,
            "ascending": ascending,
            "time": time,
        }
        # Keep all parameters including empty ones as the API expects them
        from urllib.parse import urlencode
        query_string = urlencode(params)
        full_url = f"{url}?{query_string}"

        # VPP endpoint requires the JWT token directly as Authorization (not "Bearer {token}")
        headers = dict(self._h)
        bearer = self._bearer()
        if bearer:
            headers["Authorization"] = bearer  # Raw JWT, no "Bearer" prefix
            headers["Origin"] = "https://enlighten.enphaseenergy.com"
            headers["Referer"] = "https://enlighten.enphaseenergy.com/"
        else:
            _LOGGER.warning("No bearer token available for VPP events API")

        _LOGGER.debug("VPP Events API call: %s", full_url)
        _LOGGER.debug("VPP Events has Authorization: %s, has e-auth-token: %s",
                     "Authorization" in headers, "e-auth-token" in headers)
        result = await self._json("GET", full_url, headers=headers)
        _LOGGER.debug("VPP Events API response event count: %s",
                     len(result.get("data", [])) if isinstance(result, dict) else "unknown")
        return result

    async def savings_today(self, date: str) -> dict:
        """Fetch savings data for a specific date.

        GET https://enlighten.enphaseenergy.com/service/savings/systems/<site_id>/savings
        Query params: resolution=DAY, date=YYYY-MM-DD, do_compute=true, simulated=false
        Returns savings data including imported and exported values in USD.
        """
        url = f"{BASE_URL}/service/savings/systems/{self._site}/savings"
        params = {
            "resolution": "DAY",
            "date": date,
            "do_compute": "true",
            "simulated": "false",
        }
        from urllib.parse import urlencode
        query_string = urlencode(params)
        full_url = f"{url}?{query_string}"

        return await self._json("GET", full_url)

    async def import_tariff(self) -> dict:
        """Fetch import tariff data.

        GET https://enlighten.enphaseenergy.com/service/tariff/tariff-ms/systems/<site_id>/tariff?include-site-details=true
        Returns tariff structure with seasons, periods, and rates for import costs.
        """
        url = f"{BASE_URL}/service/tariff/tariff-ms/systems/{self._site}/tariff"
        params = {"include-site-details": "true"}
        from urllib.parse import urlencode
        query_string = urlencode(params)
        full_url = f"{url}?{query_string}"

        return await self._json("GET", full_url)

    async def export_tariff(self, date: str) -> dict:
        """Fetch export tariff (buyback) data for a specific date.

        GET https://enlighten.enphaseenergy.com/service/tariff/tariff-ms/systems/<site_id>/tariffs?rateType=BUYBACK&date=YYYY-MM-DD&includeUtility=
        Returns export credit rates by hour.
        """
        url = f"{BASE_URL}/service/tariff/tariff-ms/systems/{self._site}/tariffs"
        params = {
            "rateType": "BUYBACK",
            "date": date,
            "includeUtility": "",
        }
        from urllib.parse import urlencode
        query_string = urlencode(params)
        full_url = f"{url}?{query_string}"

        return await self._json("GET", full_url)

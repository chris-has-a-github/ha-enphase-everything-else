
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, OPT_ENABLE_VPP_DEVICE
from .coordinator import EnphaseCoordinator
from .entity import EnphaseBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    import logging
    _LOGGER = logging.getLogger(__name__)

    coord: EnphaseCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = []
    # Site-level cloud reachability
    entities.append(SiteCloudReachableBinarySensor(coord))
    # VPP event today binary sensor if program_id is configured - now in VPP device
    enable_vpp = entry.options.get(OPT_ENABLE_VPP_DEVICE, True)
    if coord.vpp_program_id and enable_vpp:
        _LOGGER.debug("Creating VPP Event Today binary sensor for site %s with program_id %s",
                     coord.site_id, coord.vpp_program_id)
        entities.append(VPPEventTodayBinarySensor(coord, entry))
    else:
        _LOGGER.debug("Skipping VPP Event Today binary sensor - no vpp_program_id configured or VPP device disabled")
    serials = list(coord.serials or coord.data.keys())
    for sn in serials:
        entities.append(PluggedInBinarySensor(coord, sn))
        entities.append(ChargingBinarySensor(coord, sn))
        entities.append(FaultedBinarySensor(coord, sn))
        entities.append(ConnectedBinarySensor(coord, sn))
        entities.append(CommissionedBinarySensor(coord, sn))
    async_add_entities(entities)

class _EVBoolSensor(EnphaseBaseEntity, BinarySensorEntity):
    _attr_has_entity_name = True
    _translation_key: str | None = None

    def __init__(self, coord: EnphaseCoordinator, sn: str, key: str, tkey: str):
        super().__init__(coord, sn)
        self._key = key
        self._attr_unique_id = f"{DOMAIN}_{sn}_{key}"
        self._attr_translation_key = tkey

    @property
    def is_on(self) -> bool:
        d = (self._coord.data or {}).get(self._sn) or {}
        v = d.get(self._key)
        return bool(v)

    # available and device_info inherited from base


class PluggedInBinarySensor(_EVBoolSensor):
    def __init__(self, coord: EnphaseCoordinator, sn: str):
        super().__init__(coord, sn, "plugged", "plugged_in")


class ChargingBinarySensor(_EVBoolSensor):
    def __init__(self, coord: EnphaseCoordinator, sn: str):
        super().__init__(coord, sn, "charging", "charging")
    @property
    def icon(self) -> str | None:
        # Lightning bolt when charging, dimmed/off otherwise
        return "mdi:flash" if self.is_on else "mdi:flash-off"


class FaultedBinarySensor(_EVBoolSensor):
    def __init__(self, coord: EnphaseCoordinator, sn: str):
        super().__init__(coord, sn, "faulted", "faulted")
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        from homeassistant.helpers.entity import EntityCategory
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class ConnectedBinarySensor(_EVBoolSensor):
    def __init__(self, coord: EnphaseCoordinator, sn: str):
        super().__init__(coord, sn, "connected", "connected")
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class CommissionedBinarySensor(_EVBoolSensor):
    def __init__(self, coord: EnphaseCoordinator, sn: str):
        super().__init__(coord, sn, "commissioned", "commissioned")
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class SiteCloudReachableBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "cloud_reachable"

    def __init__(self, coord: EnphaseCoordinator):
        super().__init__(coord)
        self._coord = coord
        self._attr_unique_id = f"{DOMAIN}_site_{coord.site_id}_cloud_reachable"

    @property
    def name(self):
        return "Cloud Reachable"

    @property
    def is_on(self) -> bool:
        last = self._coord.last_success_utc
        if not last:
            return False
        now = dt_util.utcnow()
        interval = self._coord.update_interval.total_seconds() if self._coord.update_interval else 30
        threshold = interval * 2
        return (now - last).total_seconds() <= threshold

    @property
    def device_info(self):
        from homeassistant.helpers.entity import DeviceInfo
        return DeviceInfo(
            identifiers={(DOMAIN, f"site:{self._coord.site_id}")},
            manufacturer="Enphase",
            model="Enlighten Cloud",
            name=f"Enphase Site {self._coord.site_id}",
        )


class VPPEventTodayBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor that indicates if there's a VPP event today."""

    _attr_has_entity_name = True
    _attr_translation_key = "vpp_event_today"
    _attr_name = "VPP Event Today"

    def __init__(self, coord: EnphaseCoordinator, entry: ConfigEntry):
        """Initialize the binary sensor."""
        super().__init__(coord)
        self._coord = coord
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_vpp_{coord.site_id}_{coord.vpp_program_id}_event_today"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._coord.last_update_success

    @property
    def is_on(self) -> bool:
        """Return True if there's a VPP event today."""
        today_events = self._get_today_events()
        return len(today_events) > 0

    @property
    def extra_state_attributes(self):
        """Return today's VPP events as attributes."""
        today_events = self._get_today_events()

        if not today_events:
            return {"event_count": 0, "events": []}

        # Build attributes with today's events
        attrs = {
            "event_count": len(today_events),
            "events": [],
        }

        for event_data in today_events:
            event_info = {
                "id": event_data.get("id"),
                "name": event_data.get("name"),
                "type": event_data.get("type"),
                "status": event_data.get("status"),
                "start_time": event_data.get("start_time"),
                "end_time": event_data.get("end_time"),
                "target_soc": event_data.get("target_soc"),
                "avg_kw_discharged": event_data.get("avg_kw_discharged"),
                "avg_kw_charged": event_data.get("avg_kw_charged"),
            }
            attrs["events"].append(event_info)

        return attrs

    def _get_today_events(self) -> list[dict]:
        """Get all VPP events that occur today."""
        if not self._coord.vpp_events_data:
            return []

        today = dt_util.now().date()
        today_events = []

        response = self._coord.vpp_events_data
        if isinstance(response, dict):
            events = response.get("data", [])
            for event_data in events:
                try:
                    # Parse start and end times
                    start_str = event_data.get("start_time")
                    end_str = event_data.get("end_time")

                    if not start_str or not end_str:
                        continue

                    # Parse ISO format timestamps
                    from datetime import datetime, timezone

                    start_dt = datetime.fromisoformat(start_str.replace("+00:00", ""))
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=timezone.utc)

                    end_dt = datetime.fromisoformat(end_str.replace("+00:00", ""))
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=timezone.utc)

                    # Convert to local timezone for date comparison
                    start_local = dt_util.as_local(start_dt)
                    end_local = dt_util.as_local(end_dt)

                    # Check if event overlaps with today
                    if start_local.date() <= today <= end_local.date():
                        today_events.append(event_data)

                except Exception:
                    # Skip events that can't be parsed
                    continue

        return today_events

    @property
    def device_info(self):
        """Return device info for this binary sensor."""
        from homeassistant.helpers.entity import DeviceInfo

        return DeviceInfo(
            identifiers={(DOMAIN, f"vpp:{self._coord.site_id}:{self._coord.vpp_program_id}")},
            manufacturer="Enphase",
            model="Virtual Power Plant",
            name=f"Enphase VPP {self._coord.site_id} {self._coord.vpp_program_id}",
            translation_key="enphase_vpp",
            translation_placeholders={"site_id": str(self._coord.site_id), "program_id": str(self._coord.vpp_program_id)},
        )

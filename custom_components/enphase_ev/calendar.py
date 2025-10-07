from __future__ import annotations

from datetime import datetime, timedelta, timezone

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN, OPT_ENABLE_MONETARY_DEVICE, OPT_ENABLE_VPP_DEVICE
from .coordinator import EnphaseCoordinator
from .entity import EnphaseBaseEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up Enphase VPP calendar from a config entry."""
    import logging
    _LOGGER = logging.getLogger(__name__)

    coord: EnphaseCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = []
    # VPP calendar if program_id is configured - now in VPP device
    enable_vpp = entry.options.get(OPT_ENABLE_VPP_DEVICE, True)
    if coord.vpp_program_id and enable_vpp:
        _LOGGER.debug("Creating VPP Calendar for site %s with program_id %s, current events: %s",
                     coord.site_id, coord.vpp_program_id,
                     len(coord.vpp_events_data.get("data", [])) if coord.vpp_events_data else 0)
        entities.append(EnphaseVPPCalendar(coord, entry))
    else:
        _LOGGER.debug("Skipping VPP Calendar - no vpp_program_id configured or VPP device disabled")

    # Import Cost Calendar - now in Monetary device
    enable_monetary = entry.options.get(OPT_ENABLE_MONETARY_DEVICE, True)
    if enable_monetary:
        _LOGGER.debug("Creating Import Cost Calendar for site %s", coord.site_id)
        entities.append(EnphaseImportCostCalendar(coord, entry))
        _LOGGER.debug("Creating Export Price Calendar for site %s", coord.site_id)
        entities.append(EnphaseExportPriceCalendar(coord, entry))
    else:
        _LOGGER.debug("Skipping monetary calendars - monetary device disabled")

    async_add_entities(entities)


class EnphaseVPPCalendar(CalendarEntity):
    """Calendar entity for VPP events."""

    _attr_has_entity_name = True
    _attr_translation_key = "vpp_calendar"

    def __init__(self, coord: EnphaseCoordinator, entry: ConfigEntry):
        """Initialize the calendar."""
        self._coord = coord
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_vpp_{coord.site_id}_{coord.vpp_program_id}_calendar"
        self._attr_name = "VPP Events Calendar"

    @property
    def device_info(self):
        """Return device info for this calendar."""
        from homeassistant.helpers.entity import DeviceInfo

        return DeviceInfo(
            identifiers={(DOMAIN, f"vpp:{self._coord.site_id}:{self._coord.vpp_program_id}")},
            manufacturer="Enphase",
            model="Virtual Power Plant",
            name=f"Enphase VPP {self._coord.site_id} {self._coord.vpp_program_id}",
            translation_key="enphase_vpp",
            translation_placeholders={"site_id": str(self._coord.site_id), "program_id": str(self._coord.vpp_program_id)},
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming calendar event."""
        import logging
        _LOGGER = logging.getLogger(__name__)

        now = dt_util.now()
        upcoming_events = []

        if not self._coord.vpp_events_data:
            _LOGGER.debug("VPP Calendar event property: No vpp_events_data available")
            return None

        response = self._coord.vpp_events_data
        if isinstance(response, dict):
            events = response.get("data", [])
            _LOGGER.debug("VPP Calendar event property: Checking %s events for upcoming from %s", len(events), now)
            for event_data in events:
                event = self._parse_event(event_data)
                if event and event.end >= now:
                    upcoming_events.append(event)

        # Return the next upcoming event
        if upcoming_events:
            upcoming_events.sort(key=lambda e: e.start)
            _LOGGER.debug("VPP Calendar event property: Returning next event: %s", upcoming_events[0].summary)
            return upcoming_events[0]

        _LOGGER.debug("VPP Calendar event property: No upcoming events found")
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        import logging
        _LOGGER = logging.getLogger(__name__)

        events = []

        if not self._coord.vpp_events_data:
            _LOGGER.debug("VPP Calendar: No vpp_events_data available")
            return events

        response = self._coord.vpp_events_data
        if isinstance(response, dict):
            event_list = response.get("data", [])
            _LOGGER.debug("VPP Calendar: Processing %s events for range %s to %s",
                         len(event_list), start_date, end_date)
            for event_data in event_list:
                event = self._parse_event(event_data)
                if event:
                    # Include events that overlap with the requested range
                    if event.end >= start_date and event.start <= end_date:
                        events.append(event)
                        _LOGGER.debug("VPP Calendar: Added event %s (%s to %s)",
                                     event.summary, event.start, event.end)
                else:
                    _LOGGER.debug("VPP Calendar: Failed to parse event: %s", event_data.get("id"))

        _LOGGER.debug("VPP Calendar: Returning %s events", len(events))
        return sorted(events, key=lambda e: e.start)

    def _parse_event(self, event_data: dict) -> CalendarEvent | None:
        """Parse VPP event data into a CalendarEvent."""
        import logging
        _LOGGER = logging.getLogger(__name__)

        try:
            # Parse start and end times
            start_str = event_data.get("start_time")
            end_str = event_data.get("end_time")

            if not start_str or not end_str:
                _LOGGER.debug("VPP Calendar: Event %s missing start or end time", event_data.get("id"))
                return None

            # Parse ISO format timestamps - handle the +00:00 timezone format
            start_dt = datetime.fromisoformat(start_str.replace("+00:00", "+00:00"))
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)

            end_dt = datetime.fromisoformat(end_str.replace("+00:00", "+00:00"))
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)

            # Build event summary
            event_type = event_data.get("type", "unknown")
            status = event_data.get("status", "unknown")
            name = event_data.get("name", "VPP Event")

            # Create friendly summary
            type_map = {
                "battery_discharge": "Battery Discharge",
                "battery_charge": "Battery Charge",
                "idle": "Idle",
            }
            type_name = type_map.get(event_type, event_type)

            summary = f"{type_name} - {status}"

            # Build description with event details
            description_parts = [f"Event: {name}"]

            if event_data.get("target_soc") is not None:
                description_parts.append(f"Target SOC: {event_data['target_soc']}%")

            if event_data.get("rate_watt") is not None:
                rate_kw = event_data["rate_watt"] / 1000
                description_parts.append(f"Rate: {rate_kw:.1f} kW")

            if event_data.get("avg_kw_discharged") is not None:
                description_parts.append(
                    f"Avg Discharged: {event_data['avg_kw_discharged']:.2f} kW"
                )

            if event_data.get("avg_kw_charged") is not None:
                description_parts.append(
                    f"Avg Charged: {event_data['avg_kw_charged']:.2f} kW"
                )

            description_parts.append(f"Mode: {event_data.get('mode', 'N/A')}")
            description_parts.append(f"Type: {event_data.get('subtype', 'N/A')}")

            description = "\n".join(description_parts)

            return CalendarEvent(
                start=start_dt,
                end=end_dt,
                summary=summary,
                description=description,
                uid=event_data.get("id", ""),
            )

        except Exception as e:
            # Log error but don't fail entire calendar
            _LOGGER.error("VPP Calendar: Failed to parse event %s: %s", event_data.get("id"), e, exc_info=True)
            return None

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self._coord.async_add_listener(self.async_write_ha_state)
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._coord.last_update_success


class EnphaseImportCostCalendar(CalendarEntity):
    """Calendar entity for Import Cost periods."""

    _attr_has_entity_name = True
    _attr_translation_key = "import_cost_calendar"

    def __init__(self, coord: EnphaseCoordinator, entry: ConfigEntry):
        """Initialize the calendar."""
        self._coord = coord
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_monetary_{coord.site_id}_import_cost_calendar"
        self._attr_name = "Import Cost Calendar"

    @property
    def device_info(self):
        """Return device info for this calendar."""
        from homeassistant.helpers.entity import DeviceInfo

        return DeviceInfo(
            identifiers={(DOMAIN, f"monetary:{self._coord.site_id}")},
            manufacturer="Enphase",
            model="Monetary Tracking",
            name=f"Enphase Monetary {self._coord.site_id}",
            translation_key="enphase_monetary",
            translation_placeholders={"site_id": str(self._coord.site_id)},
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current or next upcoming calendar event."""
        now = dt_util.now()
        # Pass None for hass, will use fallback timezone
        upcoming_events = self._get_events(now, now + timedelta(days=7), None)

        if not upcoming_events:
            return None

        # Return the current event or next upcoming
        for event in upcoming_events:
            if event.end > now:
                return event

        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        return self._get_events(start_date, end_date, hass)

    def _get_events(self, start_date: datetime, end_date: datetime, hass: HomeAssistant = None) -> list[CalendarEvent]:
        """Generate import cost events for the date range."""
        if not self._coord.import_tariff_data:
            return []

        events = []
        tariff_data = self._coord.import_tariff_data
        purchase = tariff_data.get("purchase", {})
        seasons = purchase.get("seasons", [])

        # Generate events for each day in the range
        current_date = start_date.date()
        end = end_date.date()

        while current_date <= end:
            # Find the matching season for this date
            month = current_date.month
            day_of_week = current_date.weekday() + 1  # Monday=1

            for season in seasons:
                start_month = int(season.get("startMonth", 0))
                end_month = int(season.get("endMonth", 0))

                # Check if date is in this season
                in_season = False
                if start_month <= end_month:
                    in_season = start_month <= month <= end_month
                else:  # Wraps around year end
                    in_season = month >= start_month or month <= end_month

                if not in_season:
                    continue

                # Find matching day group
                for day_group in season.get("days", []):
                    if day_of_week not in day_group.get("days", []):
                        continue

                    # Create events for each period
                    periods = day_group.get("periods", [])
                    for period in periods:
                        event = self._create_period_event(current_date, period, season, hass)
                        if event:
                            events.append(event)

            current_date = current_date + timedelta(days=1)

        return sorted(events, key=lambda e: e.start)

    def _create_period_event(self, date, period: dict, season: dict, hass: HomeAssistant = None) -> CalendarEvent | None:
        """Create a calendar event for a tariff period."""
        try:
            start_time_str = period.get("startTime", "")
            end_time_str = period.get("endTime", "")
            rate = period.get("rate")
            period_type = period.get("type", "unknown")

            if rate is None:
                return None

            # Convert minutes from midnight to datetime
            # Note: The API returns minutes in local time, not UTC
            if not start_time_str and not end_time_str:
                # Off-peak all day
                start_dt = datetime.combine(date, datetime.min.time())
                end_dt = datetime.combine(date + timedelta(days=1), datetime.min.time())
            else:
                start_minutes = int(start_time_str) if start_time_str else 0
                end_minutes = int(end_time_str) if end_time_str else 1440

                start_dt = datetime.combine(date, datetime.min.time()) + timedelta(minutes=start_minutes)

                # Handle periods that cross midnight
                if end_minutes >= 1440:
                    end_dt = datetime.combine(date + timedelta(days=1), datetime.min.time())
                else:
                    end_dt = datetime.combine(date, datetime.min.time()) + timedelta(minutes=end_minutes)

            # Make timezone aware - times are already in local timezone from the API
            # Get the local timezone from Home Assistant
            if hass:
                local_tz = dt_util.get_time_zone(hass.config.time_zone)
                start_dt = start_dt.replace(tzinfo=local_tz)
                end_dt = end_dt.replace(tzinfo=local_tz)
            else:
                # Fallback: use the timezone from dt_util.now()
                now_with_tz = dt_util.now()
                start_dt = start_dt.replace(tzinfo=now_with_tz.tzinfo)
                end_dt = end_dt.replace(tzinfo=now_with_tz.tzinfo)

            # Create summary
            rate_value = float(rate)
            summary = f"${rate_value:.5f}/kWh - {period_type.replace('-', ' ').title()}"

            # Create description with rate components
            description_parts = [f"Rate: ${rate_value:.5f}/kWh"]
            description_parts.append(f"Season: {season.get('id', 'unknown')}")
            description_parts.append(f"Type: {period_type}")
            
            rate_components = period.get("rateComponents", [])
            if rate_components:
                description_parts.append("\nRate Components:")
                for component in rate_components:
                    for name, value in component.items():
                        description_parts.append(f"  {name}: ${value:.5f}")

            description = "\n".join(description_parts)

            return CalendarEvent(
                start=start_dt,
                end=end_dt,
                summary=summary,
                description=description,
            )

        except Exception:
            return None

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self._coord.async_add_listener(self.async_write_ha_state)
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._coord.last_update_success


class EnphaseExportPriceCalendar(CalendarEntity):
    """Calendar entity for Export Price periods."""

    _attr_has_entity_name = True
    _attr_translation_key = "export_price_calendar"

    def __init__(self, coord: EnphaseCoordinator, entry: ConfigEntry):
        """Initialize the calendar."""
        self._coord = coord
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_monetary_{coord.site_id}_export_price_calendar"
        self._attr_name = "Export Price Calendar"

    @property
    def device_info(self):
        """Return device info for this calendar."""
        from homeassistant.helpers.entity import DeviceInfo

        return DeviceInfo(
            identifiers={(DOMAIN, f"monetary:{self._coord.site_id}")},
            manufacturer="Enphase",
            model="Monetary Tracking",
            name=f"Enphase Monetary {self._coord.site_id}",
            translation_key="enphase_monetary",
            translation_placeholders={"site_id": str(self._coord.site_id)},
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current or next upcoming calendar event."""
        now = dt_util.now()
        upcoming_events = self._get_events_sync(now, now + timedelta(days=1))

        if not upcoming_events:
            return None

        # Return the current event or next upcoming
        for event in upcoming_events:
            if event.end > now:
                return event

        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        # Fetch export tariff data for each day in the range
        events = []
        current_date = start_date.date()
        end = end_date.date()

        while current_date <= end:
            date_str = current_date.strftime("%Y-%m-%d")
            try:
                tariff_data = await self._coord.client.export_tariff(date_str)
                day_events = self._create_events_for_day(current_date, tariff_data, hass)
                events.extend(day_events)
            except Exception:
                pass  # Skip days with errors

            current_date = current_date + timedelta(days=1)

        return sorted(events, key=lambda e: e.start)

    def _get_events_sync(self, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        """Get events synchronously for today using cached data."""
        if not self._coord.export_tariff_data:
            return []

        today = dt_util.now().date()
        if start_date.date() == today:
            return self._create_events_for_day(today, self._coord.export_tariff_data, None)

        return []

    def _create_events_for_day(self, date, tariff_data: dict, hass: HomeAssistant = None) -> list[CalendarEvent]:
        """Create calendar events for export prices for a specific day."""
        if not tariff_data:
            return []

        events = []
        data = tariff_data.get("data", {})
        buyback = data.get("buyback", [])

        for period in buyback:
            try:
                start_minutes = int(period.get("start", 0))
                end_minutes = int(period.get("end", 0))
                rate = period.get("rate")

                if rate is None:
                    continue

                # Create datetime from minutes since midnight
                start_dt = datetime.combine(date, datetime.min.time()) + timedelta(minutes=start_minutes)
                # End is inclusive, so add 1 minute to make it exclusive
                end_dt = datetime.combine(date, datetime.min.time()) + timedelta(minutes=end_minutes + 1)

                # Make timezone aware
                if hass:
                    local_tz = dt_util.get_time_zone(hass.config.time_zone)
                    start_dt = start_dt.replace(tzinfo=local_tz)
                    end_dt = end_dt.replace(tzinfo=local_tz)
                else:
                    now_with_tz = dt_util.now()
                    start_dt = start_dt.replace(tzinfo=now_with_tz.tzinfo)
                    end_dt = end_dt.replace(tzinfo=now_with_tz.tzinfo)

                # Create summary
                rate_value = float(rate)
                summary = f"${rate_value:.5f}/kWh Export"

                # Create description with time range
                start_hour = start_minutes // 60
                start_min = start_minutes % 60
                end_hour = end_minutes // 60
                end_min = end_minutes % 60
                description = f"Export Rate: ${rate_value:.5f}/kWh\nTime: {start_hour:02d}:{start_min:02d} - {end_hour:02d}:{end_min:02d}"

                events.append(CalendarEvent(
                    start=start_dt,
                    end=end_dt,
                    summary=summary,
                    description=description,
                ))

            except Exception:
                continue

        return events

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self._coord.async_add_listener(self.async_write_ha_state)
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._coord.last_update_success

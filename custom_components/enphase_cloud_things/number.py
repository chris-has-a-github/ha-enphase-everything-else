from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import EnphaseCoordinator
from .entity import EnphaseBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coord: EnphaseCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list[NumberEntity] = []
    serials = list(coord.serials or coord.data.keys())
    for sn in serials:
        entities.append(ChargingAmpsNumber(coord, sn))
    async_add_entities(entities)


class ChargingAmpsNumber(EnphaseBaseEntity, NumberEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "charging_amps"
    _attr_native_unit_of_measurement = "A"

    def __init__(self, coord: EnphaseCoordinator, sn: str):
        super().__init__(coord, sn)
        self._attr_unique_id = f"{DOMAIN}_{sn}_amps_number"

    @property
    def native_value(self) -> float | None:
        d = (self._coord.data or {}).get(self._sn) or {}
        lvl = d.get("charging_level")
        if lvl is None:
            # If unknown from API and no prior setpoint, prefer 32A default
            return float(int(self._coord.last_set_amps.get(self._sn) or 32))
        try:
            return float(int(lvl))
        except Exception:
            return float(int(self._coord.last_set_amps.get(self._sn) or 32))

    @property
    def native_min_value(self) -> float:
        d = (self._coord.data or {}).get(self._sn) or {}
        v = d.get("min_amp")
        try:
            return float(int(v)) if v is not None else 6.0
        except Exception:
            return 6.0

    @property
    def native_max_value(self) -> float:
        d = (self._coord.data or {}).get(self._sn) or {}
        v = d.get("max_amp")
        try:
            return float(int(v)) if v is not None else 40.0
        except Exception:
            return 40.0

    @property
    def native_step(self) -> float:
        return 1.0

    async def async_set_native_value(self, value: float) -> None:
        amps = int(value)
        # Store desired setpoint locally; do not start charging here.
        # Start actions (switch/button/service) will use this setpoint.
        self._coord.set_last_set_amps(self._sn, amps)
        await self._coord.async_request_refresh()

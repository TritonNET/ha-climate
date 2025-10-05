from __future__ import annotations

import logging
from typing import Any, Optional, Union

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import (
    HVACMode,
    FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH,
    PRESET_ECO, PRESET_AWAY, PRESET_COMFORT,
    ATTR_TARGET_TEMP_LOW, ATTR_TARGET_TEMP_HIGH,
    ATTR_HVAC_MODE,
)
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_ROOMS, CONF_NAME, CONF_COVER, DATA, ENTITY_PREFIX

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Create room climate entities from the ConfigEntry."""
    stored = hass.data[DOMAIN][entry.entry_id][DATA]
    controller = stored["controller"]
    cfg = stored["config"]

    room_items = list(cfg[CONF_ROOMS].items())
    entities = []

    for room_key, room in room_items:
        name = room[CONF_NAME]
        cover = room[CONF_COVER]
        entities.append(
            TritonNetRoomClimate(
                hass=hass,
                entry=entry,
                controller=controller,
                room_key=room_key,
                friendly_name=name,
                cover_entity_id=cover,
            )
        )

    async_add_entities(entities, update_before_add=False)


class TritonNetRoomClimate(ClimateEntity):
    """One virtual climate per configured room."""

    _attr_should_poll = False
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
    )
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.HEAT_COOL,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
    ]
    _attr_fan_modes = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
    _attr_preset_modes = [PRESET_ECO, PRESET_AWAY, PRESET_COMFORT]
    _attr_swing_modes = ["off", "on"]

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        controller,
        room_key: str,
        friendly_name: str,
        cover_entity_id: str,
    ):
        self.hass = hass
        self._entry = entry
        self._controller = controller
        self._room_key = room_key
        self._attr_name = friendly_name
        self._cover_entity_id = cover_entity_id

        # Respect system unit (°C/°F)
        self._attr_temperature_unit = hass.config.units.temperature_unit

        # Defaults
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_fan_mode = FAN_AUTO
        self._attr_preset_mode = PRESET_COMFORT
        self._attr_swing_mode = "off"
        self._attr_target_temperature = 21.0
        self._attr_target_temperature_low: Optional[float] = None
        self._attr_target_temperature_high: Optional[float] = None
        self._attr_min_temp = 7.0
        self._attr_max_temp = 30.0

        # Unique per entity & linked to this ConfigEntry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{room_key}"

        # Force deterministic entity_id on first create
        # (If an entity with this unique_id already exists, registry keeps the stored id.
        # We also migrate in __init__.py to this id if needed.)
        self.entity_id = f"climate.{ENTITY_PREFIX}{room_key}"

    @property
    def device_info(self) -> DeviceInfo:
        # All room entities share one device per ConfigEntry
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="TritonNET Climate",
            manufacturer="TritonNET",
            model="Controller",
        )

    @property
    def target_temperature(self) -> Optional[float]:
        if self._attr_hvac_mode == HVACMode.HEAT_COOL:
            return None
        return self._attr_target_temperature

    @property
    def target_temperature_high(self) -> Optional[float]:
        if self._attr_hvac_mode != HVACMode.HEAT_COOL:
            return None
        return self._attr_target_temperature_high

    @property
    def target_temperature_low(self) -> Optional[float]:
        if self._attr_hvac_mode != HVACMode.HEAT_COOL:
            return None
        return self._attr_target_temperature_low

    async def _push(self):
        """Tell the controller about current desired state."""
        await self._controller.set_climate(
            self._room_key,
            hvac_mode=self._attr_hvac_mode,
            target_temp=self._attr_target_temperature,
            target_temp_low=self._attr_target_temperature_low,
            target_temp_high=self._attr_target_temperature_high,
            fan_mode=self._attr_fan_mode,
            preset_mode=self._attr_preset_mode,
            swing_mode=self._attr_swing_mode,
            humidity=None,
        )

    async def async_set_hvac_mode(self, hvac_mode: Union[str, HVACMode]) -> None:
        self._attr_hvac_mode = HVACMode(hvac_mode) if hvac_mode else HVACMode.OFF
        self.async_write_ha_state()
        await self._push()

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(HVACMode.HEAT_COOL)

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        updated = False

        if kwargs.get(ATTR_HVAC_MODE) is not None:
            await self.async_set_hvac_mode(kwargs[ATTR_HVAC_MODE])

        if self._attr_hvac_mode == HVACMode.HEAT_COOL:
            hi = kwargs.get(ATTR_TARGET_TEMP_HIGH)
            lo = kwargs.get(ATTR_TARGET_TEMP_LOW)
            if hi is not None:
                self._attr_target_temperature_high = float(hi)
                updated = True
            if lo is not None:
                self._attr_target_temperature_low = float(lo)
                updated = True
        else:
            temp = kwargs.get(ATTR_TEMPERATURE)
            if temp is not None:
                self._attr_target_temperature = float(temp)
                updated = True

        if updated:
            self.async_write_ha_state()
            await self._push()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        if fan_mode in self._attr_fan_modes:
            self._attr_fan_mode = fan_mode
            self.async_write_ha_state()
            await self._push()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode in self._attr_preset_modes:
            self._attr_preset_mode = preset_mode
            self.async_write_ha_state()
            await self._push()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        if swing_mode in self._attr_swing_modes:
            self._attr_swing_mode = swing_mode
            self.async_write_ha_state()
            await self._push()

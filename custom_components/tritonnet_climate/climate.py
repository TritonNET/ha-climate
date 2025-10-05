import logging
from typing import Any, Optional

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
)
from homeassistant.components.climate.const import (
    HVACMode,                               # import HVACMode from .const for consistency
    FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH,
    PRESET_ECO, PRESET_AWAY, PRESET_COMFORT,
    ATTR_TARGET_TEMP_LOW, ATTR_TARGET_TEMP_HIGH,
    ATTR_HVAC_MODE,
)
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    DOMAIN, DATA_CONFIG, DATA_CONTROLLER, CONF_ROOMS, CONF_NAME, CONF_COVER
)

_LOGGER = logging.getLogger(__name__)

ASYNC_SETUP_PLATFORM_CALLED = False

async def async_setup_entry(hass, entry, async_add_entities):
    # Not used; we are YAML only.
    return

async def async_setup_platform_via_forward_entry(hass: HomeAssistant, async_add_entities):
    # Not used; present for clarity.
    return

async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    # HA will call this because __init__ forwarded the platform load.
    triton_cfg = hass.data[DOMAIN][DATA_CONFIG]
    controller = hass.data[DOMAIN][DATA_CONTROLLER]
    room_items = list(triton_cfg[CONF_ROOMS].items())

    entities = []
    for room_key, room in room_items:
        name = room[CONF_NAME]
        cover = room[CONF_COVER]
        entities.append(
            TritonNetRoomClimate(
                hass=hass,
                controller=controller,
                room_key=room_key,
                friendly_name=name,
                cover_entity_id=cover,
            )
        )

    async_add_entities(entities, update_before_add=False)

class TritonNetRoomClimate(ClimateEntity):
    _attr_should_poll = False
    _attr_temperature_unit = TEMP_CELSIUS
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

    def __init__(self, hass: HomeAssistant, controller, room_key: str, friendly_name: str, cover_entity_id: str):
        self.hass = hass
        self._controller = controller
        self._room_key = room_key
        self._attr_name = friendly_name
        self.entity_id = f"climate.tritonnet_{room_key}"
        self._cover_entity_id = cover_entity_id

        self._attr_temperature_unit = hass.config.units.temperature_unit

        # Defaults
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_fan_mode = FAN_AUTO
        self._attr_preset_mode = PRESET_COMFORT
        self._attr_swing_mode = "off"
        self._attr_target_temperature = 21.0
        self._attr_target_temperature_low = None
        self._attr_target_temperature_high = None
        self._attr_min_temp = 7.0
        self._attr_max_temp = 30.0
        self._attr_unique_id = f"tritonnet_climate_{room_key}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, "tritonnet_climate")},
            name="TritonNET Climate",
            manufacturer="TritonNET",
            model="Room Virtual Climate",
        )

    @property
    def available(self) -> bool:
        # You can make this dependent on main AC/cover availability, if desired.
        return True

    @property
    def target_temperature(self) -> Optional[float]:
        return None if self._attr_hvac_mode == HVACMode.HEAT_COOL else self._attr_target_temperature

    @property
    def target_temperature_high(self) -> Optional[float]:
        return self._attr_target_temperature_high if self._attr_hvac_mode == HVACMode.HEAT_COOL else None

    @property
    def target_temperature_low(self) -> Optional[float]:
        return self._attr_target_temperature_low if self._attr_hvac_mode == HVACMode.HEAT_COOL else None

    async def _push(self):
        # Central place to notify your controller about current desired state
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

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
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

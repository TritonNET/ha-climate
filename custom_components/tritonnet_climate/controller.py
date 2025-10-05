import logging

_LOGGER = logging.getLogger(__name__)

class TritonNetController:
    """Stub controller. Replace set_climate() with your actual logic."""

    def __init__(self, hass, main_ac_entity_id: str):
        self.hass = hass
        self.main_ac = main_ac_entity_id

    async def set_climate(
        self,
        room_key,
        *,
        hvac_mode=None,            # HVACMode or str
        target_temp=None,          # float
        target_temp_low=None,      # float
        target_temp_high=None,     # float
        fan_mode=None,             # str
        preset_mode=None,          # str
        swing_mode=None,           # str
        humidity=None              # float/int
    ):
        _LOGGER.info(
            "set_climate(room=%s hvac=%s t=%s t_lo=%s t_hi=%s fan=%s preset=%s swing=%s humidity=%s)",
            room_key, hvac_mode, target_temp, target_temp_low, target_temp_high,
            fan_mode, preset_mode, swing_mode, humidity
        )
        # TODO: implement real control here
        return True

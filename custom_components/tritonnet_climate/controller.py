import logging

_LOGGER = logging.getLogger(__name__)

class TritonNetController:
    """
    Thin controller you can expand.
    Replace the set_climate() body with your real integration to AC/IR/covers/etc.
    """

    def __init__(self, hass, main_ac_entity_id):
        self.hass = hass
        self.main_ac = main_ac_entity_id

    async def set_climate(
        self,
        room_key,
        *,
        hvac_mode=None,            # "heat", "cool", "heat_cool", "off", etc.
        target_temp=None,          # float
        target_temp_low=None,      # float (for heat_cool)
        target_temp_high=None,     # float (for heat_cool)
        fan_mode=None,             # "auto", "low", "medium", "high" etc.
        preset_mode=None,          # "eco", "away", etc.
        swing_mode=None,           # "on"/"off" or vendor specific
        humidity=None              # float/int target
    ):
        """
        TODO: Replace this with your logic.
        For now we only log the request so you can verify calls.
        """
        _LOGGER.info(
            "set_climate room=%s hvac_mode=%s target_temp=%s "
            "range=[%s,%s] fan=%s preset=%s swing=%s humidity=%s",
            room_key, hvac_mode, target_temp,
            target_temp_low, target_temp_high, fan_mode, preset_mode, swing_mode, humidity
        )
        # Example: call your IR blaster, open/close covers, or route commands to main AC.
        # await self.hass.services.async_call("climate", "set_temperature", {...})
        return True

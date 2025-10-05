import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.discovery import async_load_platform

from .const import (
    DOMAIN,
    CONF_MAIN_AC,
    CONF_ROOMS,
    CONF_NAME,
    CONF_COVER,
    DATA_CONFIG,
    DATA_CONTROLLER,
)
from .controller import TritonNetController

_LOGGER = logging.getLogger(__name__)

ROOM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_COVER): cv.entity_id,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_MAIN_AC): cv.entity_id,
                vol.Required(CONF_ROOMS): {cv.slug: ROOM_SCHEMA},
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    if DOMAIN not in config:
        return True

    cfg = config[DOMAIN]
    main_ac = cfg[CONF_MAIN_AC]
    rooms = cfg[CONF_ROOMS]

    controller = TritonNetController(hass, main_ac)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][DATA_CONFIG] = cfg
    hass.data[DOMAIN][DATA_CONTROLLER] = controller

    _LOGGER.info("TritonNET Climate: main_ac=%s rooms=%s", main_ac, list(rooms.keys()))

    hass.async_create_task(
        async_load_platform(hass, "climate", DOMAIN, {}, config)
    )
    return True

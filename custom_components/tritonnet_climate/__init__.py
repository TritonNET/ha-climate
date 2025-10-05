import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    CONF_MAIN_AC,
    CONF_ROOMS,
    CONF_NAME,
    CONF_COVER,
    DATA_CONFIG,
    DATA_CONTROLLER,
    DATA_DEVICE_IDENTIFIERS,
    DEVICE_UNIQUE_ID,
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
    """YAML setup for TritonNET Climate."""
    if DOMAIN not in config:
        return True

    cfg = config[DOMAIN]
    main_ac = cfg[CONF_MAIN_AC]
    rooms = cfg[CONF_ROOMS]

    controller = TritonNetController(hass, main_ac)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][DATA_CONFIG] = cfg
    hass.data[DOMAIN][DATA_CONTROLLER] = controller

    # Create (or get) a single device in the device registry WITHOUT config_entry_id
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_or_create(
        identifiers={(DOMAIN, DEVICE_UNIQUE_ID)},
        manufacturer="TritonNET",
        name="TritonNET Climate",
        model="Controller",
    )

    # Store the identifiers for child entities to reuse
    hass.data[DOMAIN][DATA_DEVICE_IDENTIFIERS] = {(DOMAIN, DEVICE_UNIQUE_ID)}

    _LOGGER.info(
        "TritonNET Climate: main_ac=%s rooms=%s (device_id=%s)",
        main_ac, list(rooms.keys()), device.id
    )

    # Load the climate platform using legacy YAML discovery
    hass.async_create_task(
        async_load_platform(hass, "climate", DOMAIN, {}, config)
    )
    return True

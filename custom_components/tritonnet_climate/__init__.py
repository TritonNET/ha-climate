from __future__ import annotations

import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, CONF_MAIN_AC, CONF_ROOMS, CONF_NAME, CONF_COVER, DATA
from .controller import TritonNetController

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE]

ROOM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required("cover"): cv.entity_id,   # keep string literal for clarity
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
    """Kick off import flow if YAML is present."""
    if DOMAIN in config:
        await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config[DOMAIN],
        )
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from ConfigEntry (created via YAML import)."""
    data = entry.data
    main_ac = data[CONF_MAIN_AC]
    rooms = data[CONF_ROOMS]

    controller = TritonNetController(hass, main_ac)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        DATA: {
            "controller": controller,
            "config": data,
        }
    }

    _LOGGER.info(
        "TritonNET Climate set up: main_ac=%s rooms=%s",
        main_ac, list(rooms.keys())
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the ConfigEntry."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok

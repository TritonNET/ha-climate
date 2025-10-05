from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_NAME
from .const import DOMAIN

class TritonNetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_import(self, import_config) -> FlowResult:
        """Create/update a single entry from YAML."""
        # Single instance only (one device grouping all room entities)
        existing = self._async_current_entries()
        if existing:
            entry = existing[0]
            # Update the existing entry with new YAML
            self.hass.config_entries.async_update_entry(
                entry, data=import_config, title="TritonNET Climate"
            )
            await self.hass.config_entries.async_reload(entry.entry_id)
            return self.async_abort(reason="already_configured")

        return self.async_create_entry(title="TritonNET Climate", data=import_config)

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN

class TritonNetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_import(self, import_config) -> FlowResult:
        """Create/update a single entry from YAML."""
        existing = self._async_current_entries()
        if existing:
            entry = existing[0]
            self.hass.config_entries.async_update_entry(
                entry, data=import_config, title="TritonNET Climate"
            )
            # No need to reload here; HA reloads on next start or when you change YAML.
            return self.async_abort(reason="already_configured")

        return self.async_create_entry(title="TritonNET Climate", data=import_config)

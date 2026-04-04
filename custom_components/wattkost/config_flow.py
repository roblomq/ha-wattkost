"""Config flow for NL Energy Cost integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_CONSUMPTION_W,
    CONF_CONSUMPTION_KWH,
    CONF_IMPORT_T1_KWH,
    CONF_IMPORT_T2_KWH,
    CONF_IMPORT_TOTAL_KWH,
    CONF_IMPORT_W,
    CONF_EXPORT_T1_KWH,
    CONF_EXPORT_T2_KWH,
    CONF_EXPORT_TOTAL_KWH,
    CONF_EXPORT_W,
    CONF_SOLAR_KWH,
    CONF_SOLAR_W,
    CONF_GAS_DAILY_M3,
    CONF_USE_SINGLE_TARIFF,
    CONF_TARIFF_ENKEL,
    CONF_TARIFF_NORMAAL,
    CONF_TARIFF_DAL,
    CONF_TARIFF_RETURN,
    CONF_TARIFF_RETURN_COST,
    CONF_FIXED_DELIVERY_DAY_ELECTRICITY,
    CONF_SYSTEM_OPERATOR_DAY_ELECTRICITY,
    CONF_ENERGY_REDUCTION_YEAR,
    CONF_GAS_TARIFF,
    CONF_FIXED_DELIVERY_DAY_GAS,
    CONF_SYSTEM_OPERATOR_DAY_GAS,
    DEFAULT_TARIFF_ENKEL,
    DEFAULT_TARIFF_NORMAAL,
    DEFAULT_TARIFF_DAL,
    DEFAULT_TARIFF_RETURN,
    DEFAULT_TARIFF_RETURN_COST,
    DEFAULT_USE_SINGLE_TARIFF,
    DEFAULT_FIXED_DELIVERY_DAY_ELECTRICITY,
    DEFAULT_SYSTEM_OPERATOR_DAY_ELECTRICITY,
    DEFAULT_ENERGY_REDUCTION_DAY,
    DEFAULT_GAS_TARIFF,
    DEFAULT_FIXED_DELIVERY_DAY_GAS,
    DEFAULT_SYSTEM_OPERATOR_DAY_GAS,
)

_LOGGER = logging.getLogger(__name__)

SENSOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor")
)


def _clean(user_input: dict[str, Any]) -> dict[str, Any]:
    """Remove None and empty-string entity values from user input."""
    return {k: v for k, v in user_input.items() if v not in (None, "")}


class NLEnergyCostConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NL Energy Cost."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Step 1: Import sensors."""
        if user_input is not None:
            self._data.update(_clean(user_input))
            return await self.async_step_export_sensors()

        schema = vol.Schema(
            {
                vol.Optional(CONF_IMPORT_T1_KWH): SENSOR_SELECTOR,
                vol.Optional(CONF_IMPORT_T2_KWH): SENSOR_SELECTOR,
                vol.Optional(CONF_IMPORT_TOTAL_KWH): SENSOR_SELECTOR,
                vol.Optional(CONF_IMPORT_W): SENSOR_SELECTOR,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            last_step=False,
        )

    async def async_step_export_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Step 2: Export / teruglevering sensors."""
        if user_input is not None:
            self._data.update(_clean(user_input))
            return await self.async_step_other_sensors()

        schema = vol.Schema(
            {
                vol.Optional(CONF_EXPORT_T1_KWH): SENSOR_SELECTOR,
                vol.Optional(CONF_EXPORT_T2_KWH): SENSOR_SELECTOR,
                vol.Optional(CONF_EXPORT_TOTAL_KWH): SENSOR_SELECTOR,
                vol.Optional(CONF_EXPORT_W): SENSOR_SELECTOR,
            }
        )

        return self.async_show_form(
            step_id="export_sensors",
            data_schema=schema,
            last_step=False,
        )

    async def async_step_other_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Step 3: Solar, consumption and gas sensors."""
        if user_input is not None:
            self._data.update(_clean(user_input))
            return await self.async_step_electricity_tariffs()

        schema = vol.Schema(
            {
                vol.Optional(CONF_SOLAR_KWH): SENSOR_SELECTOR,
                vol.Optional(CONF_SOLAR_W): SENSOR_SELECTOR,
                vol.Optional(CONF_CONSUMPTION_W): SENSOR_SELECTOR,
                vol.Optional(CONF_CONSUMPTION_KWH): SENSOR_SELECTOR,
                vol.Optional(CONF_GAS_DAILY_M3): SENSOR_SELECTOR,
            }
        )

        return self.async_show_form(
            step_id="other_sensors",
            data_schema=schema,
            last_step=False,
        )

    async def async_step_electricity_tariffs(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Step 4: Electricity tariffs."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_fixed_costs()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_USE_SINGLE_TARIFF, default=DEFAULT_USE_SINGLE_TARIFF
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_TARIFF_ENKEL, default=DEFAULT_TARIFF_ENKEL
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=2, step="any", mode="box", unit_of_measurement="€/kWh"
                    )
                ),
                vol.Required(
                    CONF_TARIFF_NORMAAL, default=DEFAULT_TARIFF_NORMAAL
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=2, step="any", mode="box", unit_of_measurement="€/kWh"
                    )
                ),
                vol.Required(
                    CONF_TARIFF_DAL, default=DEFAULT_TARIFF_DAL
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=2, step="any", mode="box", unit_of_measurement="€/kWh"
                    )
                ),
                vol.Required(
                    CONF_TARIFF_RETURN, default=DEFAULT_TARIFF_RETURN
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=2, step="any", mode="box", unit_of_measurement="€/kWh excl. BTW"
                    )
                ),
                vol.Required(
                    CONF_TARIFF_RETURN_COST, default=DEFAULT_TARIFF_RETURN_COST
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=2, step="any", mode="box", unit_of_measurement="€/kWh"
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="electricity_tariffs",
            data_schema=schema,
            last_step=False,
        )

    async def async_step_fixed_costs(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Step 5: Fixed daily costs and gas tariff."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(
                title="WattKost",
                data=self._data,
            )

        schema = vol.Schema(
            {
                # Electricity fixed costs
                vol.Required(
                    CONF_FIXED_DELIVERY_DAY_ELECTRICITY,
                    default=round(DEFAULT_FIXED_DELIVERY_DAY_ELECTRICITY, 5),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=5, step="any", mode="box", unit_of_measurement="€/dag"
                    )
                ),
                vol.Required(
                    CONF_SYSTEM_OPERATOR_DAY_ELECTRICITY,
                    default=round(DEFAULT_SYSTEM_OPERATOR_DAY_ELECTRICITY, 5),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=5, step="any", mode="box", unit_of_measurement="€/dag"
                    )
                ),
                vol.Required(
                    CONF_ENERGY_REDUCTION_YEAR,
                    default=round(DEFAULT_ENERGY_REDUCTION_DAY, 5),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=-5, max=0, step="any", mode="box", unit_of_measurement="€/dag"
                    )
                ),
                # Gas tariffs & fixed costs
                vol.Required(
                    CONF_GAS_TARIFF, default=DEFAULT_GAS_TARIFF
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=5, step="any", mode="box", unit_of_measurement="€/m³"
                    )
                ),
                vol.Required(
                    CONF_FIXED_DELIVERY_DAY_GAS,
                    default=round(DEFAULT_FIXED_DELIVERY_DAY_GAS, 5),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=5, step="any", mode="box", unit_of_measurement="€/dag"
                    )
                ),
                vol.Required(
                    CONF_SYSTEM_OPERATOR_DAY_GAS,
                    default=round(DEFAULT_SYSTEM_OPERATOR_DAY_GAS, 5),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=5, step="any", mode="box", unit_of_measurement="€/dag"
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="fixed_costs",
            data_schema=schema,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> NLEnergyCostOptionsFlow:
        """Return options flow."""
        return NLEnergyCostOptionsFlow(config_entry)


class NLEnergyCostOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for NL Energy Cost (re-configure tariffs)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._data: dict[str, Any] = dict(config_entry.data)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage options: update tariffs."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_fixed_costs_options()

        data = self._data

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_USE_SINGLE_TARIFF,
                    default=data.get(CONF_USE_SINGLE_TARIFF, DEFAULT_USE_SINGLE_TARIFF),
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_TARIFF_ENKEL,
                    default=data.get(CONF_TARIFF_ENKEL, DEFAULT_TARIFF_ENKEL),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=2, step="any", mode="box", unit_of_measurement="€/kWh"
                    )
                ),
                vol.Required(
                    CONF_TARIFF_NORMAAL,
                    default=data.get(CONF_TARIFF_NORMAAL, DEFAULT_TARIFF_NORMAAL),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=2, step="any", mode="box", unit_of_measurement="€/kWh"
                    )
                ),
                vol.Required(
                    CONF_TARIFF_DAL,
                    default=data.get(CONF_TARIFF_DAL, DEFAULT_TARIFF_DAL),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=2, step="any", mode="box", unit_of_measurement="€/kWh"
                    )
                ),
                vol.Required(
                    CONF_TARIFF_RETURN,
                    default=data.get(CONF_TARIFF_RETURN, DEFAULT_TARIFF_RETURN),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=2, step="any", mode="box", unit_of_measurement="€/kWh excl. BTW"
                    )
                ),
                vol.Required(
                    CONF_TARIFF_RETURN_COST,
                    default=data.get(CONF_TARIFF_RETURN_COST, DEFAULT_TARIFF_RETURN_COST),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=2, step="any", mode="box", unit_of_measurement="€/kWh"
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            last_step=False,
        )

    async def async_step_fixed_costs_options(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Options step 2: fixed costs."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="", data=self._data)

        data = self._data

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_FIXED_DELIVERY_DAY_ELECTRICITY,
                    default=data.get(CONF_FIXED_DELIVERY_DAY_ELECTRICITY, DEFAULT_FIXED_DELIVERY_DAY_ELECTRICITY),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=5, step="any", mode="box", unit_of_measurement="€/dag"
                    )
                ),
                vol.Required(
                    CONF_SYSTEM_OPERATOR_DAY_ELECTRICITY,
                    default=data.get(CONF_SYSTEM_OPERATOR_DAY_ELECTRICITY, DEFAULT_SYSTEM_OPERATOR_DAY_ELECTRICITY),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=5, step="any", mode="box", unit_of_measurement="€/dag"
                    )
                ),
                vol.Required(
                    CONF_ENERGY_REDUCTION_YEAR,
                    default=data.get(CONF_ENERGY_REDUCTION_YEAR, DEFAULT_ENERGY_REDUCTION_DAY),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=-500, max=0, step="any", mode="box", unit_of_measurement="€/jaar"
                    )
                ),
                vol.Required(
                    CONF_GAS_TARIFF,
                    default=data.get(CONF_GAS_TARIFF, DEFAULT_GAS_TARIFF),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=5, step="any", mode="box", unit_of_measurement="€/m³"
                    )
                ),
                vol.Required(
                    CONF_FIXED_DELIVERY_DAY_GAS,
                    default=data.get(CONF_FIXED_DELIVERY_DAY_GAS, DEFAULT_FIXED_DELIVERY_DAY_GAS),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=5, step="any", mode="box", unit_of_measurement="€/dag"
                    )
                ),
                vol.Required(
                    CONF_SYSTEM_OPERATOR_DAY_GAS,
                    default=data.get(CONF_SYSTEM_OPERATOR_DAY_GAS, DEFAULT_SYSTEM_OPERATOR_DAY_GAS),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=5, step="any", mode="box", unit_of_measurement="€/dag"
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="fixed_costs_options", data_schema=schema
        )

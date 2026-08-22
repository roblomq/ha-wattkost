"""Sensor platform for WattKost integration."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.util import dt as dt_util

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
    CONF_USE_SALDERING,
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
    DEFAULT_USE_SALDERING,
    DEFAULT_TARIFF_NORMAAL,
    DEFAULT_TARIFF_DAL,
    DEFAULT_TARIFF_RETURN,
    DEFAULT_TARIFF_RETURN_COST,
    DEFAULT_FIXED_DELIVERY_DAY_ELECTRICITY,
    DEFAULT_SYSTEM_OPERATOR_DAY_ELECTRICITY,
    DEFAULT_ENERGY_REDUCTION_DAY,
    DEFAULT_GAS_TARIFF,
    DEFAULT_FIXED_DELIVERY_DAY_GAS,
    DEFAULT_SYSTEM_OPERATOR_DAY_GAS,
)

_LOGGER = logging.getLogger(__name__)

DAYS_PER_YEAR = 365.2425


def _safe_float(hass: HomeAssistant, entity_id: str | None) -> float | None:
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None or state.state in ("unknown", "unavailable", None):
        return None
    try:
        return float(state.state)
    except (ValueError, TypeError):
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    config = {**entry.data, **entry.options}
    coordinator = WattKostCoordinator(hass, config, entry.entry_id)

    sensors = [
        WattKostSensor(coordinator, entry.entry_id, "electricity_current_cost_eur_h",
            "Stroom actuele kosten", "euro_per_h", "mdi:lightning-bolt",
            None, SensorStateClass.MEASUREMENT,
            lambda c: c.electricity_current_cost_eur_h),
        WattKostSensor(coordinator, entry.entry_id, "electricity_import_rate",
            "Stroom actueel importtarief", "EUR/kWh", "mdi:cash-minus",
            None, SensorStateClass.MEASUREMENT,
            lambda c: c.current_import_rate),
        WattKostSensor(coordinator, entry.entry_id, "electricity_export_rate",
            "Stroom actueel teruglevertarief", "EUR/kWh", "mdi:cash-plus",
            None, SensorStateClass.MEASUREMENT,
            lambda c: c.current_export_rate),
        WattKostSensor(coordinator, entry.entry_id, "electricity_daily_variable_cost",
            "Stroom variabele dagkosten", "EUR", "mdi:lightning-bolt",
            SensorDeviceClass.MONETARY, SensorStateClass.MEASUREMENT,
            lambda c: c.electricity_daily_variable_cost),
        WattKostSensor(coordinator, entry.entry_id, "electricity_daily_fixed_cost",
            "Stroom vaste dagkosten", "EUR", "mdi:calendar-today",
            SensorDeviceClass.MONETARY, SensorStateClass.MEASUREMENT,
            lambda c: c.electricity_daily_fixed_cost),
        WattKostSensor(coordinator, entry.entry_id, "electricity_daily_total_cost",
            "Stroom totale dagkosten", "EUR", "mdi:lightning-bolt",
            SensorDeviceClass.MONETARY, SensorStateClass.MEASUREMENT,
            lambda c: c.electricity_daily_total_cost),
        WattKostSensor(coordinator, entry.entry_id, "electricity_monthly_cost",
            "Stroom maandkosten", "EUR", "mdi:lightning-bolt",
            SensorDeviceClass.MONETARY, SensorStateClass.MEASUREMENT,
            lambda c: c.electricity_monthly_cost),
        WattKostSensor(coordinator, entry.entry_id, "electricity_net_daily_kwh",
            "Stroom netto dag kWh", "kWh", "mdi:transmission-tower",
            SensorDeviceClass.ENERGY, SensorStateClass.MEASUREMENT,
            lambda c: c.net_daily_kwh),
        WattKostSensor(coordinator, entry.entry_id, "gas_daily_cost",
            "Gas dagkosten", "EUR", "mdi:gas-burner",
            SensorDeviceClass.MONETARY, SensorStateClass.MEASUREMENT,
            lambda c: c.gas_daily_cost),
        WattKostSensor(coordinator, entry.entry_id, "gas_monthly_cost",
            "Gas maandkosten", "EUR", "mdi:gas-burner",
            SensorDeviceClass.MONETARY, SensorStateClass.MEASUREMENT,
            lambda c: c.gas_monthly_cost),
        WattKostSensor(coordinator, entry.entry_id, "total_daily_cost",
            "Totale dagkosten energie", "EUR", "mdi:cash",
            SensorDeviceClass.MONETARY, SensorStateClass.MEASUREMENT,
            lambda c: c.total_daily_cost),
        WattKostSensor(coordinator, entry.entry_id, "total_monthly_cost",
            "Totale maandkosten energie", "EUR", "mdi:cash",
            SensorDeviceClass.MONETARY, SensorStateClass.MEASUREMENT,
            lambda c: c.total_monthly_cost),
    ]

    async_add_entities(sensors)
    await coordinator.async_setup(sensors)


class WattKostCoordinator:

    def __init__(self, hass: HomeAssistant, config: dict[str, Any], entry_id: str) -> None:
        self.hass = hass
        self.config = config
        self.entry_id = entry_id
        self._sensors: list[WattKostSensor] = []

        self._current_day: date = dt_util.now().date()
        self._current_month: int = dt_util.now().month

        self._day_start_import_t1: float | None = None
        self._day_start_import_t2: float | None = None
        self._day_start_export_t1: float | None = None
        self._day_start_export_t2: float | None = None
        self._day_start_import_total: float | None = None
        self._day_start_export_total: float | None = None
        self._day_start_gas: float | None = None

        self._month_start_import_t1: float | None = None
        self._month_start_import_t2: float | None = None
        self._month_start_export_t1: float | None = None
        self._month_start_export_t2: float | None = None
        self._month_start_import_total: float | None = None
        self._month_start_export_total: float | None = None
        self._month_start_gas: float | None = None

        self.electricity_current_cost_eur_h: float | None = None
        self.current_import_rate: float | None = None
        self.current_export_rate: float | None = None
        self.electricity_daily_variable_cost: float | None = None
        self.electricity_daily_fixed_cost: float | None = None
        self.electricity_daily_total_cost: float | None = None
        self.electricity_monthly_cost: float | None = None
        self.net_daily_kwh: float | None = None
        self.gas_daily_cost: float | None = None
        self.gas_monthly_cost: float | None = None
        self.total_daily_cost: float | None = None
        self.total_monthly_cost: float | None = None

    @property
    def _import_rate(self) -> float:
        return float(self.config.get(CONF_TARIFF_NORMAAL, DEFAULT_TARIFF_NORMAAL))

    @property
    def _return_rate(self) -> float:
        use_saldering = self.config.get(CONF_USE_SALDERING, DEFAULT_USE_SALDERING)
        if not use_saldering:
            cost = float(self.config.get(CONF_TARIFF_RETURN_COST, DEFAULT_TARIFF_RETURN_COST))
            return -cost
        credit = float(self.config.get(CONF_TARIFF_RETURN, DEFAULT_TARIFF_RETURN)) * 1.21
        cost = float(self.config.get(CONF_TARIFF_RETURN_COST, DEFAULT_TARIFF_RETURN_COST))
        return credit - cost

    @property
    def _fixed_day_electricity(self) -> float:
        fixed = float(self.config.get(CONF_FIXED_DELIVERY_DAY_ELECTRICITY, DEFAULT_FIXED_DELIVERY_DAY_ELECTRICITY))
        system = float(self.config.get(CONF_SYSTEM_OPERATOR_DAY_ELECTRICITY, DEFAULT_SYSTEM_OPERATOR_DAY_ELECTRICITY))
        reduction = float(self.config.get(CONF_ENERGY_REDUCTION_YEAR, DEFAULT_ENERGY_REDUCTION_DAY * DAYS_PER_YEAR)) / DAYS_PER_YEAR
        return fixed + system + reduction

    @property
    def _fixed_day_gas(self) -> float:
        fixed = float(self.config.get(CONF_FIXED_DELIVERY_DAY_GAS, DEFAULT_FIXED_DELIVERY_DAY_GAS))
        system = float(self.config.get(CONF_SYSTEM_OPERATOR_DAY_GAS, DEFAULT_SYSTEM_OPERATOR_DAY_GAS))
        return fixed + system

    def _kwh_import_today(self) -> float:
        t1 = _safe_float(self.hass, self.config.get(CONF_IMPORT_T1_KWH))
        t2 = _safe_float(self.hass, self.config.get(CONF_IMPORT_T2_KWH))
        total = _safe_float(self.hass, self.config.get(CONF_IMPORT_TOTAL_KWH))
        if t1 is not None and t2 is not None:
            return max(0.0, (t1 - (self._day_start_import_t1 or t1)) + (t2 - (self._day_start_import_t2 or t2)))
        if total is not None:
            return max(0.0, total - (self._day_start_import_total or total))
        return 0.0

    def _kwh_export_today(self) -> float:
        t1 = _safe_float(self.hass, self.config.get(CONF_EXPORT_T1_KWH))
        t2 = _safe_float(self.hass, self.config.get(CONF_EXPORT_T2_KWH))
        total = _safe_float(self.hass, self.config.get(CONF_EXPORT_TOTAL_KWH))
        if t1 is not None and t2 is not None:
            return max(0.0, (t1 - (self._day_start_export_t1 or t1)) + (t2 - (self._day_start_export_t2 or t2)))
        if total is not None:
            return max(0.0, total - (self._day_start_export_total or total))
        return 0.0

    def _kwh_import_month(self) -> float:
        t1 = _safe_float(self.hass, self.config.get(CONF_IMPORT_T1_KWH))
        t2 = _safe_float(self.hass, self.config.get(CONF_IMPORT_T2_KWH))
        total = _safe_float(self.hass, self.config.get(CONF_IMPORT_TOTAL_KWH))
        if t1 is not None and t2 is not None:
            return max(0.0, (t1 - (self._month_start_import_t1 or t1)) + (t2 - (self._month_start_import_t2 or t2)))
        if total is not None:
            return max(0.0, total - (self._month_start_import_total or total))
        return 0.0

    def _kwh_export_month(self) -> float:
        t1 = _safe_float(self.hass, self.config.get(CONF_EXPORT_T1_KWH))
        t2 = _safe_float(self.hass, self.config.get(CONF_EXPORT_T2_KWH))
        total = _safe_float(self.hass, self.config.get(CONF_EXPORT_TOTAL_KWH))
        if t1 is not None and t2 is not None:
            return max(0.0, (t1 - (self._month_start_export_t1 or t1)) + (t2 - (self._month_start_export_t2 or t2)))
        if total is not None:
            return max(0.0, total - (self._month_start_export_total or total))
        return 0.0

    def _gas_today_m3(self) -> float:
        gas = _safe_float(self.hass, self.config.get(CONF_GAS_DAILY_M3))
        if gas is None:
            return 0.0
        return max(0.0, gas - (self._day_start_gas or gas))

    def _gas_month_m3(self) -> float:
        gas = _safe_float(self.hass, self.config.get(CONF_GAS_DAILY_M3))
        if gas is None:
            return 0.0
        return max(0.0, gas - (self._month_start_gas or gas))

    def _snapshot_day_start(self) -> None:
        self._day_start_import_t1 = _safe_float(self.hass, self.config.get(CONF_IMPORT_T1_KWH))
        self._day_start_import_t2 = _safe_float(self.hass, self.config.get(CONF_IMPORT_T2_KWH))
        self._day_start_export_t1 = _safe_float(self.hass, self.config.get(CONF_EXPORT_T1_KWH))
        self._day_start_export_t2 = _safe_float(self.hass, self.config.get(CONF_EXPORT_T2_KWH))
        self._day_start_import_total = _safe_float(self.hass, self.config.get(CONF_IMPORT_TOTAL_KWH))
        self._day_start_export_total = _safe_float(self.hass, self.config.get(CONF_EXPORT_TOTAL_KWH))
        self._day_start_gas = _safe_float(self.hass, self.config.get(CONF_GAS_DAILY_M3))

    def _snapshot_month_start(self) -> None:
        self._month_start_import_t1 = _safe_float(self.hass, self.config.get(CONF_IMPORT_T1_KWH))
        self._month_start_import_t2 = _safe_float(self.hass, self.config.get(CONF_IMPORT_T2_KWH))
        self._month_start_export_t1 = _safe_float(self.hass, self.config.get(CONF_EXPORT_T1_KWH))
        self._month_start_export_t2 = _safe_float(self.hass, self.config.get(CONF_EXPORT_T2_KWH))
        self._month_start_import_total = _safe_float(self.hass, self.config.get(CONF_IMPORT_TOTAL_KWH))
        self._month_start_export_total = _safe_float(self.hass, self.config.get(CONF_EXPORT_TOTAL_KWH))
        self._month_start_gas = _safe_float(self.hass, self.config.get(CONF_GAS_DAILY_M3))

    def update(self) -> None:
        now = dt_util.now()
        today = now.date()

        if today != self._current_day:
            self._snapshot_day_start()
            self._current_day = today

        if now.month != self._current_month:
            self._snapshot_month_start()
            self._current_month = now.month

        if self._day_start_import_t1 is None and self._day_start_import_total is None:
            self._snapshot_day_start()
        if self._month_start_import_t1 is None and self._month_start_import_total is None:
            self._snapshot_month_start()

        self.current_import_rate = self._import_rate
        self.current_export_rate = self._return_rate

        import_w = _safe_float(self.hass, self.config.get(CONF_IMPORT_W))
        export_w = _safe_float(self.hass, self.config.get(CONF_EXPORT_W))

        if import_w is not None:
            cost_h = (import_w / 1000.0) * self._import_rate
            if export_w is not None and export_w > 0:
                cost_h -= (export_w / 1000.0) * self._return_rate
            self.electricity_current_cost_eur_h = cost_h
        else:
            self.electricity_current_cost_eur_h = None

        kwh_import = self._kwh_import_today()
        kwh_export = self._kwh_export_today()
        self.electricity_daily_variable_cost = round(kwh_import * self._import_rate - kwh_export * self._return_rate, 4)
        self.net_daily_kwh = round(kwh_import - kwh_export, 4)
        self.electricity_daily_fixed_cost = round(self._fixed_day_electricity, 4)
        self.electricity_daily_total_cost = round(self.electricity_daily_variable_cost + self.electricity_daily_fixed_cost, 4)

        days_in_month = (now.replace(month=now.month % 12 + 1, day=1) - timedelta(days=1)).day if now.month < 12 else 31
        self.electricity_monthly_cost = round(
            self._kwh_import_month() * self._import_rate - self._kwh_export_month() * self._return_rate + self._fixed_day_electricity * days_in_month, 4)

        gas_tariff = float(self.config.get(CONF_GAS_TARIFF, DEFAULT_GAS_TARIFF))
        self.gas_daily_cost = round(self._gas_today_m3() * gas_tariff + self._fixed_day_gas, 4)
        self.gas_monthly_cost = round(self._gas_month_m3() * gas_tariff + self._fixed_day_gas * days_in_month, 4)
        self.total_daily_cost = round(self.electricity_daily_total_cost + self.gas_daily_cost, 4)
        self.total_monthly_cost = round(self.electricity_monthly_cost + self.gas_monthly_cost, 4)

        for sensor in self._sensors:
            sensor.async_write_ha_state()

    async def async_setup(self, sensors: list) -> None:
        self._sensors = sensors
        watch_keys = [
            CONF_CONSUMPTION_W, CONF_CONSUMPTION_KWH,
            CONF_IMPORT_T1_KWH, CONF_IMPORT_T2_KWH, CONF_IMPORT_TOTAL_KWH, CONF_IMPORT_W,
            CONF_EXPORT_T1_KWH, CONF_EXPORT_T2_KWH, CONF_EXPORT_TOTAL_KWH, CONF_EXPORT_W,
            CONF_SOLAR_KWH, CONF_SOLAR_W, CONF_GAS_DAILY_M3,
        ]
        entity_ids = [self.config[k] for k in watch_keys if k in self.config and self.config[k]]

        @callback
        def _state_changed(_event: Any) -> None:
            self.update()

        if entity_ids:
            async_track_state_change_event(self.hass, entity_ids, _state_changed)

        @callback
        def _time_update(_now: Any) -> None:
            self.update()

        async_track_time_change(self.hass, _time_update, second=0)
        self.update()


class WattKostSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry_id, key, name, unit, icon, device_class, state_class, value_fn) -> None:
        self._coordinator = coordinator
        self._key = key
        self._value_fn = value_fn
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_suggested_display_precision = 4

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._coordinator.entry_id)},
            name="WattKost",
            manufacturer="WattKost",
            model="Energie Kostenberekening NL",
        )

    @property
    def native_value(self) -> float | None:
        try:
            val = self._value_fn(self._coordinator)
            return round(float(val), 4) if val is not None else None
        except Exception:
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self._key == "electricity_daily_total_cost":
            return {
                "variabele_kosten_eur": self._coordinator.electricity_daily_variable_cost,
                "vaste_kosten_eur": self._coordinator.electricity_daily_fixed_cost,
                "netto_import_kwh": self._coordinator.net_daily_kwh,
                "import_tarief_eur_kwh": self._coordinator.current_import_rate,
                "teruglever_tarief_eur_kwh": self._coordinator.current_export_rate,
            }
        return {}


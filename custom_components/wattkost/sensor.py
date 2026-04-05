"""Sensor platform for NL Energy Cost integration."""
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
    CONF_USE_SINGLE_TARIFF,
    CONF_USE_SALDERING,
    DEFAULT_USE_SALDERING,
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

DAYS_PER_YEAR = 365.2425


def _safe_float(hass: HomeAssistant, entity_id: str | None) -> float | None:
    """Safely retrieve float state of an entity."""
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
    """Set up NL Energy Cost sensors from config entry."""
    config = {**entry.data, **entry.options}

    coordinator = NLEnergyCostCoordinator(hass, config, entry.entry_id)

    sensors = [
        NLEnergyCostSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            key="saldo_import_jaar_kwh",
            name="Saldo import dit jaar",
            unit="kWh",
            icon="mdi:transmission-tower-import",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            value_fn=lambda c: c.saldo_import_jaar_kwh,
        ),
        NLEnergyCostSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            key="saldo_export_jaar_kwh",
            name="Saldo export dit jaar",
            unit="kWh",
            icon="mdi:transmission-tower-export",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            value_fn=lambda c: c.saldo_export_jaar_kwh,
        ),
        NLEnergyCostSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            key="saldo_netto_jaar_kwh",
            name="Saldo netto dit jaar",
            unit="kWh",
            icon="mdi:scale-balance",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda c: c.saldo_netto_jaar_kwh,
        ),
        NLEnergyCostSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            key="saldo_kosten_jaarafrekening",
            name="Geschatte jaarafrekening stroom",
            unit="€",
            icon="mdi:cash-clock",
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda c: c.saldo_kosten_jaarafrekening,
        ),
        NLEnergyCostSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            key="electricity_current_cost_eur_h",
            name="Stroom actuele kosten",
            unit="€/h",
            icon="mdi:lightning-bolt",
            device_class=None,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda c: c.electricity_current_cost_eur_h,
        ),
        NLEnergyCostSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            key="electricity_import_rate",
            name="Stroom actueel importtarief",
            unit="€/kWh",
            icon="mdi:cash-minus",
            device_class=None,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda c: c.current_import_rate,
        ),
        NLEnergyCostSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            key="electricity_export_rate",
            name="Stroom actueel teruglevertarief",
            unit="€/kWh",
            icon="mdi:cash-plus",
            device_class=None,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda c: c.current_export_rate,
        ),
        NLEnergyCostSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            key="electricity_daily_variable_cost",
            name="Stroom variabele dagkosten",
            unit="€",
            icon="mdi:lightning-bolt",
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            value_fn=lambda c: c.electricity_daily_variable_cost,
        ),
        NLEnergyCostSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            key="electricity_daily_fixed_cost",
            name="Stroom vaste dagkosten",
            unit="€",
            icon="mdi:calendar-today",
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda c: c.electricity_daily_fixed_cost,
        ),
        NLEnergyCostSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            key="electricity_daily_total_cost",
            name="Stroom totale dagkosten",
            unit="€",
            icon="mdi:lightning-bolt",
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            value_fn=lambda c: c.electricity_daily_total_cost,
        ),
        NLEnergyCostSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            key="electricity_monthly_cost",
            name="Stroom maandkosten",
            unit="€",
            icon="mdi:lightning-bolt",
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            value_fn=lambda c: c.electricity_monthly_cost,
        ),
        NLEnergyCostSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            key="electricity_net_daily_kwh",
            name="Stroom netto dag kWh (import - export)",
            unit="kWh",
            icon="mdi:transmission-tower",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            value_fn=lambda c: c.net_daily_kwh,
        ),
        NLEnergyCostSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            key="gas_daily_cost",
            name="Gas dagkosten",
            unit="€",
            icon="mdi:gas-burner",
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            value_fn=lambda c: c.gas_daily_cost,
        ),
        NLEnergyCostSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            key="gas_monthly_cost",
            name="Gas maandkosten",
            unit="€",
            icon="mdi:gas-burner",
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            value_fn=lambda c: c.gas_monthly_cost,
        ),
        NLEnergyCostSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            key="total_daily_cost",
            name="Totale dagkosten energie",
            unit="€",
            icon="mdi:cash",
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            value_fn=lambda c: c.total_daily_cost,
        ),
        NLEnergyCostSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            key="total_monthly_cost",
            name="Totale maandkosten energie",
            unit="€",
            icon="mdi:cash",
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            value_fn=lambda c: c.total_monthly_cost,
        ),
    ]

    async_add_entities(sensors)
    await coordinator.async_setup(sensors)


class NLEnergyCostCoordinator:
    """Central coordinator that tracks all state and computes costs."""

    def __init__(
        self,
        hass: HomeAssistant,
        config: dict[str, Any],
        entry_id: str,
    ) -> None:
        """Initialize coordinator."""
        self.hass = hass
        self.config = config
        self.entry_id = entry_id
        self._sensors: list[NLEnergyCostSensor] = []

        # Day tracking
        self._current_day: date = dt_util.now().date()
        self._day_start_import_t1: float | None = None
        self._day_start_import_t2: float | None = None
        self._day_start_export_t1: float | None = None
        self._day_start_export_t2: float | None = None
        self._day_start_solar: float | None = None
        self._day_start_import_total: float | None = None
        self._day_start_export_total: float | None = None

        # Month tracking
        self._month_start_import_t1: float | None = None
        self._month_start_import_t2: float | None = None
        self._month_start_export_t1: float | None = None
        self._month_start_export_t2: float | None = None
        self._month_start_solar: float | None = None
        self._month_start_import_total: float | None = None
        self._month_start_export_total: float | None = None
        self._month_start_gas: float | None = None
        self._day_start_gas: float | None = None
        self._current_month: int = dt_util.now().month

        # Year tracking (salderingsbalans)
        self._year_start_import_t1: float | None = None
        self._year_start_import_t2: float | None = None
        self._year_start_export_t1: float | None = None
        self._year_start_export_t2: float | None = None
        self._year_start_import_total: float | None = None
        self._year_start_export_total: float | None = None
        self._current_year: int = dt_util.now().year

        # Computed values
        self.saldo_import_jaar_kwh: float | None = None
        self.saldo_export_jaar_kwh: float | None = None
        self.saldo_netto_jaar_kwh: float | None = None
        self.saldo_kosten_jaarafrekening: float | None = None
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
    def _cfg(self) -> dict[str, Any]:
        return self.config

    def _get(self, key: str, default: Any = None) -> Any:
        return self._cfg.get(key, default)

    @property
    def _import_rate(self) -> float:
        """Active import rate (enkel or normaal/dal based on T1/T2 availability)."""
        use_single = self._get(CONF_USE_SINGLE_TARIFF, DEFAULT_USE_SINGLE_TARIFF)
        if use_single:
            return float(self._get(CONF_TARIFF_ENKEL, DEFAULT_TARIFF_ENKEL))
        # Use normaal for T1 (day) — caller decides which to use
        return float(self._get(CONF_TARIFF_NORMAAL, DEFAULT_TARIFF_NORMAAL))

    @property
    def _dal_rate(self) -> float:
        return float(self._get(CONF_TARIFF_DAL, DEFAULT_TARIFF_DAL))

    @property
    def _return_rate(self) -> float:
        """Net return rate: saldering credit minus terugleveerkosten."""
        credit = float(self._get(CONF_TARIFF_RETURN, DEFAULT_TARIFF_RETURN)) * 1.21  # excl BTW -> incl
        cost = float(self._get(CONF_TARIFF_RETURN_COST, DEFAULT_TARIFF_RETURN_COST))
        return credit - cost  # positive = credit per kWh terug

    @property
    def _fixed_day_electricity(self) -> float:
        """Total fixed electricity costs per day (incl. BTW)."""
        fixed = float(self._get(CONF_FIXED_DELIVERY_DAY_ELECTRICITY, DEFAULT_FIXED_DELIVERY_DAY_ELECTRICITY))
        system = float(self._get(CONF_SYSTEM_OPERATOR_DAY_ELECTRICITY, DEFAULT_SYSTEM_OPERATOR_DAY_ELECTRICITY))
        reduction_day = float(self._get(CONF_ENERGY_REDUCTION_YEAR, DEFAULT_ENERGY_REDUCTION_DAY))
        return fixed + system + reduction_day

    @property
    def _fixed_day_gas(self) -> float:
        """Total fixed gas costs per day (incl. BTW)."""
        fixed = float(self._get(CONF_FIXED_DELIVERY_DAY_GAS, DEFAULT_FIXED_DELIVERY_DAY_GAS))
        system = float(self._get(CONF_SYSTEM_OPERATOR_DAY_GAS, DEFAULT_SYSTEM_OPERATOR_DAY_GAS))
        return fixed + system

    def _kwh_import_today(self) -> float:
        """Total kWh imported today (T1+T2 or total)."""
        t1 = _safe_float(self.hass, self._get(CONF_IMPORT_T1_KWH))
        t2 = _safe_float(self.hass, self._get(CONF_IMPORT_T2_KWH))
        total = _safe_float(self.hass, self._get(CONF_IMPORT_TOTAL_KWH))

        if t1 is not None and t2 is not None:
            current_t1 = t1 - (self._day_start_import_t1 or t1)
            current_t2 = t2 - (self._day_start_import_t2 or t2)
            return max(0.0, current_t1 + current_t2)
        if total is not None:
            return max(0.0, total - (self._day_start_import_total or total))
        return 0.0

    def _kwh_export_today(self) -> float:
        """Total kWh exported today (T1+T2 or total)."""
        t1 = _safe_float(self.hass, self._get(CONF_EXPORT_T1_KWH))
        t2 = _safe_float(self.hass, self._get(CONF_EXPORT_T2_KWH))
        total = _safe_float(self.hass, self._get(CONF_EXPORT_TOTAL_KWH))

        if t1 is not None and t2 is not None:
            current_t1 = t1 - (self._day_start_export_t1 or t1)
            current_t2 = t2 - (self._day_start_export_t2 or t2)
            return max(0.0, current_t1 + current_t2)
        if total is not None:
            return max(0.0, total - (self._day_start_export_total or total))
        return 0.0

    def _kwh_solar_today(self) -> float:
        """Solar production today."""
        solar = _safe_float(self.hass, self._get(CONF_SOLAR_KWH))
        if solar is None:
            return 0.0
        return max(0.0, solar - (self._day_start_solar or solar))

    def _kwh_import_month(self) -> float:
        t1 = _safe_float(self.hass, self._get(CONF_IMPORT_T1_KWH))
        t2 = _safe_float(self.hass, self._get(CONF_IMPORT_T2_KWH))
        total = _safe_float(self.hass, self._get(CONF_IMPORT_TOTAL_KWH))

        if t1 is not None and t2 is not None:
            delta_t1 = t1 - (self._month_start_import_t1 or t1)
            delta_t2 = t2 - (self._month_start_import_t2 or t2)
            return max(0.0, delta_t1 + delta_t2)
        if total is not None:
            return max(0.0, total - (self._month_start_import_total or total))
        return 0.0

    def _kwh_export_month(self) -> float:
        t1 = _safe_float(self.hass, self._get(CONF_EXPORT_T1_KWH))
        t2 = _safe_float(self.hass, self._get(CONF_EXPORT_T2_KWH))
        total = _safe_float(self.hass, self._get(CONF_EXPORT_TOTAL_KWH))

        if t1 is not None and t2 is not None:
            delta_t1 = t1 - (self._month_start_export_t1 or t1)
            delta_t2 = t2 - (self._month_start_export_t2 or t2)
            return max(0.0, delta_t1 + delta_t2)
        if total is not None:
            return max(0.0, total - (self._month_start_export_total or total))
        return 0.0

    def _gas_today_m3(self) -> float:
        gas = _safe_float(self.hass, self._get(CONF_GAS_DAILY_M3))
        if gas is None:
            return 0.0
        return max(0.0, gas - (self._day_start_gas or gas))

    def _gas_month_m3(self) -> float:
        gas = _safe_float(self.hass, self._get(CONF_GAS_DAILY_M3))
        if gas is None:
            return 0.0
        return max(0.0, gas - (self._month_start_gas or gas))

    def _snapshot_day_start(self) -> None:
        """Snapshot current sensor values as the day-start baseline."""
        self._day_start_import_t1 = _safe_float(self.hass, self._get(CONF_IMPORT_T1_KWH))
        self._day_start_import_t2 = _safe_float(self.hass, self._get(CONF_IMPORT_T2_KWH))
        self._day_start_export_t1 = _safe_float(self.hass, self._get(CONF_EXPORT_T1_KWH))
        self._day_start_export_t2 = _safe_float(self.hass, self._get(CONF_EXPORT_T2_KWH))
        self._day_start_solar = _safe_float(self.hass, self._get(CONF_SOLAR_KWH))
        self._day_start_import_total = _safe_float(self.hass, self._get(CONF_IMPORT_TOTAL_KWH))
        self._day_start_export_total = _safe_float(self.hass, self._get(CONF_EXPORT_TOTAL_KWH))
        self._day_start_gas = _safe_float(self.hass, self._get(CONF_GAS_DAILY_M3))

    def _snapshot_month_start(self) -> None:
        """Snapshot current sensor values as the month-start baseline."""
        self._month_start_import_t1 = _safe_float(self.hass, self._get(CONF_IMPORT_T1_KWH))
        self._month_start_import_t2 = _safe_float(self.hass, self._get(CONF_IMPORT_T2_KWH))
        self._month_start_export_t1 = _safe_float(self.hass, self._get(CONF_EXPORT_T1_KWH))
        self._month_start_export_t2 = _safe_float(self.hass, self._get(CONF_EXPORT_T2_KWH))
        self._month_start_solar = _safe_float(self.hass, self._get(CONF_SOLAR_KWH))
        self._month_start_import_total = _safe_float(self.hass, self._get(CONF_IMPORT_TOTAL_KWH))
        self._month_start_export_total = _safe_float(self.hass, self._get(CONF_EXPORT_TOTAL_KWH))
        self._month_start_gas = _safe_float(self.hass, self._get(CONF_GAS_DAILY_M3))

    def _snapshot_year_start(self) -> None:
        """Snapshot current sensor values as the year-start baseline."""
        self._year_start_import_t1 = _safe_float(self.hass, self._get(CONF_IMPORT_T1_KWH))
        self._year_start_import_t2 = _safe_float(self.hass, self._get(CONF_IMPORT_T2_KWH))
        self._year_start_export_t1 = _safe_float(self.hass, self._get(CONF_EXPORT_T1_KWH))
        self._year_start_export_t2 = _safe_float(self.hass, self._get(CONF_EXPORT_T2_KWH))
        self._year_start_import_total = _safe_float(self.hass, self._get(CONF_IMPORT_TOTAL_KWH))
        self._year_start_export_total = _safe_float(self.hass, self._get(CONF_EXPORT_TOTAL_KWH))

    def _kwh_import_year(self) -> float:
        t1 = _safe_float(self.hass, self._get(CONF_IMPORT_T1_KWH))
        t2 = _safe_float(self.hass, self._get(CONF_IMPORT_T2_KWH))
        total = _safe_float(self.hass, self._get(CONF_IMPORT_TOTAL_KWH))
        if t1 is not None and t2 is not None:
            return max(0.0, (t1 - (self._year_start_import_t1 or t1)) + (t2 - (self._year_start_import_t2 or t2)))
        if total is not None:
            return max(0.0, total - (self._year_start_import_total or total))
        return 0.0

    def _kwh_export_year(self) -> float:
        t1 = _safe_float(self.hass, self._get(CONF_EXPORT_T1_KWH))
        t2 = _safe_float(self.hass, self._get(CONF_EXPORT_T2_KWH))
        total = _safe_float(self.hass, self._get(CONF_EXPORT_TOTAL_KWH))
        if t1 is not None and t2 is not None:
            return max(0.0, (t1 - (self._year_start_export_t1 or t1)) + (t2 - (self._year_start_export_t2 or t2)))
        if total is not None:
            return max(0.0, total - (self._year_start_export_total or total))
        return 0.0

    def update(self) -> None:
        """Recompute all cost sensors."""
        now = dt_util.now()
        today = now.date()

        # Day rollover
        if today != self._current_day:
            self._snapshot_day_start()
            self._current_day = today

        # Month rollover
        if now.month != self._current_month:
            self._snapshot_month_start()
            self._current_month = now.month

        # Year rollover
        if now.year != self._current_year:
            self._snapshot_year_start()
            self._current_year = now.year

        # Initialize baselines on first run
        if self._day_start_import_t1 is None and self._day_start_import_total is None:
            self._snapshot_day_start()
        if self._month_start_import_t1 is None and self._month_start_import_total is None:
            self._snapshot_month_start()
        if self._year_start_import_t1 is None and self._year_start_import_total is None:
            self._snapshot_year_start()

        # --- Current rate & instantaneous cost ---
        import_w = _safe_float(self.hass, self._get(CONF_IMPORT_W))
        export_w = _safe_float(self.hass, self._get(CONF_EXPORT_W))

        self.current_import_rate = self._import_rate
        self.current_export_rate = self._return_rate

        if import_w is not None:
            import_kw = import_w / 1000.0
            self.electricity_current_cost_eur_h = import_kw * self._import_rate
            # If we're exporting (net negative import or positive export)
            if export_w is not None and export_w > 0:
                export_kw = export_w / 1000.0
                self.electricity_current_cost_eur_h -= export_kw * self._return_rate
        else:
            self.electricity_current_cost_eur_h = None

        # --- Daily variable costs ---
        kwh_import = self._kwh_import_today()
        kwh_export = self._kwh_export_today()
        use_saldering = self._get(CONF_USE_SALDERING, DEFAULT_USE_SALDERING)

        if use_saldering:
            # Saldering: export saldeert eerst tegen import tegen hetzelfde importtarief.
            # Alleen surplus export (meer dan import) krijgt de lagere terugleververgoeding.
            if kwh_export <= kwh_import:
                daily_variable = (kwh_import - kwh_export) * self._import_rate
            else:
                daily_variable = -(kwh_export - kwh_import) * self._return_rate
        else:
            # Zonder saldering: import en export apart verrekenen
            daily_variable = (kwh_import * self._import_rate) - (kwh_export * self._return_rate)
        self.electricity_daily_variable_cost = round(daily_variable, 4)
        self.net_daily_kwh = round(kwh_import - kwh_export, 4)

        # Daily fixed
        self.electricity_daily_fixed_cost = round(self._fixed_day_electricity, 4)

        # Daily total
        self.electricity_daily_total_cost = round(
            self.electricity_daily_variable_cost + self.electricity_daily_fixed_cost, 4
        )

        # Monthly electricity
        kwh_import_m = self._kwh_import_month()
        kwh_export_m = self._kwh_export_month()
        days_in_month = (
            (now.replace(month=now.month % 12 + 1, day=1) - timedelta(days=1)).day
            if now.month < 12
            else 31
        )
        monthly_fixed = self._fixed_day_electricity * days_in_month
        if use_saldering:
            if kwh_export_m <= kwh_import_m:
                monthly_variable = (kwh_import_m - kwh_export_m) * self._import_rate
            else:
                monthly_variable = -(kwh_export_m - kwh_import_m) * self._return_rate
        else:
            monthly_variable = (kwh_import_m * self._import_rate) - (kwh_export_m * self._return_rate)
        self.electricity_monthly_cost = round(monthly_fixed + monthly_variable, 4)

        # --- Salderingsbalans jaar ---
        kwh_import_y = self._kwh_import_year()
        kwh_export_y = self._kwh_export_year()
        self.saldo_import_jaar_kwh = round(kwh_import_y, 3)
        self.saldo_export_jaar_kwh = round(kwh_export_y, 3)
        self.saldo_netto_jaar_kwh = round(kwh_import_y - kwh_export_y, 3)
        if use_saldering:
            if kwh_export_y <= kwh_import_y:
                saldo_var = (kwh_import_y - kwh_export_y) * self._import_rate
            else:
                saldo_var = -(kwh_export_y - kwh_import_y) * self._return_rate
        else:
            saldo_var = (kwh_import_y * self._import_rate) - (kwh_export_y * self._return_rate)
        day_of_year = now.timetuple().tm_yday
        # Fixed costs: pro-rated for days elapsed this year
        yearly_fixed_ytd = self._fixed_day_electricity * day_of_year
        # Variable costs: year-to-date actual (no extrapolation)
        self.saldo_kosten_jaarafrekening = round(saldo_var + yearly_fixed_ytd, 2)

        # --- Gas ---
        gas_tariff = float(self._get(CONF_GAS_TARIFF, DEFAULT_GAS_TARIFF))
        gas_today = self._gas_today_m3()
        gas_month = self._gas_month_m3()

        self.gas_daily_cost = round(
            gas_today * gas_tariff + self._fixed_day_gas, 4
        )
        self.gas_monthly_cost = round(
            gas_month * gas_tariff + self._fixed_day_gas * days_in_month, 4
        )

        # --- Totals ---
        self.total_daily_cost = round(
            self.electricity_daily_total_cost + self.gas_daily_cost, 4
        )
        self.total_monthly_cost = round(
            self.electricity_monthly_cost + self.gas_monthly_cost, 4
        )

        # Push updates to sensors
        for sensor in self._sensors:
            sensor.async_write_ha_state()

    async def async_setup(self, sensors: list[NLEnergyCostSensor]) -> None:
        """Subscribe to state changes for all configured source sensors."""
        self._sensors = sensors

        # Collect all configured entity IDs to watch
        watch_keys = [
            CONF_CONSUMPTION_W, CONF_CONSUMPTION_KWH,
            CONF_IMPORT_T1_KWH, CONF_IMPORT_T2_KWH, CONF_IMPORT_TOTAL_KWH, CONF_IMPORT_W,
            CONF_EXPORT_T1_KWH, CONF_EXPORT_T2_KWH, CONF_EXPORT_TOTAL_KWH, CONF_EXPORT_W,
            CONF_SOLAR_KWH, CONF_SOLAR_W,
            CONF_GAS_DAILY_M3,
        ]
        entity_ids = [
            self.config[k] for k in watch_keys if k in self.config and self.config[k]
        ]

        @callback
        def _state_changed(_event: Any) -> None:
            self.update()

        if entity_ids:
            async_track_state_change_event(self.hass, entity_ids, _state_changed)

        # Also update every minute for fixed daily cost drift
        @callback
        def _time_update(_now: Any) -> None:
            self.update()

        async_track_time_change(self.hass, _time_update, second=0)

        # Initial computation
        self.update()


class NLEnergyCostSensor(SensorEntity):
    """A single computed cost sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NLEnergyCostCoordinator,
        entry_id: str,
        key: str,
        name: str,
        unit: str,
        icon: str,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass,
        value_fn,
    ) -> None:
        """Initialize sensor."""
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
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._coordinator.entry_id)},
            name="WattKost",
            manufacturer="WattKost",
            model="Energie Kostenberekening NL",
        )

    @property
    def native_value(self) -> float | None:
        """Return computed sensor value."""
        try:
            val = self._value_fn(self._coordinator)
            if val is None:
                return None
            return round(float(val), 4)
        except Exception:  # noqa: BLE001
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra diagnostic attributes."""
        if self._key == "electricity_daily_total_cost":
            return {
                "variabele_kosten_eur": self._coordinator.electricity_daily_variable_cost,
                "vaste_kosten_eur": self._coordinator.electricity_daily_fixed_cost,
                "netto_import_kwh": self._coordinator.net_daily_kwh,
                "import_tarief_eur_kwh": self._coordinator.current_import_rate,
                "teruglever_tarief_eur_kwh": self._coordinator.current_export_rate,
            }
        if self._key == "gas_daily_cost":
            return {
                "gas_tarief_eur_m3": self._coordinator.config.get(CONF_GAS_TARIFF, DEFAULT_GAS_TARIFF),
                "vaste_gaskosten_eur": self._coordinator._fixed_day_gas,
            }
        return {}

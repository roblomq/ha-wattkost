"""Sensor platform for NL Energy Cost integration."""
from __future__ import annotations

import datetime
import logging
from datetime import date, timedelta
from functools import partial
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
from homeassistant.helpers.storage import Store
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
    CONF_SALDO_START_MONTH,
    CONF_SALDO_START_DAY,
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
    DEFAULT_USE_SALDERING,
    DEFAULT_SALDO_START_MONTH,
    DEFAULT_SALDO_START_DAY,
    DEFAULT_FIXED_DELIVERY_DAY_ELECTRICITY,
    DEFAULT_SYSTEM_OPERATOR_DAY_ELECTRICITY,
    DEFAULT_ENERGY_REDUCTION_DAY,
    DEFAULT_GAS_TARIFF,
    DEFAULT_FIXED_DELIVERY_DAY_GAS,
    DEFAULT_SYSTEM_OPERATOR_DAY_GAS,
)

_LOGGER = logging.getLogger(__name__)

DAYS_PER_YEAR = 365.2425
STORAGE_VERSION = 1


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


def _contract_year_start(now: datetime.datetime, start_month: int, start_day: int) -> datetime.datetime:
    """Return the most recent contract year start datetime."""
    tz = now.tzinfo
    this_year_start = datetime.datetime(now.year, start_month, start_day, 0, 0, 0, tzinfo=tz)
    if now >= this_year_start:
        return this_year_start
    return datetime.datetime(now.year - 1, start_month, start_day, 0, 0, 0, tzinfo=tz)


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
            precision=2,
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
            precision=2,
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
            precision=2,
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
            precision=2,
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
            precision=2,
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
            precision=5,
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
            precision=5,
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
            precision=2,
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
            precision=2,
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
            precision=2,
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
            precision=2,
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
            precision=2,
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
            precision=2,
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
            precision=2,
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
            precision=2,
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
            precision=2,
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
        self._store: Store | None = None

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

        # Contract year tracking (salderingsbalans)
        self._contract_year_start_dt: datetime.datetime | None = None
        self._year_start_import_t1: float | None = None
        self._year_start_import_t2: float | None = None
        self._year_start_export_t1: float | None = None
        self._year_start_export_t2: float | None = None
        self._year_start_import_total: float | None = None
        self._year_start_export_total: float | None = None

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
        use_single = self._get(CONF_USE_SINGLE_TARIFF, DEFAULT_USE_SINGLE_TARIFF)
        if use_single:
            return float(self._get(CONF_TARIFF_ENKEL, DEFAULT_TARIFF_ENKEL))
        return float(self._get(CONF_TARIFF_NORMAAL, DEFAULT_TARIFF_NORMAAL))

    @property
    def _dal_rate(self) -> float:
        return float(self._get(CONF_TARIFF_DAL, DEFAULT_TARIFF_DAL))

    @property
    def _return_rate(self) -> float:
        credit = float(self._get(CONF_TARIFF_RETURN, DEFAULT_TARIFF_RETURN)) * 1.21
        cost = float(self._get(CONF_TARIFF_RETURN_COST, DEFAULT_TARIFF_RETURN_COST))
        return credit - cost

    @property
    def _fixed_day_electricity(self) -> float:
        fixed = float(self._get(CONF_FIXED_DELIVERY_DAY_ELECTRICITY, DEFAULT_FIXED_DELIVERY_DAY_ELECTRICITY))
        system = float(self._get(CONF_SYSTEM_OPERATOR_DAY_ELECTRICITY, DEFAULT_SYSTEM_OPERATOR_DAY_ELECTRICITY))
        reduction_day = float(self._get(CONF_ENERGY_REDUCTION_YEAR, DEFAULT_ENERGY_REDUCTION_DAY))
        return fixed + system + reduction_day

    @property
    def _fixed_day_gas(self) -> float:
        fixed = float(self._get(CONF_FIXED_DELIVERY_DAY_GAS, DEFAULT_FIXED_DELIVERY_DAY_GAS))
        system = float(self._get(CONF_SYSTEM_OPERATOR_DAY_GAS, DEFAULT_SYSTEM_OPERATOR_DAY_GAS))
        return fixed + system

    def _kwh_import_today(self) -> float:
        t1 = _safe_float(self.hass, self._get(CONF_IMPORT_T1_KWH))
        t2 = _safe_float(self.hass, self._get(CONF_IMPORT_T2_KWH))
        total = _safe_float(self.hass, self._get(CONF_IMPORT_TOTAL_KWH))
        if t1 is not None and t2 is not None:
            return max(0.0, (t1 - (self._day_start_import_t1 or t1)) + (t2 - (self._day_start_import_t2 or t2)))
        if total is not None:
            return max(0.0, total - (self._day_start_import_total or total))
        return 0.0

    def _kwh_export_today(self) -> float:
        t1 = _safe_float(self.hass, self._get(CONF_EXPORT_T1_KWH))
        t2 = _safe_float(self.hass, self._get(CONF_EXPORT_T2_KWH))
        total = _safe_float(self.hass, self._get(CONF_EXPORT_TOTAL_KWH))
        if t1 is not None and t2 is not None:
            return max(0.0, (t1 - (self._day_start_export_t1 or t1)) + (t2 - (self._day_start_export_t2 or t2)))
        if total is not None:
            return max(0.0, total - (self._day_start_export_total or total))
        return 0.0

    def _kwh_solar_today(self) -> float:
        solar = _safe_float(self.hass, self._get(CONF_SOLAR_KWH))
        if solar is None:
            return 0.0
        return max(0.0, solar - (self._day_start_solar or solar))

    def _kwh_import_month(self) -> float:
        t1 = _safe_float(self.hass, self._get(CONF_IMPORT_T1_KWH))
        t2 = _safe_float(self.hass, self._get(CONF_IMPORT_T2_KWH))
        total = _safe_float(self.hass, self._get(CONF_IMPORT_TOTAL_KWH))
        if t1 is not None and t2 is not None:
            return max(0.0, (t1 - (self._month_start_import_t1 or t1)) + (t2 - (self._month_start_import_t2 or t2)))
        if total is not None:
            return max(0.0, total - (self._month_start_import_total or total))
        return 0.0

    def _kwh_export_month(self) -> float:
        t1 = _safe_float(self.hass, self._get(CONF_EXPORT_T1_KWH))
        t2 = _safe_float(self.hass, self._get(CONF_EXPORT_T2_KWH))
        total = _safe_float(self.hass, self._get(CONF_EXPORT_TOTAL_KWH))
        if t1 is not None and t2 is not None:
            return max(0.0, (t1 - (self._month_start_export_t1 or t1)) + (t2 - (self._month_start_export_t2 or t2)))
        if total is not None:
            return max(0.0, total - (self._month_start_export_total or total))
        return 0.0

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
        self._day_start_import_t1 = _safe_float(self.hass, self._get(CONF_IMPORT_T1_KWH))
        self._day_start_import_t2 = _safe_float(self.hass, self._get(CONF_IMPORT_T2_KWH))
        self._day_start_export_t1 = _safe_float(self.hass, self._get(CONF_EXPORT_T1_KWH))
        self._day_start_export_t2 = _safe_float(self.hass, self._get(CONF_EXPORT_T2_KWH))
        self._day_start_solar = _safe_float(self.hass, self._get(CONF_SOLAR_KWH))
        self._day_start_import_total = _safe_float(self.hass, self._get(CONF_IMPORT_TOTAL_KWH))
        self._day_start_export_total = _safe_float(self.hass, self._get(CONF_EXPORT_TOTAL_KWH))
        self._day_start_gas = _safe_float(self.hass, self._get(CONF_GAS_DAILY_M3))

    def _snapshot_month_start(self) -> None:
        self._month_start_import_t1 = _safe_float(self.hass, self._get(CONF_IMPORT_T1_KWH))
        self._month_start_import_t2 = _safe_float(self.hass, self._get(CONF_IMPORT_T2_KWH))
        self._month_start_export_t1 = _safe_float(self.hass, self._get(CONF_EXPORT_T1_KWH))
        self._month_start_export_t2 = _safe_float(self.hass, self._get(CONF_EXPORT_T2_KWH))
        self._month_start_solar = _safe_float(self.hass, self._get(CONF_SOLAR_KWH))
        self._month_start_import_total = _safe_float(self.hass, self._get(CONF_IMPORT_TOTAL_KWH))
        self._month_start_export_total = _safe_float(self.hass, self._get(CONF_EXPORT_TOTAL_KWH))
        self._month_start_gas = _safe_float(self.hass, self._get(CONF_GAS_DAILY_M3))

    def _snapshot_year_start_from_current(self) -> None:
        """Snapshot current meter values as year-start baseline and persist."""
        self._year_start_import_t1 = _safe_float(self.hass, self._get(CONF_IMPORT_T1_KWH))
        self._year_start_import_t2 = _safe_float(self.hass, self._get(CONF_IMPORT_T2_KWH))
        self._year_start_export_t1 = _safe_float(self.hass, self._get(CONF_EXPORT_T1_KWH))
        self._year_start_export_t2 = _safe_float(self.hass, self._get(CONF_EXPORT_T2_KWH))
        self._year_start_import_total = _safe_float(self.hass, self._get(CONF_IMPORT_TOTAL_KWH))
        self._year_start_export_total = _safe_float(self.hass, self._get(CONF_EXPORT_TOTAL_KWH))
        self.hass.async_create_task(self._async_save_year_start())

    async def _async_save_year_start(self) -> None:
        """Persist year-start values to storage."""
        if self._store is None or self._contract_year_start_dt is None:
            return
        await self._store.async_save({
            "contract_year_start": self._contract_year_start_dt.isoformat(),
            "import_t1": self._year_start_import_t1,
            "import_t2": self._year_start_import_t2,
            "export_t1": self._year_start_export_t1,
            "export_t2": self._year_start_export_t2,
            "import_total": self._year_start_import_total,
            "export_total": self._year_start_export_total,
        })

    async def _async_load_or_fetch_year_start(self) -> None:
        """Load persisted year-start values or fetch from recorder history."""
        now = dt_util.now()
        start_month = int(self._get(CONF_SALDO_START_MONTH, DEFAULT_SALDO_START_MONTH))
        start_day = int(self._get(CONF_SALDO_START_DAY, DEFAULT_SALDO_START_DAY))
        self._contract_year_start_dt = _contract_year_start(now, start_month, start_day)

        # Try loading from persistent storage first
        self._store = Store(
            self.hass, STORAGE_VERSION, f"wattkost_year_start_{self.entry_id}"
        )
        stored = await self._store.async_load()

        if stored:
            try:
                stored_dt = datetime.datetime.fromisoformat(stored["contract_year_start"])
                # Only use stored values if they match the current contract year start
                if abs((stored_dt - self._contract_year_start_dt).total_seconds()) < 86400:
                    self._year_start_import_t1 = stored.get("import_t1")
                    self._year_start_import_t2 = stored.get("import_t2")
                    self._year_start_export_t1 = stored.get("export_t1")
                    self._year_start_export_t2 = stored.get("export_t2")
                    self._year_start_import_total = stored.get("import_total")
                    self._year_start_export_total = stored.get("export_total")
                    _LOGGER.debug("WattKost: jaar-start geladen uit opslag (%s)", stored_dt.date())
                    return
            except Exception:
                pass

        # Try recorder history to get values at contract year start
        await self._async_fetch_year_start_from_recorder()

    async def _async_fetch_year_start_from_recorder(self) -> None:
        """Query recorder for sensor values at contract year start."""
        if self._contract_year_start_dt is None:
            return

        try:
            from homeassistant.components.recorder import get_instance
            from homeassistant.components.recorder.history import get_significant_states

            start_dt = self._contract_year_start_dt
            end_dt = start_dt + datetime.timedelta(hours=2)

            sensor_map = {
                CONF_IMPORT_T1_KWH: "_year_start_import_t1",
                CONF_IMPORT_T2_KWH: "_year_start_import_t2",
                CONF_EXPORT_T1_KWH: "_year_start_export_t1",
                CONF_EXPORT_T2_KWH: "_year_start_export_t2",
                CONF_IMPORT_TOTAL_KWH: "_year_start_import_total",
                CONF_EXPORT_TOTAL_KWH: "_year_start_export_total",
            }

            entity_ids = [
                self._get(k) for k in sensor_map if self._get(k)
            ]

            if not entity_ids:
                return

            recorder = get_instance(self.hass)

            def _query():
                return get_significant_states(
                    self.hass,
                    start_dt,
                    end_dt,
                    entity_ids,
                    minimal_response=True,
                    no_attributes=True,
                )

            history = await recorder.async_add_executor_job(_query)

            found_any = False
            for conf_key, attr in sensor_map.items():
                entity_id = self._get(conf_key)
                if not entity_id or entity_id not in history:
                    continue
                states = history[entity_id]
                if states:
                    try:
                        val = float(states[0].state)
                        setattr(self, attr, val)
                        found_any = True
                        _LOGGER.debug(
                            "WattKost: jaar-start %s = %.3f (via recorder)", entity_id, val
                        )
                    except (ValueError, TypeError):
                        pass

            if found_any:
                await self._async_save_year_start()
                return

        except Exception as err:
            _LOGGER.debug("WattKost: recorder lookup mislukt: %s", err)

        # Fallback: use current values as baseline
        _LOGGER.debug("WattKost: geen historische data, gebruik huidige waarden als jaar-start")
        self._snapshot_year_start_from_current()

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

        # Contract year rollover
        if self._contract_year_start_dt is not None:
            start_month = int(self._get(CONF_SALDO_START_MONTH, DEFAULT_SALDO_START_MONTH))
            start_day = int(self._get(CONF_SALDO_START_DAY, DEFAULT_SALDO_START_DAY))
            new_year_start = _contract_year_start(now, start_month, start_day)
            if new_year_start != self._contract_year_start_dt:
                self._contract_year_start_dt = new_year_start
                self._snapshot_year_start_from_current()

        # Initialize baselines on first run
        if self._day_start_import_t1 is None and self._day_start_import_total is None:
            self._snapshot_day_start()
        if self._month_start_import_t1 is None and self._month_start_import_total is None:
            self._snapshot_month_start()

        # --- Current rate & instantaneous cost ---
        import_w = _safe_float(self.hass, self._get(CONF_IMPORT_W))
        export_w = _safe_float(self.hass, self._get(CONF_EXPORT_W))

        self.current_import_rate = self._import_rate
        self.current_export_rate = self._return_rate

        if import_w is not None:
            import_kw = import_w / 1000.0
            self.electricity_current_cost_eur_h = import_kw * self._import_rate
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
            if kwh_export <= kwh_import:
                daily_variable = (kwh_import - kwh_export) * self._import_rate
            else:
                daily_variable = -(kwh_export - kwh_import) * self._return_rate
        else:
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

        # --- Salderingsbalans contract jaar ---
        kwh_import_y = self._kwh_import_year()
        kwh_export_y = self._kwh_export_year()
        self.saldo_import_jaar_kwh = round(kwh_import_y, 2)
        self.saldo_export_jaar_kwh = round(kwh_export_y, 2)
        self.saldo_netto_jaar_kwh = round(kwh_import_y - kwh_export_y, 2)

        if use_saldering:
            if kwh_export_y <= kwh_import_y:
                saldo_var = (kwh_import_y - kwh_export_y) * self._import_rate
            else:
                saldo_var = -(kwh_export_y - kwh_import_y) * self._return_rate
        else:
            saldo_var = (kwh_import_y * self._import_rate) - (kwh_export_y * self._return_rate)

        # Days elapsed since contract year start
        if self._contract_year_start_dt is not None:
            days_elapsed = max(1, (now - self._contract_year_start_dt).days)
        else:
            days_elapsed = now.timetuple().tm_yday
        yearly_fixed_ytd = self._fixed_day_electricity * days_elapsed
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

        # Load year-start from storage or recorder
        await self._async_load_or_fetch_year_start()

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

        # Update every 5 minutes for fixed daily cost drift (reduces DB writes)
        @callback
        def _time_update(_now: Any) -> None:
            self.update()

        async_track_time_change(self.hass, _time_update, minute=[0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55], second=0)

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
        precision: int = 2,
    ) -> None:
        """Initialize sensor."""
        self._coordinator = coordinator
        self._key = key
        self._value_fn = value_fn
        self._precision = precision
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_suggested_display_precision = precision

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
            return round(float(val), self._precision)
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
        if self._key == "saldo_kosten_jaarafrekening":
            return {
                "contract_jaar_start": (
                    self._coordinator._contract_year_start_dt.date().isoformat()
                    if self._coordinator._contract_year_start_dt else None
                ),
                "saldo_import_kwh": self._coordinator.saldo_import_jaar_kwh,
                "saldo_export_kwh": self._coordinator.saldo_export_jaar_kwh,
                "saldo_netto_kwh": self._coordinator.saldo_netto_jaar_kwh,
            }
        return {}

"""Constants for the NL Energy Cost integration."""

DOMAIN = "wattkost"
PLATFORMS = ["sensor"]

# Config entry keys - Electricity sensors
CONF_CONSUMPTION_W = "consumption_w_sensor"
CONF_CONSUMPTION_KWH = "consumption_kwh_sensor"

CONF_IMPORT_T1_KWH = "import_t1_kwh_sensor"
CONF_IMPORT_T2_KWH = "import_t2_kwh_sensor"
CONF_IMPORT_TOTAL_KWH = "import_total_kwh_sensor"
CONF_IMPORT_W = "import_w_sensor"

CONF_EXPORT_T1_KWH = "export_t1_kwh_sensor"
CONF_EXPORT_T2_KWH = "export_t2_kwh_sensor"
CONF_EXPORT_TOTAL_KWH = "export_total_kwh_sensor"
CONF_EXPORT_W = "export_w_sensor"

CONF_SOLAR_KWH = "solar_kwh_sensor"
CONF_SOLAR_W = "solar_w_sensor"

# Config entry keys - Gas sensors
CONF_GAS_DAILY_M3 = "gas_daily_m3_sensor"

# Electricity tariff parameters (incl. BTW)
CONF_TARIFF_NORMAAL = "tariff_normaal"         # € per kWh incl. BTW (T1/dag, of enkeltarief)
CONF_TARIFF_DAL = "tariff_dal"                 # € per kWh incl. BTW (T2/nacht)
CONF_TARIFF_RETURN = "tariff_return"           # € per kWh excl. BTW (teruglevering)
CONF_TARIFF_RETURN_COST = "tariff_return_cost" # € per kWh incl. BTW (terugleveerkosten)

# Saldering: verrekening export tegen import (uitschakelbaar voor na 2027)
CONF_USE_SALDERING = "use_saldering"
DEFAULT_USE_SALDERING = True

# Jaarafrekening startdatum (contractdatum)
CONF_SALDO_START_MONTH = "saldo_start_month"   # 1–12
CONF_SALDO_START_DAY = "saldo_start_day"       # 1–31
DEFAULT_SALDO_START_MONTH = 1
DEFAULT_SALDO_START_DAY = 1

# Fixed daily costs electricity (incl. BTW)
CONF_FIXED_DELIVERY_DAY_ELECTRICITY = "fixed_delivery_day_electricity"    # € per dag
CONF_SYSTEM_OPERATOR_DAY_ELECTRICITY = "system_operator_day_electricity"  # € per dag
CONF_ENERGY_REDUCTION_YEAR = "energy_reduction_year"                       # € per jaar (korting)

# Gas tariff parameters (incl. BTW)
CONF_GAS_TARIFF = "gas_tariff"                 # € per m³ incl. BTW

# Fixed daily costs gas (incl. BTW)
CONF_FIXED_DELIVERY_DAY_GAS = "fixed_delivery_day_gas"      # € per dag
CONF_SYSTEM_OPERATOR_DAY_GAS = "system_operator_day_gas"    # € per dag

# Defaults — voorbeeldwaarden (incl. BTW, 2026)
DEFAULT_TARIFF_NORMAAL = 0.20927         # T1/dag (of enkeltarief: zelfde waarde voor T1 en T2)
DEFAULT_TARIFF_DAL = 0.22137            # T2/nacht
DEFAULT_TARIFF_RETURN = 0.16000          # excl. BTW
DEFAULT_TARIFF_RETURN_COST = 0.15488     # incl. BTW (terugleveerkosten per kWh)

DEFAULT_FIXED_DELIVERY_DAY_ELECTRICITY = 0.30635
DEFAULT_SYSTEM_OPERATOR_DAY_ELECTRICITY = 1.30970 / 30.4375   # € per jaar -> per dag
DEFAULT_ENERGY_REDUCTION_DAY = -1.7232 / 365.2425  # korting per dag

DEFAULT_GAS_TARIFF = 1.23274
DEFAULT_FIXED_DELIVERY_DAY_GAS = 0.26922
DEFAULT_SYSTEM_OPERATOR_DAY_GAS = 0.73048 / 30.4375

# Sensor name suffixes
SENSOR_ELECTRICITY_CURRENT_COST = "electricity_current_cost"
SENSOR_ELECTRICITY_DAILY_COST = "electricity_daily_cost"
SENSOR_ELECTRICITY_MONTHLY_COST = "electricity_monthly_cost"
SENSOR_ELECTRICITY_IMPORT_DAILY = "electricity_import_daily_kwh"
SENSOR_ELECTRICITY_EXPORT_DAILY = "electricity_export_daily_kwh"
SENSOR_ELECTRICITY_NET_DAILY = "electricity_net_daily_kwh"
SENSOR_ELECTRICITY_SOLAR_DAILY = "electricity_solar_daily_kwh"
SENSOR_GAS_DAILY_COST = "gas_daily_cost"
SENSOR_GAS_MONTHLY_COST = "gas_monthly_cost"
SENSOR_TOTAL_DAILY_COST = "total_daily_cost"
SENSOR_TOTAL_MONTHLY_COST = "total_monthly_cost"
SENSOR_CURRENT_IMPORT_RATE = "current_import_rate"
SENSOR_CURRENT_EXPORT_RATE = "current_export_rate"

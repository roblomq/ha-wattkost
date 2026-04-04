# WattKost — Home Assistant HACS Integratie

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)](https://www.home-assistant.io/)

Een nauwkeurige energiekostenberekening voor Nederlandse energiecontracten, volledig configureerbaar via de UI. Ondersteunt enkel-/normaal-/daltarieven, teruglevering (saldering), zonnepanelen en gas — inclusief alle vaste leveringskosten, systeembeheerkosten en de vermindering energiebelasting.

---

## Functies

- **Actuele stroomkosten** — real-time kosten op basis van huidig importvermogen (€/uur)
- **Dagelijkse kosten** — variabele + vaste leveringskosten + systeembeheerkosten per dag
- **Maandelijkse kosten** — automatisch bijgehouden per kalendermaand
- **Teruglevering** — saldering correct verrekend: terugleververgoeding minus terugleveerkosten
- **Zonnepanelen** — productie verrekend in de netto kostencalculatie
- **Gas** — dagelijkse en maandelijkse gaskosten inclusief vaste kosten
- **Totaalkosten** — energie (stroom + gas) gecombineerd per dag en per maand
- **Volledig UI-gestuurd** — geen YAML nodig
- **Tarieven direct aanpasbaar** via *Instellingen → Integraties → Configureren*

---

## Installatie via HACS

1. Ga naar **HACS → Integraties → ⋮ → Aangepaste repositories**
2. Voeg toe: `https://github.com/roblomq/ha-wattkost`
3. Categorie: **Integratie**
4. Klik **Toevoegen**, zoek naar **WattKost** en installeer
5. Herstart Home Assistant
6. Ga naar **Instellingen → Apparaten & Diensten → Integratie toevoegen**
7. Zoek op **WattKost** en volg de wizard (4 stappen)

---

## Handmatige installatie

Kopieer de map `custom_components/nl_energy_cost` naar jouw HA config-directory:

```
/config/custom_components/nl_energy_cost/
```

Herstart Home Assistant en voeg de integratie toe via de UI.

---

## Configuratiewizard (4 stappen)

### Stap 1 — Stroom import & productie sensoren
| Veld | Sensor in jouw HA |
|------|-------------------|
| Verbruik W (totaal) | `sensor.energie_consumptie_w_totaal` |
| Verbruik kWh (totaal) | `sensor.energie_consumptie_kwh_totaal` |
| Import T1 kWh | `sensor.slimme_meter_energie_import_t1_kwh` |
| Import T2 kWh | `sensor.slimme_meter_energie_import_t2_kwh` |
| Import totaal kWh | `sensor.energie_import_kwh_totaal` |
| Import W | `sensor.slimme_meter_energie_import_w` |
| Zonnepanelen kWh | `sensor.samilpower_inverter_energie_productie_kwh_total` |
| Zonnepanelen W | `sensor.samilpower_inverter_energie_productie_w` |

### Stap 2 — Teruglevering & gas sensoren
| Veld | Sensor in jouw HA |
|------|-------------------|
| Export T1 kWh | `sensor.slimme_meter_energie_export_t1_kwh` |
| Export T2 kWh | `sensor.slimme_meter_energie_export_t2_kwh` |
| Export totaal kWh | `sensor.energie_export_kwh_totaal` |
| Export W | `sensor.slimme_meter_energie_export_w` |
| Gas m³ (cumulatief) | `sensor.gas_consumptie_dagelijks` |

### Stap 3 — Stroomtarieven (incl. BTW 21%)
Gebaseerd op het screenshot (Greenchoice, vanaf 1 jan 2026):

| Parameter | Standaardwaarde |
|-----------|----------------|
| Enkeltarief | € 0,21532 /kWh |
| Normaaltarief (T1/dag) | € 0,20927 /kWh |
| Daltarief (T2/nacht) | € 0,22137 /kWh |
| Terugleververgoeding | € 0,16000 /kWh *excl.* BTW |
| Terugleveerkosten | € 0,15488 /kWh |

### Stap 4 — Vaste kosten & gastarieven (incl. BTW)

| Parameter | Standaardwaarde |
|-----------|----------------|
| Vaste leveringskosten stroom | € 0,30635 /dag |
| Systeembeheerkosten stroom | € 1,30970 /jaar → € 0,00358 /dag |
| Vermindering energiebelasting | −€ 1,7232 /jaar → −€ 0,00472 /dag |
| Gastarief | € 1,23274 /m³ |
| Vaste leveringskosten gas | € 0,26922 /dag |
| Systeembeheerkosten gas | € 0,73048 /jaar → € 0,00200 /dag |

---

## Gegenereerde sensoren

| Sensor | Eenheid | Beschrijving |
|--------|---------|--------------|
| `sensor.stroom_actuele_kosten` | €/h | Huidig stroomverbruik in kosten per uur |
| `sensor.stroom_actueel_importtarief` | €/kWh | Huidig importtarief (incl. BTW) |
| `sensor.stroom_actueel_teruglevertarief` | €/kWh | Netto teruglevertarief (vergoeding − kosten) |
| `sensor.stroom_variabele_dagkosten` | € | Variabele kosten vandaag (import − teruglevercredit) |
| `sensor.stroom_vaste_dagkosten` | € | Vaste leveringskosten + systeembeheer vandaag |
| `sensor.stroom_totale_dagkosten` | € | Variabel + vast vandaag |
| `sensor.stroom_maandkosten` | € | Totale stroomkosten deze maand |
| `sensor.stroom_netto_dag_kwh_import_export` | kWh | Netto import vandaag |
| `sensor.gas_dagkosten` | € | Gaskosten vandaag (variabel + vast) |
| `sensor.gas_maandkosten` | € | Totale gaskosten deze maand |
| `sensor.totale_dagkosten_energie` | € | Stroom + gas vandaag |
| `sensor.totale_maandkosten_energie` | € | Stroom + gas deze maand |

---

## Kostenberekening

### Stroom dagkosten (variabel)
```
import_kosten   = kWh_import_vandaag × importtarief
teruglevercredit = kWh_export_vandaag × (terugleververgoeding_incl_btw − terugleveerkosten)
variabele_kosten = import_kosten − teruglevercredit
```

### Stroom dagkosten (vast)
```
vast = vaste_leveringskosten_dag + systeembeheer_dag + vermindering_energiebelasting_dag
```

### Gaskosten per dag
```
gas_kosten = m3_vandaag × gastarief + vaste_leveringskosten_gas_dag + systeembeheer_gas_dag
```

---

## Tarieven aanpassen

Na installatie kunt u tarieven altijd aanpassen:  
**Instellingen → Apparaten & Diensten → WattKost → Configureren**

---

## Licentie

MIT License — vrij te gebruiken en aan te passen.

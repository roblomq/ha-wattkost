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
7. Zoek op **WattKost** en volg de wizard (5 stappen)

---

## Handmatige installatie

Kopieer de map `custom_components/wattkost` naar jouw HA config-directory:

```
/config/custom_components/wattkost/
```

Herstart Home Assistant en voeg de integratie toe via de UI.

---

## Configuratiewizard (5 stappen)

Alle velden zijn optioneel — vul alleen in wat beschikbaar is in jouw situatie. De integratie werkt ook als niet alle sensoren beschikbaar zijn.

### Stap 1 — Import sensoren

| Veld | Beschrijving |
|------|--------------|
| Import T1 kWh | Cumulatieve kWh-meter voor import tijdens normaaluren (T1/dag). Komt van je slimme meter. |
| Import T2 kWh | Cumulatieve kWh-meter voor import tijdens daluren (T2/nacht). Komt van je slimme meter. |
| Import totaal kWh | Cumulatieve totale import in kWh (als je geen T1/T2 splitsing hebt). |
| Import huidig vermogen W | Actueel importvermogen in Watt. Gebruikt voor real-time kostencalculatie. |

### Stap 2 — Export / teruglevering sensoren

| Veld | Beschrijving |
|------|--------------|
| Export T1 kWh | Cumulatieve kWh-meter voor teruglevering tijdens normaaluren (T1). Komt van je slimme meter. |
| Export T2 kWh | Cumulatieve kWh-meter voor teruglevering tijdens daluren (T2). Komt van je slimme meter. |
| Export totaal kWh | Cumulatieve totale teruglevering in kWh (als je geen T1/T2 splitsing hebt). |
| Export huidig vermogen W | Actueel terugleveringsvermogen in Watt. |

### Stap 3 — Opwekking, consumptie & gas sensoren

| Veld | Beschrijving |
|------|--------------|
| Zonnepanelen productie kWh | Cumulatieve opgewekte kWh van je zonnepanelen (dag- of totaalteller van je omvormer). |
| Zonnepanelen huidig vermogen W | Actueel opgewekt vermogen in Watt van je zonnepanelen. |
| Verbruik W (totaal huidig vermogen) | Totaal huidig stroomverbruik in Watt (inclusief zonnepanelenproductie). |
| Verbruik kWh (totaal) | Cumulatieve totale stroomconsumptie in kWh. |
| Gasverbruik m³ (cumulatief) | Cumulatieve gasmeter in m³. Komt van je slimme meter. |

### Stap 4 — Stroomtarieven (incl. BTW 21%)

Voorbeeldwaarden als standaard (Nederlandse gemiddelden, incl. BTW, 2026):

| Parameter | Standaardwaarde | Beschrijving |
|-----------|----------------|--------------|
| Saldering actief | Aan | Schakel uit als saldering per 2027 wordt afgeschaft. Bij saldering wordt export verrekend tegen het importtarief (niet het lagere teruglevertarief). |
| Startdatum contractjaar | 01-01 | Ingangsdatum van je energiecontract in MM-DD formaat (bijv. 04-01 voor 1 april). Staat op je energiecontract. Wordt gebruikt voor de salderingsbalans en jaarafrekening. |
| Enkeltarief | € 0,21532 /kWh | All-in tarief als je meter geen dag/nacht onderscheid maakt |
| Normaaltarief (T1/dag) | € 0,20927 /kWh | All-in tarief tijdens normaaluren (overdag) |
| Daltarief (T2/nacht) | € 0,22137 /kWh | All-in tarief tijdens daluren (nacht/weekend) |
| Terugleververgoeding | € 0,16000 /kWh *excl.* BTW | Vergoeding die je ontvangt per kWh surplus teruggeleverde stroom (meer dan je hebt verbruikt) |
| Terugleveerkosten | € 0,15488 /kWh | Kosten die je betaalt per kWh teruggeleverde stroom |

### Stap 5 — Vaste kosten & gastarieven (incl. BTW)

| Parameter | Standaardwaarde | Beschrijving |
|-----------|----------------|--------------|
| Vaste leveringskosten stroom | € 0,30635 /dag | Vaste dagprijs voor stroomlevering, ongeacht verbruik |
| Systeembeheerkosten stroom | € 0,04303 /dag | Kosten netbeheerder per dag (transportkosten aansluiting) |
| Vermindering energiebelasting | −€ 1,7232 /dag | Vaste dagkorting op energiebelasting (negatief bedrag) |
| Gastarief | € 1,23274 /m³ | All-in tarief per m³ gas |
| Vaste leveringskosten gas | € 0,26922 /dag | Vaste dagprijs voor gaslevering, ongeacht verbruik |
| Systeembeheerkosten gas | € 0,02400 /dag | Kosten gasnetbeheerder per dag |

---

## Gegenereerde sensoren

### Actuele & dagwaarden
| Sensor | Eenheid | Beschrijving |
|--------|---------|--------------|
| `sensor.stroom_actuele_kosten` | €/h | Huidig stroomverbruik in kosten per uur |
| `sensor.stroom_actueel_importtarief` | €/kWh | Huidig importtarief (incl. BTW) |
| `sensor.stroom_actueel_teruglevertarief` | €/kWh | Netto teruglevertarief (vergoeding − kosten) |
| `sensor.stroom_variabele_dagkosten` | € | Variabele kosten vandaag (met saldering verrekend) |
| `sensor.stroom_vaste_dagkosten` | € | Vaste leveringskosten + systeembeheer + reductie vandaag |
| `sensor.stroom_totale_dagkosten` | € | Variabel + vast vandaag |
| `sensor.stroom_maandkosten` | € | Totale stroomkosten deze maand |
| `sensor.stroom_netto_dag_kwh_import_export` | kWh | Netto import vandaag (import − export) |
| `sensor.gas_dagkosten` | € | Gaskosten vandaag (variabel + vast) |
| `sensor.gas_maandkosten` | € | Totale gaskosten deze maand |
| `sensor.totale_dagkosten_energie` | € | Stroom + gas vandaag |
| `sensor.totale_maandkosten_energie` | € | Stroom + gas deze maand |

### Salderingsbalans (contractjaar)
| Sensor | Eenheid | Beschrijving |
|--------|---------|--------------|
| `sensor.saldo_import_dit_jaar` | kWh | Totaal geïmporteerde kWh dit contractjaar (vanaf startdatum contract) |
| `sensor.saldo_export_dit_jaar` | kWh | Totaal teruggeleverde kWh dit contractjaar |
| `sensor.saldo_netto_dit_jaar` | kWh | Netto saldo (import − export). Negatief = netto terugleveraar |
| `sensor.geschatte_jaarafrekening_stroom` | € | Wat de stroomafrekening zou zijn als het contractjaar nu eindigt (incl. vaste kosten en saldering) |

> **Technische noot:** De startwaarden van de meters op de contractstartdatum worden opgehaald uit de HA recorder (historische data). Als er geen historische data beschikbaar is (bijv. bij een nieuwe installatie), worden de huidige meterwaarden als startpunt gebruikt. De startwaarden worden lokaal opgeslagen zodat ze HA-herstarts overleven. Alle sensoren worden elke 5 minuten bijgewerkt om de databasegroei te beperken.

---

## Kostenberekening

### Stroom dagkosten (variabel)
```
import_kosten    = kWh_import_vandaag × importtarief
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

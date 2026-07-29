# Fontainebleau etter brannen — statuskart

Interaktivt kart over hvilke buldresektorer i Fontainebleau som ble rammet av
skogbrannen i juli 2026, og hvilke som bare er stengt.

**Hovedfunnet:** brannen tok 923 hektar. Ferdselsforbudet stengte 23 613 hektar.
Bare 3,9 prosent av det stengte arealet har faktisk brent.

## Slik publiserer du siden

Alt ligger i `index.html`. Ingen byggesteg, ingen avhengigheter å installere.

1. Legg filen i et offentlig repo
2. Settings → Pages → Source: **Deploy from a branch**, `main` og `/ (root)`
3. Siden dukker opp på `https://brukernavn.github.io/reponavn/`

## Slik oppdateres innholdet

All data ligger i én blokk øverst i `<script>`, merket `/* === DATA === */`.

| Konstant | Innhold |
|---|---|
| `META` | Dato, versjon og tallene i faktastripa |
| `CAT` | Statuskategoriene med farge og forklaring |
| `SECTORS` | 90 sektorer med koordinater, andel brent og avstand til brannflate |
| `BURN_RINGS` | Brannflaten, 76 polygoner |
| `FORESTS` | De tre stengte statsskogene |
| `PLACES` | Stedsnavnene i kartlaget «Steder», avslått som standard |
| `BOOLDER` | Sektornavn → Boolder-slug, brukt til lenka i infoboksen |
| `SOURCES` | Kildelista nederst på siden |

Boolder-slugene følger ingen fast regel — `Rocher d'Avon` blir `rocher-avon`,
`Buthiers Piscine` blir `buthiers`, `Cuvier Petit Rempart` blir `petit-rempart`.
De er sjekket mot boolder.com én for én. Hvis Boolder gir en sektor nytt navn,
må slugen kontrolleres manuelt; adressen blir
`https://www.boolder.com/en/fontainebleau/<slug>`.

Når ONF gjenåpner en sektor, endres feltet `s` for den sektoren til `open`.

### Hva som må oppdateres over tid

Det meste av siden er varige fakta om brannen og trenger aldri endres.
Bare disse feltene er ferskvare:

| Felt | Hva det styrer |
|---|---|
| `META.updated` | Datoen i toppstripa |
| `META.n_open` | Tallet i faktakortet «Åpne sektorer» |
| `META.access_date` | Datoen samme kort viser |
| `META.ban_until` | Datoen ferdselsforbudet gjelder til, vist i samme kort |
| `SECTORS[].s` | Statusen på hver sektor — sett `open` ved gjenåpning |

Overskrift, ingress, forholdsbånd og de tre første faktakortene handler om
brannens utstrekning. De står seg uansett hva som åpner igjen.

## Datakilder

| Lag | Kilde | Lisens |
|---|---|---|
| Brannflate | [Copernicus EMS EMSR894](https://mapping.emergency.copernicus.eu/activations/EMSR894/), produkt Grading Monit01, satellittbilde 19.07.2026 | © European Union |
| Skoggrenser | [ONF OpenData](https://geo-onf.opendata.arcgis.com/), offentlige skoger i fastlands-Frankrike | Åpne data |
| Sektorer | [Boolder](https://github.com/boolder-org/boolder-data) | CC BY 4.0 |
| Åpen/stengt | [CrashPad Tours](https://crashpadtours.fr/fontainebleau-incendie-secteurs-ouverts/) | — |
| Bakgrunnskart | OpenStreetMap, CARTO, Esri | Se attribusjon i kartet |

## Lisens

Koden i `index.html` er MIT-lisensiert, se [LICENSE](LICENSE). Dataene siden
bygger på har sine egne vilkår — Boolders sektordata er CC BY 4.0, brannflaten
er © European Union / Copernicus EMS. Vilkårene står i lisensfilen og i
kildetabellen over.

## Metode

Sektorenes yttergrenser fra Boolder er lagt over Copernicus-brannflaten, og
andelen overlapp er regnet ut i projeksjonen Lambert-93 (EPSG:2154).
Geometrien er forenklet for visning, med under 0,3 prosent arealavvik.

Svakhet å kjenne til: andelen brent er regnet mot sektorens rektangulære
yttergrense, ikke mot hver enkelt blokk. En sektor med lav prosent kan likevel
ha brent kraftig i ett hjørne.

## Forbehold

Dette er ingen offisiell kilde. Det som avgjør om du har lov å gå inn, er
ferdselsforbudet fra statsforvalteren i Seine-et-Marne og oppslag på stedet.
Sjekk [bleau.info](https://bleau.info) og
[prefekturen](https://www.seine-et-marne.gouv.fr/Actualites/Incendies-points-de-situation)
før avreise.

---

## In English

Interactive map of the July 2026 Fontainebleau wildfire and its effect on
bouldering access. The official Copernicus EMS burn perimeter is overlaid on
Boolder's area boundaries to show how much of each sector actually burned.

923 hectares burned. 23 613 hectares remain closed. Only 3.9 % of the closed
area was affected — the closure is about hazardous trees and smouldering peat,
not destroyed forest.

Page text is in Norwegian. Not an official source: always check the prefectural
decree and bleau.info before you travel.

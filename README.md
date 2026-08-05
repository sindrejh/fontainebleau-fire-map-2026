# Fontainebleau etter brannen — statuskart

Interaktivt kart over hvilke buldresektorer i Fontainebleau som ble rammet av
skogbrannen i juli 2026, og hvilke som bare er stengt.

**Hovedfunnet:** brannen tok 926 hektar. Ferdselsforbudet stengte 23 613 hektar.
Bare 3,9 prosent av det stengte arealet har faktisk brent. Av de 19 137
blokkproblemene i Bleau ligger 2 104 — 11 prosent — innenfor brannflaten.

## Slik publiserer du siden

Ingen byggesteg og ingen avhengigheter å installere. Siden er `index.html` pluss
mappa `vendor/`, som inneholder Leaflet og skriftene.

1. Legg filene i et offentlig repo
2. Settings → Pages → Source: **Deploy from a branch**, `main` og `/ (root)`
3. Siden dukker opp på `https://brukernavn.github.io/reponavn/`

Alt utenom kartflisene lastes fra samme domene som siden selv. Blokkeres et CDN,
eller er nettet borte, står siden likevel — bare bakgrunnskartet faller bort, og
det bytter selv til neste leverandør i lista.

## Slik oppdateres innholdet

All data ligger i én blokk øverst i `<script>`, merket `/* === DATA === */`.

| Konstant | Innhold |
|---|---|
| `META` | Dato, versjon og alle tallene siden viser |
| `CAT` | Statuskategoriene med farge og forklaring |
| `SECTORS` | 90 sektorer med koordinater, andel brent og avstand til brannflate |
| `SECTORS[].dep` | Departementet sektoren ligger i, `77` eller `91` |
| `SECTORS[].annenskog` | Skog forbudet omfatter, men kartet ikke tegner |
| `HISTORIKK` | Endringsloggen, med norsk og engelsk tekst per oppføring |
| `PTS` | Posisjonen til hver av de 19 137 blokkene, delta-kodet |
| `BURN_RINGS` | Brannflaten, 76 polygoner |
| `FORESTS` | De tre stengte statsskogene |
| `PLACES` | Stedsnavnene i kartlaget «Steder», avslått som standard |
| `BOOLDER` | Sektornavn → Boolder-slug, brukt til lenka i infoboksen |
| `SOURCES` | Kildelista nederst på siden |

**Ingen tall står i prosaen.** Alt fra ingressen til bunnteksten bygges av
`META` når siden lastes. Tidligere sto hovedtallet tre steder med tre ulike
verdier — 921, 923 og 926 hektar samtidig — og det er grunnen til at det nå bare
finnes ett sted.

Boolder-slugene følger ingen fast regel — `Rocher d'Avon` blir `rocher-avon`,
`Buthiers Piscine` blir `buthiers`, `Cuvier Petit Rempart` blir `petit-rempart`.
De er sjekket mot boolder.com én for én. Hvis Boolder gir en sektor nytt navn,
må slugen kontrolleres manuelt; adressen blir
`https://www.boolder.com/en/fontainebleau/<slug>`.

### Hva som må oppdateres over tid

Det meste av siden er varige fakta om brannen og trenger aldri endres.
Bare disse feltene er ferskvare:

| Felt | Hva det styrer |
|---|---|
| `META.updated` | Datoen i toppstripa |
| `META.access_date` | Datoen faktakortet «Åpne sektorer» viser |
| `META.ban_until` | Datoen ferdselsforbudet gjelder til, vist i samme kort |
| `META.ess_until` | Datoen Essonnes siste forbud gjaldt til, vist på de sektorene |
| `SECTORS[].s` | Statusen på hver sektor — sett `open` ved gjenåpning |
| | `uavklart` når sektoren er ført som stengt uten at hjemmelen finnes |

Datoene skrives som `ÅÅÅÅ-MM-DD`. Sida formaterer dem selv, på norsk eller
engelsk. Går datoen i `ban_until` ut, sier sida fra av seg selv med en varselrute
i stedet for å vise en utløpt dato som om den fortsatt gjaldt.

`META.n_open` og de andre opptellingene regnes ut av `tools/beregn.py` og skal
ikke redigeres for hånd. Når ONF gjenåpner en sektor, endres `s` til `open` og
skriptet kjøres på nytt.

### To forbud, ikke ett

Sektorene ligger i to departementer, og de har hver sin ordning. Forskjellen er
grunnen til at `ess` finnes.

**Seine-et-Marne** stenger navngitte skoger — Fontainebleau, Trois Pignons, la
Commanderie, Nanteau-Poligny og kommuneskogen i Nemours — og vedtakene står i
ukevis. Det er dette `ban_until` følger.

**Essonne** stenger *alle* skoger i departementet over 0,5 hektar, private som
offentlige, pluss 200 meter rundt dem. Vedtakene varer to–tre døgn og kommer
tilbake hver gang brannfaren stiger; det skjedde to ganger i juli. Åtte sektorer
ligger der, og statusen deres kan bli utdatert i løpet av dagen. De har `dep`
lik `91` og bærer en egen merknad i infoboksen.

`dep` er målt, ikke antatt: hver blokk er testet mot IGNs departementsgrenser med
samme kryssingstest som resten. Alle 90 sektorene faller entydig i ett departement
— 82 i Seine-et-Marne, 8 i Essonne — og ingen ligger på grensa. Skal feltet
regnes om, hentes grensene fra
[france-geojson](https://github.com/gregoiredavid/france-geojson) og måles med
`tools/forbudssone.py`.

Hvilke sektorer et forbud faktisk treffer, avgjøres ikke av områdenavnet hos
Boolder. Det er en klatreinndeling, ikke en eiendomsgrense. Da arrêté 1266 stengte
kommuneskogen i Nemours, lå bare én av de fem sektorene i Boolder-området
«Nemours» innenfor grensa. Bruk `tools/forbudssone.py` i stedet for å gjette.

## Regne ut på nytt

`tools/beregn.py` er det som produserer blokktallene. Det leser brannflaten fra
`index.html` og blokkposisjonene fra Boolders database, teller hvor mange blokker
som ligger innenfor flaten, og skriver resultatet tilbake i datablokka.

```sh
git clone --depth 1 https://github.com/boolder-org/boolder-data.git
pip install numpy
python3 tools/beregn.py boolder-data/boolder.db
```

Skriptet er idempotent — det gir samme resultat uansett hvor mange ganger det
kjøres. Adgangsstatusen (`open`, `stengt_annet`) rører det ikke; den er en
menneskelig avgjørelse, ikke noe som følger av brannflaten.

## Måle mot en eiendomsgrense

`tools/forbudssone.py` svarer på hvilke sektorer et forbud treffer, når forbudet
gjelder en skog kartet ikke tegner. Den teller blokkproblemene innenfor en
GeoJSON-grense, med samme projeksjon og kryssingstest som `beregn.py`.

```sh
python3 tools/forbudssone.py --selvtest          # mål mot brannflaten, der fasiten er kjent
python3 tools/forbudssone.py nemours.geojson     # mål mot en ny grense
```

Grensene hentes fra [ONF OpenData](https://geo-onf.opendata.arcgis.com/) som
GeoJSON. Selvtesten måler mot brannflaten og skal reprodusere `bb` per sektor;
ryker den, er tallene mot en ny skoggrense ikke verdt å stole på.

Skriptet skriver ingenting. Det rapporterer, og så avgjør et menneske — en sektor
kan ligge i skogen uten å være omfattet, eller være stengt av en grunn ingen
polygon kjenner til.

## Kartet i fullskjerm

Knappen over kartet lar kartet fylle skjermen. Der nettleseren tillater det,
brukes fullskjerm-API-et; ellers legger sida seg over vinduet med CSS, slik at
iOS Safari — som bare gir fullskjerm til video — oppfører seg likt. Escape
avslutter i begge tilfeller.

Detaljene om en sektor står i panelet under kartet, og det panelet er utenfor
synsfeltet så snart kartet fyller skjermen. I fullskjerm flyttes derfor det
samme elementet opp som en infoboks oppå kartet — én tekst og én kodevei, ikke
en kopi. Boksen står til venstre på brede skjermer og nederst på smale, og et
sektorvalg rammes inn i den delen av kartet boksen ikke dekker. Er ingen sektor
valgt, eller lukker leseren boksen, ligger den ikke i veien.

Tegnforklaringa har samme problem og samme løsning: knappen ved siden av
fullskjermknappen henter opp de to bolkene som ellers står under kartet —
«Flatene i kartet» og «Status» — og de samme elementene flyttes tilbake dit når
fullskjerm avsluttes. Ruta er mørk som sida ellers, fordi fargene i
tegnforklaringa er skrevet for den bakgrunnen.

De to rutene deler plass, og bare én står framme om gangen. På telefon er det
ikke rom for to, og på skjerm ville de dekket hver sin del av kartet. Et
sektorvalg lukker tegnforklaringa, Escape lukker den ruta som står framme før
den avslutter fullskjerm.

Zoomknappene flytter til høyre side i fullskjerm. Ellers ville de blitt liggende
under rutene.

Toppstripa skal være én linje. Hver ekstra linje er kart man gikk i fullskjerm
for å se, og på norsk ble det tre av dem. Derfor står navnet på bakgrunnskartet
bare i nedtrekkslista: prikken ved siden av sier hvordan det går med det, og
skriver bare tekst når den har noe å si ut over navnet — at sida prøver en
leverandør, eller at den ikke svarer. Skjermlesere får teksten uansett, for en
farge alene sier dem ingenting. På smale skjermer faller etiketten foran lista
bort, og knappene blir ikoner med navnet i `aria-label` og `title`. Det skjer
under 480 piksler i vanlig visning, og under 700 i fullskjerm, der stripa har en
knapp til å få plass til. Fullskjermknappen har ett ikon som peker ut når man
står utenfor, og inn når man er inne.

## Sektorlista

Områdene (Boolders klynger) står sammenslåtte. 90 rader etter hverandre er mer
enn noen leser; 19 områdeoverskrifter kan man skumme. Overskrifta bærer
sammendraget — antall sektorer, hvor mange av områdets blokker som ligger i
brannflaten, og for uberørte områder avstanden til nærmeste brannflate — og et
trykk på den åpner området.

Områdene sorteres som lista ellers, mest brent først. Alfabetisk ville Trois
Pignons, det eneste området brannen traff for alvor, havnet nest nederst.

Velger man en sektor i kartet, åpner området sitt av seg selv, ellers ville
raden vært markert uten å være synlig. Søk og alle andre sorteringer viser lista
flat, uten områdeoverskrifter.

Statusforklaringa står i høyre spalte på brede skjermer, men er sitt eget
element i rutenettet — ikke en del av spalta. Når spaltene stables på smale
skjermer, flytter den seg opp foran lista, rett under filterknappene, som bærer
de samme fargene. Ellers ville forklaringa på fargene ligget etter alle 90
radene. Plasseringa i rutenettet er derfor eksplisitt: lista spenner over begge
radene, og et nytt element uten plassering havner et tilfeldig sted.

## Endringslogg

`HISTORIKK` er tidslinja sida viser i høyre spalte, nyeste først. Hver oppføring
peker på en kilde i `SOURCES` og skal bare si det kilden faktisk viser. Vi vet
for eksempel ikke når den enkelte sektoren ble gjenåpnet, bare hva listene viste
på gitte datoer — og det er det oppføringen sier.

Oppføringer som er kommet til siden forrige besøk, merkes «Nytt». Sida husker
den nyeste datoen leseren har sett, i `localStorage`.

Statusendringer føres opp av `tools/logg.py`:

```sh
python3 tools/logg.py            # vis hva som har endret seg
python3 tools/logg.py --skriv    # legg oppføringen inn i HISTORIKK
```

Skriptet sammenlikner statusene i `index.html` med forrige øyeblikksbilde i
`tools/statuslogg.json`, skriver en oppføring på begge språk om hvilke sektorer
som skiftet, og setter `META.updated` og `META.access_date`. Arbeidsgangen når
ONF åpner en sektor er: sett `s` til `open`, kjør `beregn.py`, kjør `logg.py
--skriv`.

## Språk

Sida finnes på norsk og engelsk i samme fil. Datablokka er stor, så to
HTML-filer ville doblet vekta og latt oversettelsene gli fra hverandre — i
stedet ligger all tekst i `tekster()` i `<script>`, og `CAT`, `SOURCES` og
`HISTORIKK` bærer felter med `_en`-endelse.

Språket velges i denne rekkefølgen: `?lang=nb` eller `?lang=en` i adressa, så
et tidligere valg fra `localStorage`, så nettleserens språk. Nordiske lesere får
norsk, alle andre engelsk — ellers står de igjen med en side de ikke kan lese.
Knappen i toppstripa bytter, og valget følger med i adressa.

Tall og datoer formateres etter språket: `19 137` og `3,9 %` på norsk,
`19,137` og `3.9%` på engelsk.

## Røyktest

```sh
python3 -m http.server 8931 &
npm i playwright
node tools/royktest.mjs
```

Testen sperrer alt nettverk utenfor localhost, så den slår også fast at siden
virker uten CDN. Den kjører hele suiten på begge språk, og sjekker blant annet
at nettleseren teller nøyaktig like mange brente blokker som `tools/beregn.py`
gjorde, at språkbyttet tar med seg kartlagene og den valgte sektoren, og at
varselet om utløpt ferdselsforbud dukker opp når datoen er passert.

## Datakilder

| Lag | Kilde | Lisens |
|---|---|---|
| Brannflate | [Copernicus EMS EMSR894](https://mapping.emergency.copernicus.eu/activations/EMSR894/), produkt Grading Monit01, satellittbilde 19.07.2026 | © European Union |
| Skoggrenser | [ONF OpenData](https://geo-onf.opendata.arcgis.com/), offentlige skoger i fastlands-Frankrike | Åpne data |
| Sektorer og blokker | [Boolder](https://github.com/boolder-org/boolder-data) | CC BY 4.0 |
| Åpen/stengt | [CrashPad Tours](https://crashpadtours.fr/fontainebleau-incendie-secteurs-ouverts/) | — |
| Ferdselsforbud, Seine-et-Marne | Arrêtés 2026/CAB/SIDPC/1265 og 1266 av 29.07.2026 | Offentlig vedtak |
| Ferdselsforbud, Essonne | Arrêtés 2026-DDT-SEAF av 07.07.2026 og 2026-PREF-DCSIPC-SIDPC-1244 av 27.07.2026 | Offentlig vedtak |
| Bakgrunnskart | OpenStreetMap, CARTO, Esri | Se attribusjon i kartet |

## Lisens

Koden i `index.html` er MIT-lisensiert, se [LICENSE](LICENSE). Dataene siden
bygger på har sine egne vilkår — Boolders sektor- og blokkdata er CC BY 4.0,
brannflaten er © European Union / Copernicus EMS. Leaflet og skriftene under
`vendor/` har egne lisensfiler. Vilkårene står i lisensfilen og i
kildetabellen over.

## Metode

Hver av de 19 137 blokkene i Boolders datasett testes mot Copernicus-brannflaten
med en kryssingstest. 2 104 av dem ligger innenfor. Det er dette tallet siden
oppgir per sektor.

Tidligere regnet siden andelen brent mot sektorens rektangulære yttergrense.
Det målet var upresist begge veier: Diplodocus ble oppgitt til 31,2 prosent
brent, men alle de 159 blokkproblemene i sektoren ligger inne i brannflaten,
mens Rocher Fin hadde 6 prosent av rektangelet innenfor uten at én eneste av de
253 blokkene er berørt. Det gamle tallet er beholdt i feltet `flate` og vises
som sammenlikning i infoboksen.

Koordinatene rundes til hundretusendels grad — omtrent en meter — *før* de måles
mot brannflaten. Det er de samme koordinatene siden publiserer og tegner, så
tallet, prikken i kartet og en eventuell etterregning stemmer overens.

### Svakheter å kjenne til

* Brannflaten er forenklet for visning. De forenklede polygonene dekker 975
  hektar mot Copernicus' 926 — omtrent 5 prosent for mye. Tellingen er derfor i
  overkant raus helt inntil brannkanten.
* Blokkoordinatene fra Boolder er GPS-satte og treffer på noen meter.
* En blokk utenfor flaten kan være svidd likevel, og en blokk innenfor kan stå
  uskadd. Flaten sier hvor det brant, ikke hva som skjedde med hver enkelt stein.
* 50 av de 90 sektorene ligger utenfor området Copernicus gjennomgikk. Alle
  ligger minst 2,22 km fra nærmeste kartlagte brannflate og er derfor ikke
  berørt av denne brannen.
* ONF og pressen oppgir rundt 2 000 hektar, «omtrent 10 prosent av massivet».
  Copernicus kartlegger 926. En del av forskjellen er at de offisielle tallene
  måler arealet innenfor brannens ytre omkrets og ikke bare det som virkelig
  brant, men to andre forhold trekker samme vei: analyseområdet dekker bare
  10 290 hektar, og satellittbildet flaten er tegnet fra er tatt 19. juli, mens
  statsforvalteren daterer brannene til 12.–24. juli og melder om oppblussinger
  helt til 30. Aktiveringen EMSR894 er avsluttet uten noe produkt etter Grading
  Monit01, så flaten står. Merk hva det betyr: den står fordi kartleggingen tok
  slutt, ikke fordi noen har målt at det ikke brant mer. Hvor mye de siste
  dagene la til, vet vi ikke.

## Forbehold

Dette er ingen offisiell kilde. Det som avgjør om du har lov å gå inn, er
ferdselsforbudet fra statsforvalteren i Seine-et-Marne og oppslag på stedet.
Sjekk [bleau.info](https://bleau.info) og
[prefekturen](https://www.seine-et-marne.gouv.fr/Actualites/Incendies-points-de-situation)
før avreise.

---

## In English

Interactive map of the July 2026 Fontainebleau wildfire and its effect on
bouldering access. The official Copernicus EMS burn perimeter is tested against
every single boulder problem in Boolder's dataset, rather than against a
bounding box per sector.

926 hectares burned, in 76 separate patches. 23 613 hectares remain closed, and
only 3.9 % of that closed area was affected — the closure is about hazardous
trees and smouldering peat, not destroyed forest. Of the 19 137 boulder problems
in Bleau, 2 104 (11 %) fall inside the burn perimeter, across 15 sectors; five
sectors have every one of their boulders inside it.

The page is available in both Norwegian and English — use the language button in
the top bar, or add `?lang=en` to the address. It defaults to English unless your
browser is set to a Scandinavian language.

Not an official source: always check the prefectural decree and bleau.info
before you travel.

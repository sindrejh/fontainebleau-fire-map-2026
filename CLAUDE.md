# Arbeidsregler for dette repoet

Statuskart over skogbrannen i Fontainebleau, juli 2026. Én selvstendig
`index.html` med data, tekst og logikk, pluss `vendor/` og `tools/`.

`README.md` forklarer hva sida er, hvor dataene kommer fra og hvordan de
oppdateres. **Les den først.** Denne fila gjentar ikke README — den lister bare
det som ikke er synlig fra koden, og som gjør skade hvis det brytes.

Ingen tall fra datasettet skal stå her. Står de to steder, spriker de før eller
siden, og det er nøyaktig feilen dette prosjektet er bygget for å unngå.

## Regler som ikke kan brytes

**Rediger aldri datablokka for hånd.** Alt mellom `/* === DATA === */` og
`/* === END DATA === */` som gjelder `SECTORS`, `PTS` og de avledede feltene i
`META`, skrives av `tools/beregn.py`. Håndredigering blir overskrevet ved neste
kjøring.

**`SECTORS[].flate` skal aldri regnes ut på nytt.** Det er det gamle
rektangelmålet fra overlappsanalysen i Lambert-93, og det finnes ikke noe sted
å hente det fra igjen. `beregn.py` setter det bare hvis det mangler. Skriver du
det over med `brent`, er sammenlikningsgrunnlaget tapt for godt.

**Kvantiser før du måler.** Koordinatene rundes til hundretusendels grad før de
testes mot brannflaten, fordi det er de samme koordinatene sida publiserer og
tegner. Måler du fullpresise koordinater og publiserer avrundede, havner blokker
inntil brannkanten på hver sin side av grensa i tallet og i kartet.

**Adgangsstatus er en menneskelig avgjørelse.** `open`, `stengt_annet` og
`uavklart` følger av oppslag og vedtak, ikke av brannflaten. `beregn.py` rører
dem ikke, og skal fortsette å la være — de står i `ADGANG`, og en status som
ikke står der, blir overskrevet ved neste kjøring.

**`uavklart` betyr at vi ikke finner hjemmelen.** Den er ikke en mildere
«stengt», og den skal ikke settes fordi noe er uoversiktlig. Den sier at
sektoren er ført som stengt, at vedtaket som stengte den er utløpt, og at vi
ikke har funnet noe nytt. Finner du hjemmelen, er statusen ikke lenger uavklart.

**Ingen tall i prosaen.** All tekst bygges av `META` i `tekster()`. Hovedtallet
sto en gang tre steder med tre ulike verdier samtidig. Skal du skrive et tall i
en setning, hent det fra `META` — og mangler feltet, legg det til i `beregn.py`.

**Alt som vises, må finnes på begge språk.** Ny UI-tekst i begge grenene av
`tekster()`; nye data-strenger med `_en`-felt ved siden av. Tall og datoer
formateres av `tall()`, `pc()` og `dato()` — ikke skriv dem ut direkte.

**Oppføringer i `HISTORIKK` skal kunne føres tilbake til en kilde.** Feltet
`kilde` peker på `SOURCES`. Vi vet ikke når den enkelte sektoren ble gjenåpnet,
bare hva listene viste på gitte datoer. Ikke utled, ikke anta, ikke rund av til
noe som høres bedre ut.

**Ingenting skal lastes fra CDN.** Leaflet og skriftene ligger i `vendor/`
nettopp fordi et blokkert CDN tok med seg hele kartet. Røyktesten sperrer alt
nettverk utenfor localhost for å holde på det.

## Arbeidsgang

```sh
# regne blokktallene på nytt (krever numpy + en klone av boolder-data)
python3 tools/beregn.py boolder-data/boolder.db

# føre opp at sektorer har åpnet eller stengt
python3 tools/logg.py --skriv

# røyktest — kjør denne før du committer
python3 -m http.server 8931 &
node tools/royktest.mjs
```

`beregn.py` er idempotent og skal forbli det. Kjør den to ganger og se at
diffen er tom før du committer endringer i den.

Testen kjører hele suiten på begge språk. Den sjekker blant annet at
nettleseren teller nøyaktig like mange brente blokker som `beregn.py` gjorde —
den invarianten er hele grunnlaget for tallet sida oppgir. Ryker den, er det
ikke testen som er feil.

## Feller som har tatt oss før

* `display:flex` på et element med `hidden` slår nettleserens egen regel.
  Skjulte elementer trenger `[hidden]{display:none}` eksplisitt.
* Sektorprikkene ligger tettere enn en fingertupp på telefon. `selectNear`
  velger nærmeste, og de usynlige trykkflatene må følge filtreringen — ellers
  kaprer en bortfiltrert sektor trykk ment for brannflaten under.
* Myk rulling som regel for hele sida flytter radene mellom to trykk. Den er
  med vilje begrenset til menyklikk.
* Rader i sammenslåtte områder ligger fortsatt i DOM-en. Velger du en sektor,
  må området åpnes, ellers markeres en rad ingen ser.

## Språk og tone

Repoet er norsk: kommentarer, commit-meldinger, dokumentasjon og variabelnavn.
Kommentarer forklarer *hvorfor*, ikke *hva* — se de eksisterende. Sida er
uoffisiell, og teksten skal ikke gi inntrykk av noe annet.

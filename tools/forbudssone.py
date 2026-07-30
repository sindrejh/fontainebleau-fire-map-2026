#!/usr/bin/env python3
"""Teller hvor mange blokkproblemer i hver sektor som ligger innenfor en
eiendomsgrense, og rapporterer hvilke sektorer et ferdselsforbud faktisk
treffer.

    python3 tools/forbudssone.py --selvtest
    python3 tools/forbudssone.py nemours.geojson nanteau-poligny.geojson

Arretene 2026/CAB/SIDPC/1265 og 1266 av 29.07.2026 stengte skoger sida ikke
tegner -- kommuneskogen i Nemours og foret domaniale de Nanteau-Poligny. Uten
grensene deres er det bare gjetning hvilke sektorer som ligger inne i dem, og
adgangsstatus skal ikke gjettes. Hent grensene fra ONF OpenData
(https://geo-onf.opendata.arcgis.com/) som GeoJSON og mal dem her.

Skriptet skriver ingenting. Det rapporterer, og sa avgjor et menneske. Det er
med vilje: adgangsstatus folger av vedtak og oppslag, ikke av geometri --
en sektor kan ligge i skogen uten a vaere omfattet, eller vaere stengt av en
grunn ingen polygon kjenner til.

Kilder: blokkdata Boolder (CC BY 4.0), skoggrenser ONF OpenData.
"""
import json
import re
import sys
from pathlib import Path

try:
    import numpy as np
except ImportError:
    sys.exit("krever numpy:  pip install numpy")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beregn import MLAT, MLON, les, punkt_i_flate  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "index.html"


def punkt_i_polygon(px, py, polygoner):
    """Som punkt_i_flate, men for polygoner som kan ha hull.

    Brannflaten har ingen hull, sa beregn.py kan noye seg med a se hver ring
    for seg. Eiendomsgrenser har det: en kommuneskog kan ha et jorde eller en
    tomt skaret ut midt i. Innenfor ett polygon avgjor derfor et oddetall
    ringer -- ytterringen teller inn, hullet teller ut igjen -- mens flere
    polygoner ellers legges sammen.
    """
    inne = np.zeros(len(px), dtype=bool)
    for ringer in polygoner:
        odde = np.zeros(len(px), dtype=bool)
        for r in ringer:
            odde ^= punkt_i_flate(px, py, [r])
        inne |= odde
    return inne


def polygoner_fra_geojson(sti):
    """Plukker ut alle polygonene i en GeoJSON-fil, som lister av ringer.

    ONF leverer [lengde, bredde]; resten av repoet regner i [bredde, lengde],
    sa de snus her og ikke lenger ut."""
    data = json.loads(Path(sti).read_text(encoding="utf8"))
    feats = data.get("features", [data]) if isinstance(data, dict) else data
    ut = []
    for f in feats:
        g = f.get("geometry", f) or {}
        t, koord = g.get("type"), g.get("coordinates", [])
        if t == "Polygon":
            biter = [koord]
        elif t == "MultiPolygon":
            biter = koord
        else:
            continue
        for p in biter:
            ut.append([[(pt[1], pt[0]) for pt in ring] for ring in p])
    if not ut:
        sys.exit("fant ingen polygoner i %s" % sti)
    return ut


def blokker_per_sektor(src):
    """Dekoder PTS tilbake til koordinater.

    PTS er allerede kvantisert av beregn.py, sa det som males her er noyaktig
    de koordinatene sida publiserer og tegner. Runder man av etterpa i stedet,
    havner blokker inntil grensa pa hver sin side i tallet og i kartet."""
    ut = {}
    for navn, (la0, lo0, arr) in les("PTS", src, ";\n/* Boolder-URL").items():
        pts, a, o = [], 0, 0
        for i in range(0, len(arr), 2):
            a += arr[i]
            o += arr[i + 1]
            pts.append((la0 + a / 1e5, lo0 + o / 1e5))
        ut[navn] = pts
    return ut


def tell(blokker, SECTORS, polygoner):
    """Antall blokkproblemer per sektor innenfor polygonene."""
    flat = [(s["n"], la, lo) for s in SECTORS for la, lo in blokker[s["n"]]]
    px = np.array([r[2] for r in flat]) * MLON
    py = np.array([r[1] for r in flat]) * MLAT
    inne = punkt_i_polygon(px, py, polygoner)
    per = {s["n"]: 0 for s in SECTORS}
    for (navn, _, _), i in zip(flat, inne):
        per[navn] += int(i)
    return per


def selvtest(src, SECTORS, blokker):
    """Maler mot brannflaten, der fasiten allerede star i datablokka.

    Reproduserer tellingen bb per sektor, sa vet vi at dekodingen av PTS,
    projeksjonen og punkt-i-polygon-testen her gir samme svar som beregn.py --
    og da er tallene mot en ny skoggrense verdt a stole pa."""
    ringer = les("BURN_RINGS", src)
    per = tell(blokker, SECTORS, [[r] for r in ringer])
    feil = [(s["n"], s["bb"], per[s["n"]]) for s in SECTORS if per[s["n"]] != s["bb"]]
    for n, ventet, fikk in feil:
        print("  %-26s ventet %d, fikk %d" % (n, ventet, fikk))
    sum_n = sum(len(blokker[s["n"]]) for s in SECTORS)
    META = les("META", src)
    if sum_n != META["blokk_total"]:
        print("  totalt antall blokker: ventet %d, fikk %d" % (META["blokk_total"], sum_n))
        feil.append(("total", META["blokk_total"], sum_n))
    if feil:
        sys.exit("selvtesten ryker -- ikke stol pa tallene mot skoggrensene")
    print("selvtest OK: %d av %d blokkproblemer i brannflaten, likt med beregn.py"
          % (sum(per.values()), sum_n))


def main():
    src = HTML.read_text(encoding="utf8")
    SECTORS = les("SECTORS", src)
    blokker = blokker_per_sektor(src)

    filer = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--selvtest" in sys.argv or not filer:
        selvtest(src, SECTORS, blokker)
        if not filer:
            print("\nbruk: python3 tools/forbudssone.py <grense.geojson> ...")
            print("hent grensene fra https://geo-onf.opendata.arcgis.com/")
            return

    polygoner = []
    for f in filer:
        p = polygoner_fra_geojson(f)
        print("%s: %d polygon(er)" % (f, len(p)))
        polygoner += p

    per = tell(blokker, SECTORS, polygoner)
    truffet = [s for s in SECTORS if per[s["n"]]]
    if not truffet:
        print("\ningen sektorer ligger innenfor grensene")
        return

    print("\n%-26s %-13s %8s %8s %7s" % ("sektor", "status na", "blokker", "innenfor", "andel"))
    for s in sorted(truffet, key=lambda s: -per[s["n"]] / len(blokker[s["n"]])):
        n = len(blokker[s["n"]])
        print("%-26s %-13s %8d %8d %6.1f %%"
              % (s["n"], s["s"], n, per[s["n"]], 100.0 * per[s["n"]] / n))

    helt = [s["n"] for s in truffet if per[s["n"]] == len(blokker[s["n"]])]
    delvis = [s["n"] for s in truffet if s["n"] not in helt]
    print("\n%d sektorer har alle blokkene innenfor: %s" % (len(helt), ", ".join(sorted(helt))))
    if delvis:
        print("%d ligger delvis innenfor og ma vurderes hver for seg: %s"
              % (len(delvis), ", ".join(sorted(delvis))))
    aapne = [s["n"] for s in truffet if s["s"] == "open"]
    if aapne:
        print("\nav disse star %d oppfort som apne na: %s" % (len(aapne), ", ".join(sorted(aapne))))
        print("sett dem til stengt_annet i SECTORS hvis vedtaket omfatter dem,")
        print("kjor sa beregn.py og logg.py --skriv")


if __name__ == "__main__":
    main()

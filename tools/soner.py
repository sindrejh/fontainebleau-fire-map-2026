#!/usr/bin/env python3
"""Legger de stengte sonene fra ONFs kart inn i datablokka som SONER.

    curl -o soner.geojson https://umap.openstreetmap.fr/fr/datalayer/1443097/2ef1acb6-984c-4987-b95f-d7e5e6ad6186/
    python3 tools/soner.py soner.geojson

Arrete 2026/CAB/SIDPC/1386 stenger sonene som er tegnet pa kartvedleggene, men
vedleggene er skannede rasterkart. ONF forer de samme sonene som polygoner i et
uMap, og det er dem sida tegner og maler sektorene mot. Kjor skriptet pa nytt
nar ONF endrer sonelaget -- se forbudssone.py for hvor ID-ene star.

Koordinatene rundes til hundretusendels grad for de skrives, som resten av
datablokka. Det er de avrundede sonene sida tegner, sa det er ogsa dem
sektorene skal males mot. Skriptet gjor det til slutt og sier fra hvis en
sektor ligger et annet sted enn statusen dens sier -- da ma et menneske se pa
statusen, ikke skriptet.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beregn import les  # noqa: E402
from forbudssone import blokker_per_sektor, polygoner_fra_geojson, tell  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "index.html"
BRANN = ("brent_mye", "brent_delvis", "brent_kant", "naer", "stengt")


def rund(polygoner):
    """Runder av og fjerner punkter som faller sammen etter avrundinga."""
    ut = []
    for pol in polygoner:
        ringer = []
        for r in pol:
            ny = []
            for la, lo in r:
                p = [round(la, 5), round(lo, 5)]
                if not ny or ny[-1] != p:
                    ny.append(p)
            if len(ny) >= 4:
                ringer.append(ny)
        if ringer:
            ut.append(ringer)
    return ut


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    soner = rund(polygoner_fra_geojson(sys.argv[1]))

    src = HTML.read_text(encoding="utf8")
    linje = "const SONER = %s;\n" % json.dumps(soner, separators=(",", ":"))
    m = re.search(r"const SONER = \[.*?\];\n", src, re.S)
    if m:
        src = src[:m.start()] + linje + src[m.end():]
    else:
        # Rett etter brannflaten: beregn.py skriver konstantene i fast rekkefolge.
        m = re.search(r"const BURN_RINGS = \[.*?\];\n", src, re.S)
        src = src[:m.end()] + linje + src[m.end():]
    HTML.write_text(src, encoding="utf8")
    hjorner = sum(len(r) for pol in soner for r in pol)
    print("skrev %d soner, %d hjorner, inn i SONER" % (len(soner), hjorner))

    SECTORS = les("SECTORS", src)
    per = tell(blokker_per_sektor(src), SECTORS,
               [[[tuple(p) for p in r] for r in pol] for pol in soner])
    avvik = []
    for s in SECTORS:
        n, k = s["blokk"], per[s["n"]]
        if s["s"] in BRANN and k < n:
            avvik.append("%s har brannkategori, men %d av %d blokker ligger utenfor" % (s["n"], n - k, n))
        elif s["s"] == "open" and k > 0:
            avvik.append("%s er apen, men %d av %d blokker ligger innenfor" % (s["n"], k, n))
        elif s["s"] == "delvis" and k in (0, n):
            avvik.append("%s er delvis, men %s blokkene ligger innenfor" % (s["n"], "alle" if k else "ingen av"))
    if avvik:
        print("\nsektorer som ikke ligger der statusen sier:")
        for a in avvik:
            print("  " + a)
        print("vurder statusen deres, og kjor sa beregn.py og logg.py --skriv")
    else:
        print("alle sektorene ligger der statusen sier")


if __name__ == "__main__":
    main()

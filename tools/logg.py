#!/usr/bin/env python3
"""Forer statusendringer inn i endringsloggen.

    python3 tools/logg.py                 # vis hva som har endret seg
    python3 tools/logg.py --skriv         # skriv oppforingen inn i HISTORIKK
    python3 tools/logg.py --skriv --dato 2026-08-04

Arbeidsgangen naar ONF aapner en sektor: sett SECTORS[].s til "open" i
index.html, kjor beregn.py, og kjor sa dette skriptet. Det sammenlikner
statusene med forrige oyeblikksbilde i tools/statuslogg.json og skriver en
oppforing som sier hvilke sektorer som skiftet, og hvor mange som er aapne.

Skriptet finner ikke paa noe. Det oppgir bare hva som faktisk star i
datablokka na mot hva som sto der sist skriptet ble kjort.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "index.html"
SNAP = Path(__file__).resolve().parent / "statuslogg.json"

MND = ["januar", "februar", "mars", "april", "mai", "juni", "juli",
       "august", "september", "oktober", "november", "desember"]


def les(navn, src):
    m = re.search(r"const %s = (\[.*?\]|\{.*?\});\n" % navn, src, re.S)
    if not m:
        sys.exit("fant ikke %s i index.html" % navn)
    return json.loads(m.group(1)), m


def liste(navn, spraak):
    """«Apremont, Cuvier og Franchard» / «Apremont, Cuvier and Franchard»."""
    navn = sorted(navn)
    og = "og" if spraak == "nb" else "and"
    if len(navn) == 1:
        return navn[0]
    return "%s %s %s" % (", ".join(navn[:-1]), og, navn[-1])


def main():
    skriv = "--skriv" in sys.argv
    dato = date.today().isoformat()
    if "--dato" in sys.argv:
        dato = sys.argv[sys.argv.index("--dato") + 1]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", dato):
        sys.exit("datoen må være på formen ÅÅÅÅ-MM-DD")

    src = HTML.read_text(encoding="utf8")
    SECTORS, _ = les("SECTORS", src)
    naa = {s["n"]: s["s"] for s in SECTORS}

    if not SNAP.exists():
        SNAP.write_text(json.dumps({"dato": dato, "status": naa},
                                   ensure_ascii=False, indent=1), encoding="utf8")
        print("ingen grunnlinje fantes — lagret dagens statuser i %s" % SNAP.name)
        print("kjør skriptet igjen neste gang en sektor endrer status")
        return

    forrige = json.loads(SNAP.read_text(encoding="utf8"))
    gml = forrige["status"]
    endret = [(n, gml.get(n), s) for n, s in naa.items() if gml.get(n) != s]
    nye = [n for n in naa if n not in gml]
    borte = [n for n in gml if n not in naa]

    if not endret and not nye and not borte:
        print("ingen statusendringer siden %s" % forrige["dato"])
        return

    for n, a, b in sorted(endret):
        print("  %-28s %s → %s" % (n, a, b))
    for n in nye:
        print("  %-28s ny sektor (%s)" % (n, naa[n]))
    for n in borte:
        print("  %-28s falt ut av datasettet" % n)

    aapnet = sorted(n for n, a, b in endret if b == "open" and a != "open")
    stengt = sorted(n for n, a, b in endret if a == "open" and b != "open")
    n_open = sum(1 for s in naa.values() if s == "open")

    def tekst(sp):
        d = []
        if aapnet:
            d.append(("%s er åpnet igjen." if sp == "nb" else "%s reopened.")
                     % liste(aapnet, sp))
        if stengt:
            d.append(("%s er stengt igjen." if sp == "nb" else "%s closed again.")
                     % liste(stengt, sp))
        andre = [(n, a, b) for n, a, b in endret if n not in aapnet and n not in stengt]
        if andre:
            d.append(("%s har byttet statuskategori." if sp == "nb"
                      else "%s changed status category.")
                     % liste([n for n, _, _ in andre], sp))
        d.append(("%d av %d sektorer står nå oppført som åpne." if sp == "nb"
                  else "%d of %d sectors are now listed as open.") % (n_open, len(naa)))
        return " ".join(d)

    t = ("%d sektorer åpnet" % len(aapnet)) if len(aapnet) > 1 else (
         "%s åpnet" % aapnet[0]) if aapnet else "Adgangsstatus oppdatert"
    t_en = ("%d sectors reopened" % len(aapnet)) if len(aapnet) > 1 else (
            "%s reopened" % aapnet[0]) if aapnet else "Access status updated"

    ny = {"d": dato, "k": "adgang", "kilde": "crashpad",
          "t": t, "b": tekst("nb"), "t_en": t_en, "b_en": tekst("en")}
    print("\noppføring:")
    print(json.dumps(ny, ensure_ascii=False, indent=1))

    if not skriv:
        print("\n(kjør med --skriv for å legge den inn)")
        return

    H, m = les("HISTORIKK", src)
    H.append(ny)
    H.sort(key=lambda e: e["d"])
    src = src[:m.start(1)] + json.dumps(H, ensure_ascii=False, separators=(",", ":")) + src[m.end(1):]

    # META.updated og access_date foreles av oppforingen, sa de settes samtidig.
    MT, mm = les("META", src)
    MT["updated"] = dato
    MT["access_date"] = dato
    src = src[:mm.start(1)] + json.dumps(MT, ensure_ascii=False) + src[mm.end(1):]

    HTML.write_text(src, encoding="utf8")
    SNAP.write_text(json.dumps({"dato": dato, "status": naa},
                               ensure_ascii=False, indent=1), encoding="utf8")
    d = date.fromisoformat(dato)
    print("\nskrevet inn, datert %d. %s %d" % (d.day, MND[d.month - 1], d.year))
    print("husk å oppdatere META.ban_until hvis forbudet er forlenget")


if __name__ == "__main__":
    main()

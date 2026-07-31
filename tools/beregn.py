#!/usr/bin/env python3
"""Regner ut hvor mange av de faktiske blokkproblemene i hver sektor som ligger
innenfor brannflaten, og skriver resultatet inn i datablokka i index.html.

    git clone --depth 1 https://github.com/boolder-org/boolder-data.git
    python3 tools/beregn.py boolder-data/boolder.db

Brannflaten (BURN_RINGS), skoggrensene, klyngeinndelingen og adgangsstatusen
leses fra index.html og skrives tilbake urort. Det skriptet regner ut, er
blokktallene, andelen brent, avstanden til brannflaten, statuskategorien for
de brannrelaterte sektorene, blokkpunktene og de avledede tallene i META.

Kilder: brannflate Copernicus EMS EMSR894, blokkdata Boolder (CC BY 4.0).
"""
import json
import math
import re
import sqlite3
import sys
from pathlib import Path

try:
    import numpy as np
except ImportError:
    sys.exit("krever numpy:  pip install numpy")

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "index.html"

# Brannflaten ligger rundt 48,4 °N. Over et omrade pa 30 km er en lokal
# meterprojeksjon med fast skala noyaktig nok for punkt-i-polygon og avstand;
# kontrollert mot skogarealene i META er avviket 0,7 prosent.
LAT0 = 48.4
MLAT = 110540.0
MLON = 111320.0 * math.cos(math.radians(LAT0))

# Terskler for statuskategoriene, na regnet av andelen blokkproblemer.
T_MYE, T_DELVIS = 50.0, 10.0
NAER_KM = 1.0
# Adgangsstatus er ikke utledet av brannen og skrives ikke over. "uavklart" horer
# med her: den sier at vi ikke finner hjemmelen, og det er en menneskelig
# vurdering. Uten den i lista ville kategori() satt Beauvais til "stengt" ved
# neste kjoring, og vurderingen ville forsvunnet uten spor.
ADGANG = ("open", "stengt_annet", "uavklart")


def les(navn, src, slutt=";\n"):
    m = re.search(r"const %s = (\[.*?\]|\{.*?\})%s" % (navn, re.escape(slutt)), src, re.S)
    if not m:
        sys.exit("fant ikke %s i index.html" % navn)
    return json.loads(m.group(1))


def punkt_i_flate(px, py, ringer):
    """Crossing number mot hver ring. Ringene er 76 atskilte ytre flater --
    kontrollert med containment-test, ingen av dem ligger inni en annen, sa
    det finnes ingen hull a trekke fra."""
    inne = np.zeros(len(px), dtype=bool)
    for r in ringer:
        ry = np.array([q[0] for q in r]) * MLAT
        rx = np.array([q[1] for q in r]) * MLON
        if (px.min() > rx.max() or px.max() < rx.min()
                or py.min() > ry.max() or py.max() < ry.min()):
            continue
        y1, y2 = ry, np.roll(ry, -1)
        x1, x2 = rx, np.roll(rx, -1)
        kryss = np.zeros(len(px), dtype=np.int32)
        for k in range(len(r)):
            a = (y1[k] > py) != (y2[k] > py)
            if not a.any():
                continue
            xint = (x2[k] - x1[k]) * (py - y1[k]) / (y2[k] - y1[k]) + x1[k]
            kryss += (a & (px < xint)).astype(np.int32)
        inne |= kryss % 2 == 1
    return inne


def avstand(px, py, ringer):
    """Korteste avstand i meter fra hvert punkt til naermeste ringkant."""
    seg = []
    for r in ringer:
        ry = np.array([q[0] for q in r]) * MLAT
        rx = np.array([q[1] for q in r]) * MLON
        seg.append(np.stack([rx, ry, np.roll(rx, -1), np.roll(ry, -1)], axis=1))
    S = np.concatenate(seg)
    ax, ay, bx, by = S[:, 0], S[:, 1], S[:, 2], S[:, 3]
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    L2[L2 == 0] = 1e-12
    ut = np.empty(len(px))
    for i in range(0, len(px), 256):
        QX, QY = px[i:i + 256, None], py[i:i + 256, None]
        t = np.clip(((QX - ax) * dx + (QY - ay) * dy) / L2, 0.0, 1.0)
        ddx, ddy = QX - (ax + t * dx), QY - (ay + t * dy)
        ut[i:i + 256] = np.sqrt(ddx * ddx + ddy * ddy).min(axis=1)
    return ut


def areal_ha(ring):
    k = math.cos(math.radians(sum(p[0] for p in ring) / len(ring)))
    pts = [(p[1] * 111320.0 * k, p[0] * MLAT) for p in ring]
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return abs(a / 2.0) / 1e4


def kategori(gammel, stein, km):
    if gammel in ADGANG:
        return gammel
    if stein > T_MYE:
        return "brent_mye"
    if stein >= T_DELVIS:
        return "brent_delvis"
    if stein > 0:
        return "brent_kant"
    return "naer" if km < NAER_KM else "stengt"


def kvantiser(punkter):
    """Sorterer punktene og runder dem til hundretusendels grad -- omtrent en
    meter. Dette er koordinatene sida faktisk publiserer, og de er derfor ogsa
    de som skal males mot brannflaten: ellers kan en blokk som ligger under en
    meter fra brannkanten telles som brent, men tegnes utenfor flaten.
    Boolders GPS-punkter og den forenklede brannflaten har uansett langt
    grovere feilmarginer enn en meter."""
    punkter = sorted(punkter)
    la0 = round(min(p[0] for p in punkter), 5)
    lo0 = round(min(p[1] for p in punkter), 5)
    dl = [(round((la - la0) * 1e5), round((lo - lo0) * 1e5)) for la, lo in punkter]
    ut = [(la0 + a / 1e5, lo0 + o / 1e5) for a, o in dl]
    arr, pl, po = [], 0, 0
    for a, o in dl:
        arr += [a - pl, o - po]
        pl, po = a, o
    return ut, [la0, lo0, arr]


def main():
    db = Path(sys.argv[1] if len(sys.argv) > 1 else "boolder-data/boolder.db")
    if not db.exists():
        sys.exit("fant ikke %s -- klon boolder-org/boolder-data forst" % db)

    src = HTML.read_text(encoding="utf8")
    META = les("META", src)
    RINGER = les("BURN_RINGS", src)
    SECTORS = les("SECTORS", src)

    con = sqlite3.connect(db)
    rader = con.execute(
        "select a.name, p.latitude, p.longitude from problems p "
        "join areas a on a.id = p.area_id"
    ).fetchall()

    navn = {s["n"] for s in SECTORS}
    mangler = {r[0] for r in rader} ^ navn
    if mangler:
        sys.exit("sektornavn matcher ikke Boolder: %s" % sorted(mangler))

    # Kvantiser forst, mal etterpa. Da er tallet sida oppgir, prikken sida
    # tegner og en eventuell etterregning i nettleseren utledet av nover de
    # samme koordinatene.
    raa = {}
    for omr, la, lo in rader:
        raa.setdefault(omr, []).append((la, lo))
    per, flat = {}, []
    for omr, pts in raa.items():
        kv, kode = kvantiser(pts)
        per[omr] = {"n": len(kv), "b": 0, "d": 9e9, "kode": kode}
        for la, lo in kv:
            flat.append((omr, la, lo))

    px = np.array([r[2] for r in flat]) * MLON
    py = np.array([r[1] for r in flat]) * MLAT
    inne = punkt_i_flate(px, py, RINGER)
    dist = avstand(px, py, RINGER)
    dist[inne] = 0.0

    for (omr, la, lo), i, d in zip(flat, inne, dist):
        e = per[omr]
        e["b"] += int(i)
        e["d"] = min(e["d"], d)

    endret = []
    for s in SECTORS:
        e = per[s["n"]]
        stein = round(100.0 * e["b"] / e["n"], 1) if e["n"] else 0.0
        ny = kategori(s["s"], stein, e["d"] / 1000.0)
        if ny != s["s"]:
            endret.append((s["n"], s["s"], ny, s["brent"], stein))
        s["blokk"] = e["n"]
        s["bb"] = e["b"]
        # flate er det gamle malet -- andelen av sektorens rektangulaere yttergrense
        # som overlapper brannflaten. Det regnes ikke ut her; det kommer fra
        # overlappsanalysen i Lambert-93 og settes ved forste kjoring. Skrives det
        # over med brent, forsvinner sammenlikningsgrunnlaget ved neste kjoring.
        s["flate"] = s.get("flate", s["brent"])
        s["brent"] = stein               # nytt tall: andel av blokkproblemene
        s["avst"] = round(e["d"] / 1000.0, 2)
        s["s"] = ny

    PTS = {n: e["kode"] for n, e in per.items()}

    META["blokk_total"] = sum(s["blokk"] for s in SECTORS)
    META["blokk_brent"] = sum(s["bb"] for s in SECTORS)
    META["blokk_pct"] = round(100.0 * META["blokk_brent"] / META["blokk_total"], 1)
    META["n_ramma"] = sum(1 for s in SECTORS if s["bb"] > 0)
    META["n_naer"] = sum(1 for s in SECTORS if s["bb"] == 0 and s["avst"] < NAER_KM)
    META["n_helt"] = sum(1 for s in SECTORS if s["brent"] == 100.0)
    META["n_vurdert"] = sum(1 for s in SECTORS if s["iaoi"])
    META["n_total"] = len(SECTORS)
    META["n_open"] = sum(1 for s in SECTORS if s["s"] == "open")
    META["rings"] = len(RINGER)
    META["ring_ha"] = round(sum(areal_ha(r) for r in RINGER))
    # Naermeste sektor utenfor Copernicus' analyseomrade. Sier hvor stor klaring
    # de uvurderte sektorene faktisk har til naermeste kartlagte brannflate.
    META["uaoi_min"] = min(s["avst"] for s in SECTORS if not s["iaoi"])

    # De to eksemplene metodeteksten bruker for a vise hva bytte av mal gjorde:
    # sektoren det gamle rektangelmalet undervurderte mest, og en sektor der
    # rektanglet viste brannskade uten at en eneste blokk ligger i flaten.
    def eks(s):
        return {"n": s["n"], "flate": s["flate"], "brent": s["brent"],
                "blokk": s["blokk"], "bb": s["bb"]}
    META["eks_opp"] = eks(max(SECTORS, key=lambda s: s["brent"] - s["flate"]))
    ned = [s for s in SECTORS if s["flate"] > 0 and s["bb"] == 0]
    META["eks_ned"] = eks(min(ned, key=lambda s: s["brent"] - s["flate"])) if ned else None

    blokk = ["/* === DATA === */",
             "/* SECTORS, PTS og de avledede tallene i META er regnet ut av",
             "   tools/beregn.py. Rediger dem der, ikke her. */"]
    for k, v in (("META", META), ("CAT", les("CAT", src)), ("SOURCES", les("SOURCES", src)),
                 ("HISTORIKK", les("HISTORIKK", src)),
                 ("BURN_RINGS", RINGER), ("FORESTS", les("FORESTS", src, ";\nconst SECTORS")),
                 ("SECTORS", SECTORS), ("PLACES", les("PLACES", src)), ("PTS", PTS)):
        if k == "HISTORIKK":
            blokk += ["/* Endringsloggen. Hver oppforing peker pa en kilde i SOURCES, og sier bare",
                      "   det kildene faktisk viser. tools/logg.py forer opp statusendringer. */"]
        if k == "PTS":
            blokk += ["/* Blokkproblemene per sektor, delta-kodet. Se kvantiser() i tools/beregn.py. */"]
        blokk.append("const %s = %s;" % (k, json.dumps(v, ensure_ascii=False, separators=(", ", ": ") if k in ("META",) else (",", ":"))))
    ny_data = "\n".join(blokk)

    boolder = re.search(r"(/\* Boolder-URL.*?const BOOLDER = \{.*?\};)", src, re.S).group(1)
    ny_data = ny_data + "\n" + boolder + "\n/* === END DATA === */"
    ut = re.sub(r"/\* === DATA === \*/.*?/\* === END DATA === \*/", lambda _: ny_data, src, flags=re.S)

    # Meta-taggene leses av lenkeforhandsvisninger og sokemotorer for skriptet
    # kjorer, sa de kan ikke bygges av META i nettleseren. De skrives her i
    # stedet, slik at de ikke blir staende igjen med gamle tall.
    def mt(n):
        return f"{n:,}".replace(",", " ")

    ut = re.sub(
        r'(<meta property="og:description" content=")[^"]*(")',
        lambda m: m.group(1) + "%s hektar brant, fordelt på %d atskilte flater. %s av %s "
        "blokkproblemer ligger innenfor brannflaten." % (
            mt(META["burn_ha"]), META["rings"],
            mt(META["blokk_brent"]), mt(META["blokk_total"])) + m.group(2), ut)
    HTML.write_text(ut, encoding="utf8")

    print("%d av %d blokkproblemer (%.1f %%) ligger i brannflaten"
          % (META["blokk_brent"], META["blokk_total"], META["blokk_pct"]))
    print("%d sektorer rammet, %d av dem med alle blokkene inne i brannflaten"
          % (META["n_ramma"], META["n_helt"]))
    print("%d sektorer uten skade under %.0f km fra flaten" % (META["n_naer"], NAER_KM))
    print("ringareal %d ha mot Copernicus' %d ha (%+.1f %% av forenklingen)"
          % (META["ring_ha"], META["burn_ha"],
             100.0 * (META["ring_ha"] - META["burn_ha"]) / META["burn_ha"]))
    if endret:
        print("\nstatus endret av det nye malet:")
        for n, a, b, f, st in endret:
            print("  %-26s %-13s -> %-13s  flate %.1f %% -> stein %.1f %%" % (n, a, b, f, st))


if __name__ == "__main__":
    main()

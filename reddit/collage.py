import json, gzip, os
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.collections import LineCollection, PolyCollection
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
F = '/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/'
for f in ['FrauncesVar.ttf', 'IBMPlexMono-Regular.ttf', 'IBMPlexMono-Medium.ttf', 'SourceSerif4-Regular.ttf', 'SourceSerif4-Semibold.ttf', 'SourceSerif4-It.ttf']:
    fm.fontManager.addfont(F + f)
DISP = fm.FontProperties(fname=F + 'FrauncesVar.ttf', weight=900)
SER = 'Source Serif 4'; MONO = 'IBM Plex Mono'

BG = '#ECE8E1'; LAND = '#DCD6CC'; EDGE = '#C8C0B3'; MOD = '#ABA49A'
FG = '#1C1A17'; MUT = '#6A645B'; ROM = '#B5432F'; GOLD = '#4B1D6B'; HOT = '#4B1D6B'

tr = Transformer.from_crs(4326, 27700, always_xy=True)
R = json.load(open(os.path.join(ROOT, 'results', 'results_40m.json')))
COV = json.load(open(os.path.join(ROOT, 'results', 'roman_coverage.json')))
tot = R['total']; nat = {n['nation']: n for n in R['nations']}
cty = R['counties']; roads = R['roads']

def proj(c):
    c = np.asarray(c, float); x, y = tr.transform(c[:, 0], c[:, 1]); return np.c_[x, y]

# county polygons
polys = []
for f in json.load(open(os.path.join(ROOT, 'data', 'counties.geojson')))['features']:
    gs = f['geometry'].get('geometries', [f['geometry']])
    pp = []
    for g in gs:
        if g['type'] == 'MultiPolygon': pp += g['coordinates']
        elif g['type'] == 'Polygon': pp.append(g['coordinates'])
    for p in pp:
        polys.append(proj(p[0]))
# modern A-roads
osm = json.load(gzip.open(os.path.join(ROOT, 'data', 'osm_aroads.json.gz')))
mod = []
for w in osm:
    c = np.asarray(w[5], float).reshape(-1, 2) / 1e5
    mod.append(c)
lens = [len(c) for c in mod]; allc = proj(np.vstack(mod)); mod = np.split(allc, np.cumsum(lens)[:-1])
del osm
def lines(path):
    out = []
    for f in json.load(open(path))['features']:
        g = f['geometry']; cs = g['coordinates'] if g['type'] == 'MultiLineString' else [g['coordinates']]
        out += [proj(c) for c in cs if len(c) > 1 and not (np.asarray(c)[:, 1].min() < 50.6 and np.asarray(c)[:, 0].max() > 1.0) and np.asarray(c)[:, 0].max() < 1.5]
    return out
rom = lines(os.path.join(ROOT, 'results', 'itinere_gb_corrected.geojson'))
hit = lines(os.path.join(ROOT, 'results', 'roman_aroads.geojson'))

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(0.04, 0.968, 'How Roman is your road?', fontproperties=DISP, fontsize=52, color=FG, va='top')
fig.text(0.04, 0.912, f"I laid an atlas of Roman roads over all {tot['km']:,.0f} km of Great Britain's A-roads.\n"
         f"Nearly two thousand years on, {tot['roman_km']:,.0f} km of them still run on a Roman line.",
         family=SER, fontsize=15.5, color=FG, va='top', linespacing=1.35)

# ---------------- hero map
ax = fig.add_axes([0.0, 0.262, 0.62, 0.6]); ax.set_facecolor(BG)
ax.add_collection(PolyCollection(polys, facecolor=LAND, edgecolor=EDGE, lw=0.35, zorder=1))
ax.add_collection(LineCollection(mod, colors=MOD, lw=0.4, alpha=0.9, zorder=2, rasterized=True))
ax.add_collection(LineCollection(rom, colors=ROM, lw=1.25, alpha=0.95, zorder=4, rasterized=True, capstyle='round'))
ax.add_collection(LineCollection(hit, colors=HOT, lw=2.1, zorder=6, rasterized=True, capstyle='round'))
ax.axis('off'); ax.set_ylim(5000, 980000)
W = 975000 * (0.62 * 12) / (0.6 * 15); ax.set_xlim(40000, 40000 + W); ax.set_aspect('equal', adjustable='box')

# label anchors snapped to the gold A-road-on-Roman-line stretch of each road (results/roman_aroads.geojson)
LAB = [('A66\nStainmore', -2.20607, 54.51554, 560000, 575000, 'left'), ('A15\nErmine Street', -0.55436, 53.50241, 590000, 455000, 'left'),
       ('A5\nWatling Street', -1.22543, 52.42262, 680000, 345000, 'left'), ('A429\nFosse Way', -1.84855, 51.82905, 262000, 150000, 'right'),
       ('A2\nto Dover', 0.91746, 51.30307, 680000, 125000, 'left')]
for t, lon, lat, tx_, ty_, ha in LAB:
    x, y = tr.transform(lon, lat)
    ax.scatter([x], [y], s=14, facecolor='none', edgecolor=FG, lw=0.9, zorder=9)
    ax.annotate(t, (x, y), (tx_, ty_), linespacing=1.15, family=MONO, fontsize=10.5, color=FG, va='center',
                ha=ha, zorder=8,
                arrowprops=dict(arrowstyle='-', color=MUT, lw=0.7, shrinkA=2, shrinkB=3))
lg = fig.add_axes([0.63, 0.272, 0.3, 0.056]); lg.axis('off'); lg.set_xlim(0, 10); lg.set_ylim(0, 3)
for y, c, lw, t in [(2.5, MOD, 1.2, 'modern A-road'), (1.5, ROM, 2.2, 'Roman road (Itiner-e)'), (0.5, HOT, 3.2, 'A-road on a Roman line')]:
    lg.plot([0, 1.2], [y, y], color=c, lw=lw, solid_capstyle='round')
    lg.text(1.6, y, t, family=MONO, fontsize=10.5, color=FG, va='center')

# ---------------- right column numbers
tx = fig.add_axes([0.63, 0.30, 0.35, 0.57]); tx.axis('off')
top = cty[0]; a5 = [r for r in roads if r['ref1'] == 'A5'][0]
notes = [(f"{tot['share']:.1f}%", f"of Great Britain's A-road length\nfollows a Roman line. England {nat['England']['share']:.1f}%,\nWales {nat['Wales']['share']:.1f}%, Scotland {nat['Scotland']['share']:.1f}%."),
         (f"{top['share']:.1f}%", f"in {top['county']}, the most Roman\ncounty, mostly the Fosse Way ({top['top'][0][0]})."),
         (f"{a5['roman_km']:.0f} km", 'of the A5 runs on Watling Street,\nmore than any other A-road.'),
         (f"{COV['share']:.0f}%", f"of the {COV['roman_km']:,.0f} km of Roman road in\nthe atlas now lies under an A-road;\n{COV['Main Road']['share']:.0f}% for the main routes.")]
for (b, s), y in zip(notes, [1.0, 0.75, 0.52, 0.29]):
    tx.text(0, y, b, fontproperties=DISP, fontsize=42, color=ROM, va='top', transform=tx.transAxes)
    tx.text(0, y - 0.095, s, family=SER, fontsize=13, color=FG, va='top', transform=tx.transAxes, linespacing=1.3)

# ---------------- bottom: county ranking and roads
def bars(a, labels, vals, fmt, xmax, col):
    a.set_facecolor(BG); a.axis('off')
    n = len(vals); y = np.arange(n)[::-1]
    a.barh(y, [xmax] * n, height=0.62, color='#DDD7CD')
    a.barh(y, vals, height=0.62, color=col)
    for yy, l, v in zip(y, labels, vals):
        a.text(-0.02 * xmax, yy, l, family=MONO, fontsize=10.5, color=FG, ha='right', va='center')
        a.text(v + 0.015 * xmax, yy, fmt(v), family=MONO, fontsize=10.5, color=FG, va='center')
    a.set_xlim(0, xmax); a.set_ylim(-0.6, n - 0.4)

N = 10
a1 = fig.add_axes([0.235, 0.095, 0.24, 0.145])
bars(a1, [c['county'] for c in cty[:N]], [c['share'] for c in cty[:N]], lambda v: f'{v:.1f}%', 20, ROM)
fig.text(0.04, 0.252, 'MOST ROMAN COUNTIES  share of A-road km', family=MONO, fontsize=11, color=MUT)
a2 = fig.add_axes([0.66, 0.095, 0.27, 0.145])
bars(a2, [r['ref1'] for r in roads[:N]], [r['roman_km'] for r in roads[:N]], lambda v: f'{v:.0f} km', 150, GOLD)
fig.text(0.6, 0.252, 'MOST ROMAN A-ROADS  km on a Roman line', family=MONO, fontsize=11, color=MUT)

fig.text(0.04, 0.016, 'Data: Itiner-e static version 2024 (de Soto et al. 2025, Scientific Data), CC BY 4.0, datum corrected from OSGB36.\n'
         'A-roads © OpenStreetMap contributors (ODbL), October 2026. Counties: ONS, contains OS data © Crown copyright (OGL v3).\n'
         'A stretch counts if within 40 m of a Roman road and on the same heading. Itiner-e marks all British routes conjectured or hypothetical.\n'
         'Analysis and chart: Tristan Hotham, with Python and matplotlib.',
         family=MONO, fontsize=9, color=MUT, linespacing=1.45)
fig.savefig(os.path.join(HERE, 'how_roman_is_your_road.png'), facecolor=BG, dpi=200)
print('ok')

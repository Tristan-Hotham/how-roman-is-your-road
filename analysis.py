"""How Roman is your road?

Share of each county's A-road length that runs along a Roman road line.

Inputs
  data/itinere_gb.geojson   Itiner-e static version 2024 (de Soto et al. 2025, CC BY 4.0), Britain subset, WGS84
  data/osm_aroads.json.gz   OpenStreetMap ways tagged motorway/trunk/primary with an A-road ref (ODbL), compact form
  data/counties.geojson     Ceremonial counties (England), preserved counties (Wales), council areas (Scotland),
                            built from ONS local authority boundaries 2025 (OGL) with counties.py

Method
  Every A-road is cut into pieces of about 20 m. A piece counts as "on a Roman line" when its midpoint lies
  within BUFFER metres of an Itiner-e road AND it runs in roughly the same direction (within ANGLE degrees),
  so roads that merely cross a Roman road do not count. Dual carriageways are mapped in OSM as two one-way
  ways, so one-way ways are weighted by one half. Everything is measured on the British National Grid.
"""
import gzip, json, sys
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from pyproj import Transformer

BUFFER = float(sys.argv[1]) if len(sys.argv) > 1 else 40.0
ANGLE = 20.0
STEP = 20.0
tr = Transformer.from_crs(4326, 27700, always_xy=True)

# ---------- Roman roads ----------
rr = gpd.read_file('data/itinere_gb.geojson')
# Datum fix: in Britain the Itiner-e lines sit about 100 m east of the roads they trace (A15 north of Lincoln,
# A46, A429 Fosse Way). Reading their coordinates as OSGB36 latitude/longitude (EPSG:4277) rather than WGS84
# removes the offset: median distance from the A429 to the Fosse Way falls from 106 m to 8 m. So we convert.
_t = Transformer.from_crs(4277, 4326, always_xy=True)
rr['geometry'] = rr.geometry.apply(lambda g: shapely.transform(g, lambda c: np.column_stack(_t.transform(c[:, 0], c[:, 1]))))
if BUFFER == 40:
    rr.to_file('results/itinere_gb_corrected.geojson', driver='GeoJSON', COORDINATE_PRECISION=6)
rr = rr.to_crs(27700)
counties = gpd.read_file('data/counties.geojson').to_crs(27700)
land = shapely.union_all(counties.geometry.values)
rr = rr[rr.intersects(land.buffer(2000))].copy()

def segs(geoms, keep=None):
    """Explode lines into straight segments: arrays x0,y0,x1,y1 and the source index."""
    out = []
    for i, g in enumerate(geoms):
        for part in getattr(g, 'geoms', [g]):
            c = np.asarray(part.coords)[:, :2]
            if len(c) < 2: continue
            out.append(np.column_stack([c[:-1], c[1:], np.full(len(c) - 1, i)]))
    return np.vstack(out)

def roman_index(sub):
    s = segs(sub.geometry.values)
    lines = shapely.linestrings(np.stack([s[:, 0:2], s[:, 2:4]], axis=1))
    ang = np.degrees(np.arctan2(s[:, 3] - s[:, 1], s[:, 2] - s[:, 0])) % 180
    return shapely.STRtree(lines), lines, ang

# ---------- A-roads ----------
ways = json.load(gzip.open('data/osm_aroads.json.gz', 'rt'))
rows = []
for wid, ref, hw, oneway, name, flat in ways:
    a = np.asarray(flat, dtype=float).reshape(-1, 2) / 1e5
    x, y = tr.transform(a[:, 0], a[:, 1])
    rows.append((wid, ref, hw, oneway, name, np.column_stack([x, y])))

# cut every way into ~STEP m pieces: midpoints, direction, length, weight
mid, ang, ln, wt, wix = [], [], [], [], []
for k, (wid, ref, hw, oneway, name, c) in enumerate(rows):
    w = 0.5 if oneway in ('yes', '-1', 'true', '1') else 1.0
    d = np.diff(c, axis=0); L = np.hypot(d[:, 0], d[:, 1])
    for (x0, y0), (dx, dy), l in zip(c[:-1], d, L):
        if l == 0: continue
        n = max(1, int(np.ceil(l / STEP)))
        t = (np.arange(n) + 0.5) / n
        mid.append(np.column_stack([x0 + dx * t, y0 + dy * t]))
        a = np.degrees(np.arctan2(dy, dx)) % 180
        ang.append(np.full(n, a)); ln.append(np.full(n, l / n)); wt.append(np.full(n, w)); wix.append(np.full(n, k))
mid = np.vstack(mid); ang = np.concatenate(ang); ln = np.concatenate(ln); wt = np.concatenate(wt); wix = np.concatenate(wix)
pts = shapely.points(mid)
print('A-road pieces', len(pts), file=sys.stderr)

# county of each piece (nearest county for pieces just off the generalised coastline)
cj = gpd.sjoin_nearest(gpd.GeoDataFrame(geometry=pts, crs=27700), counties[['county', 'nation', 'geometry']], max_distance=3000, how='left')
cj = cj[~cj.index.duplicated()]
county = cj['county'].values; nation = cj['nation'].values

def on_roman(sub):
    tree, lines, rang = roman_index(sub)
    pi, li = tree.query_nearest(pts, max_distance=BUFFER, all_matches=True)
    diff = np.abs(ang[pi] - rang[li]); diff = np.minimum(diff, 180 - diff)
    ok = np.zeros(len(pts), bool); ok[pi[diff <= ANGLE]] = True
    return ok

flag_all = on_roman(rr)
flag_conj = on_roman(rr[rr['cert'] != 'Hypothetical'])

df = pd.DataFrame({'county': county, 'nation': nation, 'km': ln * wt / 1000,
                   'roman': flag_all, 'roman_conj': flag_conj, 'w': wix})
df['ref'] = [rows[i][1] for i in df.w]
df = df[df.county.notna()]
df['rkm'] = df.km * df.roman; df['rkm_conj'] = df.km * df.roman_conj

g = df.groupby(['county', 'nation']).agg(km=('km', 'sum'), roman_km=('rkm', 'sum'), roman_km_conj=('rkm_conj', 'sum')).reset_index()
g['share'] = 100 * g.roman_km / g.km; g['share_conj'] = 100 * g.roman_km_conj / g.km

# top Roman A-roads per county
df['ref1'] = df.ref.str.split(';').str[0].str.strip()
top = (df[df.roman].groupby(['county', 'ref1']).rkm.sum().reset_index()
       .sort_values(['county', 'rkm'], ascending=[True, False]).groupby('county').head(4))
g['top'] = g.county.map(top.groupby('county').apply(lambda t: [[r, round(k, 1)] for r, k in zip(t.ref1, t.rkm)]).to_dict())

# whole roads: which A-roads are most Roman (GB-wide, at least 20 km long)
roads = df.groupby('ref1').agg(km=('km', 'sum'), roman_km=('rkm', 'sum')).reset_index()
roads['share'] = 100 * roads.roman_km / roads.km
roads = roads[roads.km >= 20].sort_values('roman_km', ascending=False)

nat = df.groupby('nation').agg(km=('km', 'sum'), roman_km=('rkm', 'sum')).reset_index()
nat['share'] = 100 * nat.roman_km / nat.km
tot = {'km': df.km.sum(), 'roman_km': df.rkm.sum(), 'share': 100 * df.rkm.sum() / df.km.sum()}

res = {'buffer_m': BUFFER, 'angle_deg': ANGLE, 'total': tot, 'nations': nat.round(2).to_dict('records'),
       'counties': g.round(2).sort_values('share', ascending=False).to_dict('records'),
       'roads': roads.head(40).round(2).to_dict('records'),
       'roman_km_itinere': float(rr[rr.intersects(land)].length.sum() / 1000)}
json.dump(res, open(f'results/results_{int(BUFFER)}m.json', 'w'), indent=1, default=float)

if BUFFER == 40:
    # A-road stretches on Roman lines, for the map (merged, simplified, WGS84)
    df_all = pd.DataFrame({'w': wix, 'roman': flag_all})
    keep = []
    for k, grp in df_all.groupby('w'):
        f = grp.roman.values
        if not f.any(): continue
        c = rows[k][5]
        # rebuild runs along the way using the piece midpoints
        m = mid[grp.index.values]
        run = []
        for p, ok in zip(m, f):
            if ok: run.append(p)
            elif len(run) >= 2: keep.append((rows[k][1], np.array(run))); run = []
            else: run = []
        if len(run) >= 2: keep.append((rows[k][1], np.array(run)))
    back = Transformer.from_crs(27700, 4326, always_xy=True)
    feats = []
    for ref, c in keep:
        line = shapely.simplify(shapely.linestrings(c), 8)
        cc = np.asarray(line.coords)
        if len(cc) < 2: continue
        lon, lat = back.transform(cc[:, 0], cc[:, 1])
        feats.append({'type': 'Feature', 'properties': {'ref': ref.split(';')[0]},
                      'geometry': {'type': 'LineString', 'coordinates': [[round(a, 5), round(b, 5)] for a, b in zip(lon, lat)]}})
    json.dump({'type': 'FeatureCollection', 'features': feats}, open('results/roman_aroads.geojson', 'w'), separators=(',', ':'))
    print('roman stretches', len(feats), file=sys.stderr)

print(json.dumps({'total': tot, 'nations': res['nations']}, default=float, indent=1))
print(g.sort_values('share', ascending=False)[['county', 'km', 'roman_km', 'share', 'share_conj']].round(1).to_string())
print(roads.head(25).round(1).to_string())

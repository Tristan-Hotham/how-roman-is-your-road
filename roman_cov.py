"""Reverse view: what share of the Roman network (Itiner-e, datum-corrected) now lies under an A-road?
Same rule as analysis.py: a 20 m piece of Roman road counts if an A-road runs within 40 m in the same
direction (within 20 degrees). Run after analysis.py, which writes results/itinere_gb_corrected.geojson."""
import gzip, json
import numpy as np
import geopandas as gpd
import shapely
from pyproj import Transformer

tr = Transformer.from_crs(4326, 27700, always_xy=True)
rr = gpd.read_file('results/itinere_gb_corrected.geojson').to_crs(27700)
counties = gpd.read_file('data/counties.geojson').to_crs(27700)
land = shapely.union_all(counties.geometry.simplify(100).buffer(200).values)  # generalised coast, so clipping is quick
rr['geometry'] = rr.geometry.intersection(land)
rr = rr[~rr.is_empty]

segs = []
for w in json.load(gzip.open('data/osm_aroads.json.gz', 'rt')):
    a = np.asarray(w[5], float).reshape(-1, 2) / 1e5
    if len(a) < 2: continue
    x, y = tr.transform(a[:, 0], a[:, 1]); c = np.column_stack([x, y])
    segs.append(np.column_stack([c[:-1], c[1:]]))
S = np.vstack(segs); S = S[np.hypot(S[:, 2] - S[:, 0], S[:, 3] - S[:, 1]) > 0]
tree = shapely.STRtree(shapely.linestrings(np.stack([S[:, :2], S[:, 2:]], axis=1)))
sang = np.degrees(np.arctan2(S[:, 3] - S[:, 1], S[:, 2] - S[:, 0])) % 180

mid, ang, ln, typ = [], [], [], []
for g, t in zip(rr.geometry, rr['type']):
    for part in getattr(g, 'geoms', [g]):
        if part.geom_type != 'LineString': continue
        c = np.asarray(part.coords)[:, :2]
        for (x0, y0), (x1, y1) in zip(c[:-1], c[1:]):
            l = np.hypot(x1 - x0, y1 - y0)
            if l == 0: continue
            n = max(1, int(np.ceil(l / 20))); f = (np.arange(n) + .5) / n
            mid.append(np.column_stack([x0 + (x1 - x0) * f, y0 + (y1 - y0) * f]))
            ang.append(np.full(n, np.degrees(np.arctan2(y1 - y0, x1 - x0)) % 180))
            ln.append(np.full(n, l / n)); typ += [t] * n
mid = np.vstack(mid); ang = np.concatenate(ang); ln = np.concatenate(ln); typ = np.array(typ)

pi, si = tree.query_nearest(shapely.points(mid), max_distance=40, all_matches=True)
d = np.abs(ang[pi] - sang[si]); d = np.minimum(d, 180 - d)
ok = np.zeros(len(mid), bool); ok[pi[d <= 20]] = True

out = {'roman_km': float(ln.sum() / 1000), 'under_aroad_km': float(ln[ok].sum() / 1000),
       'share': float(100 * ln[ok].sum() / ln.sum())}
for t in ['Main Road', 'Secondary Road']:
    m = typ == t
    out[t] = {'km': float(ln[m].sum() / 1000), 'share': float(100 * ln[m & ok].sum() / ln[m].sum())}
json.dump(out, open('results/roman_coverage.json', 'w'), indent=1)
print(out)

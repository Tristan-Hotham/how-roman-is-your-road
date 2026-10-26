"""Assemble the GitHub Pages site from template.html, the 40 m results and the map layers."""
import json, os, shutil
import geopandas as gpd

os.makedirs('map', exist_ok=True)
R = json.load(open('results/results_40m.json'))
S = {b: json.load(open(f'results/results_{b}m.json')) for b in (20, 40, 80, 150)}
cov = json.load(open('results/roman_coverage.json')) if os.path.exists('results/roman_coverage.json') else None

# web layers
c = gpd.read_file('data/counties.geojson')
c['geometry'] = c.geometry.simplify(0.002, preserve_topology=True)
c.to_file('map/counties.geojson', driver='GeoJSON', COORDINATE_PRECISION=4)
r = gpd.read_file('results/itinere_gb_corrected.geojson')[['name', 'type', 'cert', 'geometry']]
land = c.to_crs(27700).buffer(2000).union_all()
r = r[r.to_crs(27700).intersects(land)]  # drop the few French roads in the bounding box
r.to_file('map/roman_roads.geojson', driver='GeoJSON', COORDINATE_PRECISION=5)
shutil.copy('results/roman_aroads.geojson', 'map/roman_aroads.geojson')

fmt = lambda x, d=1: f'{x:,.{d}f}'
T = R['total']; nat = {n['nation']: n for n in R['nations']}
cty = {x['county']: x for x in R['counties']}
roads = R['roads']
zero = [x['county'] for x in R['counties'] if x['roman_km'] < 0.05]
top = R['counties'][0]
a5 = next(x for x in roads if x['ref1'] == 'A5')

res = {'total': T, 'counties': [{k: x[k] for k in ('county', 'nation', 'km', 'roman_km', 'share', 'top')} for x in R['counties']],
       'roads': [{k: x[k] for k in ('ref1', 'km', 'roman_km', 'share')} for x in roads[:15]]}

places = [
    {'name': 'Downham, Lancashire', 'lat': 53.8952, 'lon': -2.3270, 'z': 15,
     'note': 'The road from Ribchester to Ilkley leaves the A59 at Worston and runs north of Pendle Hill. Its raised bank, the agger, is the straight ridge under the purple line.'},
    {'name': 'Ackling Dyke, Dorset', 'lat': 50.9435, 'lon': -1.9790, 'z': 15,
     'note': 'The road from Old Sarum to Dorchester survives as a tall bank across Oakley Down, running straight past a cluster of Bronze Age barrows.'},
    {'name': 'Stane Street, West Sussex', 'lat': 50.8915, 'lon': -0.6500, 'z': 15,
     'note': 'London to Chichester. In Eartham Wood the lidar sees through the trees to the embankment.'},
    {'name': 'High Street, Cumbria', 'lat': 54.5000, 'lon': -2.8650, 'z': 14,
     'note': 'Brougham to Ambleside, over the fells at more than 800 metres. Here the road is a terrace along the ridge rather than a bank.'},
]

intro = f'''
    <p style="margin-top:28px">Roman surveyors laid out long, straight alignments between forts and towns, and some of those lines never fell out of use. Watling Street became the A5. Ermine Street lives on in the A10 and the A1198. The Fosse Way is still the A429 across the Cotswolds and the A46 into Lincoln.</p>
    <p>But how much of the modern network really follows them? To find out, I laid the new Itiner-e atlas of Roman roads, published in 2025, over every A-road in Great Britain in OpenStreetMap: about {fmt(T["km"] / 1000, 1)} thousand kilometres of road. Then I measured how much of each county's A-road length runs along a Roman line.</p>'''

facts = f'''
      <div class="fact"><b>{fmt(T["share"])}%</b><span>of Britain's A-road length follows a Roman line: {fmt(T["roman_km"], 0)} km</span></div>
      <div class="fact"><b>{fmt(top["share"])}%</b><span>in {top["county"]}, the most Roman county, mostly the Fosse Way (A429) and the A38</span></div>
      <div class="fact"><b>{fmt(a5["roman_km"], 0)} km</b><span>of the <span class="sign">A5</span> runs on Watling Street, more than any other A-road</span></div>'''

road_rows = '\n'.join(
    f'<tr><td><span class="sign">{x["ref1"]}</span></td><td>{fmt(x["km"], 0)}</td><td>{fmt(x["roman_km"], 0)}</td><td>{fmt(x["share"], 0)}%</td></tr>'
    for x in roads[:12])
L = cty['Lancashire']
sens_rows = '\n'.join(
    f'<tr><td>{b} m</td><td>{fmt(S[b]["total"]["share"])}%</td><td>{fmt(S[b]["total"]["roman_km"], 0)}</td>'
    f'<td>{S[b]["counties"][0]["county"]}</td><td>{fmt({x["county"]: x for x in S[b]["counties"]}["Lancashire"]["share"])}%</td></tr>'
    for b in (20, 40, 80, 150))
cov_line = (f' Seen the other way round, {fmt(cov["share"], 0)}% of the {fmt(cov["roman_km"], 0)} km of Roman road that Itiner-e maps in Britain now lies under an A-road; for the main routes it is {fmt(cov["Main Road"]["share"], 0)}%.'
            if cov else '')

body = f'''
    <h2>Watling Street still leads</h2>
    <p>Measured in kilometres, no road is more Roman than the <span class="sign">A5</span>: {fmt(a5["roman_km"], 0)} km of it sits on Watling Street, the road from London to Wroxeter. The rest of the A5 continues to Holyhead on Thomas Telford's nineteenth-century line. Next come the <span class="sign">A46</span> on the Fosse Way, the <span class="sign">A38</span>, which follows Ryknild Street and the road south from Gloucester, and the <span class="sign">A66</span> over Stainmore. The roads with the highest share are shorter ones: in Cambridgeshire the <span class="sign">A1198</span> is Ermine Street for three quarters of its length.{cov_line}</p>
    <figure>
      <div class="tbl"><table>
        <thead><tr><th>Road</th><th>A-road km</th><th>On a Roman line, km</th><th>Share</th></tr></thead>
        <tbody>{road_rows}</tbody>
      </table></div>
      <figcaption>A-roads with the most length on a Roman line, Great Britain. Roads shorter than 20 km are left out.</figcaption>
    </figure>

    <h2>Every county</h2>
    <p>{top["county"]} leads at {fmt(top["share"])}%, followed by South Glamorgan, where the <span class="sign">A48</span> follows the Roman road west from Cardiff, then Cambridgeshire and Hertfordshire, which Ermine Street and Watling Street cross on their way north from London. England as a whole comes to {fmt(nat["England"]["share"])}% and Wales to {fmt(nat["Wales"]["share"])}%. Scotland manages {fmt(nat["Scotland"]["share"])}%: the Romans held most of it only briefly, and their roads there led to forts that were soon given up. Of the {len(R["counties"])} areas, {len(zero)} have no A-road on a Roman line at all; all but the Isle of Wight are in Scotland.</p>
    <div class="tbl"><table id="ctable">
      <thead><tr><th><button data-k="county">County</button></th><th class="l"><button data-k="nation">Nation</button></th><th><button data-k="km">A-road km</button></th><th><button data-k="roman_km">Roman km</button></th><th><button data-k="share">Share ▾</button></th></tr></thead>
      <tbody></tbody>
    </table></div>
    <p class="note">Click a column heading to sort.</p>

    <h2>Near Clitheroe: the road you can still see</h2>
    <p>Lancashire comes out at {fmt(L["share"])}%, below the English average. Most of that is the <span class="sign">A6</span> north of Preston, on the Roman road to Lancaster. The <span class="sign">A59</span> is a surprise: it follows a Roman line for about 1.5 km in Lancashire, near Worston, where it sits right on the road from Ribchester to Ilkley, and for about 16 km in North Yorkshire.</p>
    <p>East of Worston the Roman road leaves the modern one and climbs along the north side of Pendle Hill, past Downham towards Rimington. No modern road follows it there, but the ground remembers it. On the Environment Agency's lidar, which strips away trees and buildings, its raised bank shows as a long straight ridge across the fields.</p>
    <figure>
      <img src="img/downham-lidar.jpg" alt="Lidar hillshade of the fields between Worston and Downham, with a straight raised bank running diagonally between two dashed purple lines" style="width:100%;height:auto;display:block;border:1px solid var(--rule)">
      <figcaption>The Ribchester to Ilkley road near Downham, between the dashed lines. Bottom left, the A59 runs on the same line. Lidar hillshade © Environment Agency, Open Government Licence.</figcaption>
    </figure>
    <p>The Roman Roads Research Association's <a href="https://www.romanroads.org/gazetteer/M72a.htm">gazetteer entry for this road</a>, by David Ratledge, traces it field by field. Use the buttons beside the map to fly to Downham and three other places where the agger is clear on lidar.</p>

    <h2>A wrinkle in the data</h2>
    <p>On a first pass, the Roman roads in Itiner-e sat about 100 metres east of the modern roads that are known to follow them, such as the <span class="sign">A15</span> north of Lincoln and the <span class="sign">A429</span>. That is the size and direction of the gap between Britain's old OSGB36 map grid and the GPS system used by OpenStreetMap. Read as OSGB36 coordinates, the lines fall into place: the median gap between the A429 and the Fosse Way drops from 106 metres to 8. On the lidar they then sit on the surviving banks, as at Downham. All the figures here use the corrected lines.</p>

    <div class="method">
      <h3>How this was measured</h3>
      <ul>
        <li><b>Roman roads:</b> Itiner-e, static version 2024 (de Soto and others, 2025), {len(json.load(open("data/itinere_gb.geojson"))["features"]):,} road sections in Britain, corrected from OSGB36 to WGS84 as described above. Every British section in Itiner-e is marked "conjectured" or "hypothetical"; leaving out the hypothetical ones barely changes the results.</li>
        <li><b>A-roads:</b> every OpenStreetMap way tagged motorway, trunk or primary with an A-road number, including A(M) roads, downloaded on 26 October 2026. Dual carriageways are mapped as two one-way roads, so one-way roads count at half their length.</li>
        <li><b>Matching:</b> each A-road is cut into pieces of about 20 metres. A piece counts as Roman if it lies within 40 metres of an Itiner-e road and runs in the same direction, within 20 degrees, so roads that merely cross a Roman road are not counted. All lengths are measured on the British National Grid.</li>
        <li><b>Counties:</b> ceremonial counties in England, preserved counties in Wales and council areas in Scotland, built from ONS local authority boundaries.</li>
        <li><b>Limits:</b> Itiner-e maps the main Roman routes, not every local road, and many routes are conjectured. A modern road can also run close to a Roman one without being its successor.</li>
      </ul>
      <div class="tbl"><table>
        <thead><tr><th>Distance allowed</th><th>Great Britain</th><th>Roman km</th><th>Top county</th><th>Lancashire</th></tr></thead>
        <tbody>{sens_rows}</tbody>
      </table></div>
      <p style="margin:8px 0 0">The overall share depends on how close a road must be to count, but the ranking hardly moves.</p>
    </div>

    <h2>Sources</h2>
    <ul class="notes">
      <li>de Soto, P., Pažout, A., Brughmans, T. and others (2025). Itiner-e: a high-resolution dataset of roads of the Roman Empire. <i>Scientific Data</i>. Data: <a href="https://zenodo.org/records/17122148">Itiner-e static version 2024</a>, CC BY 4.0.</li>
      <li>Road data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>, Open Database Licence.</li>
      <li>Boundaries: Office for National Statistics, via <a href="https://github.com/onsvisual/uk-topojson">onsvisual/uk-topojson</a>. Contains OS data © Crown copyright and database right. Open Government Licence.</li>
      <li>Lidar: Environment Agency, <a href="https://environment.data.gov.uk/">LIDAR Composite DTM 1 m hillshade</a>, Open Government Licence.</li>
      <li>Roman Roads Research Association, <a href="https://www.romanroads.org/">romanroads.org</a>: gazetteer, lidar guides and the road-by-road story.</li>
      <li>Data and code for this post: <a href="https://github.com/Tristan-Hotham/how-roman-is-your-road">github.com/Tristan-Hotham/how-roman-is-your-road</a>.</li>
      <li>AI use: I wrote this post with drafting, data and coding help from Claude (Anthropic).</li>
    </ul>'''

og = f'{fmt(T["share"])}% of Britain\'s A-road length still follows a Roman line. Check your county.'
h = open('template.html').read()
h = (h.replace('{{INTRO}}', intro).replace('{{FACTS}}', facts).replace('{{BODY}}', body).replace('{{OG}}', og)
      .replace('{{RES}}', json.dumps(res, separators=(',', ':'))).replace('{{PLACES}}', json.dumps(places)))
open('index.html', 'w').write(h)
for f in os.listdir('map'): print(f, os.path.getsize('map/' + f))
print('index', len(h))

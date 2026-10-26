# How Roman is your road?

**Read the post and check your county:** https://tristan-hotham.github.io/how-roman-is-your-road/

What share of each county's A-road length still follows a Roman line? This post lays the Itiner-e atlas of Roman roads (2025) over every A-road in Great Britain in OpenStreetMap. A lidar layer shows where the old roads survive as earthworks.

## Headline results (40 m rule)

| | A-road km | On a Roman line | Share |
|---|---:|---:|---:|
| Great Britain | 46,684 | 2,346 km | 5.0% |
| England | 32,152 | 2,072 km | 6.5% |
| Wales | 4,168 | 202 km | 4.8% |
| Scotland | 10,364 | 72 km | 0.7% |

- The most Roman county is Gloucestershire, at 17.6%.
- The A-road with the most kilometres on a Roman line is the A5, with 135 km on Watling Street.
- Seen the other way round, 20% of the 11,578 km of Roman road in Itiner-e now lies under an A-road. For main routes the figure is 28%.

Full tables are in `results/`.

## A datum shift in Itiner-e's British roads

In Britain the Itiner-e lines sit about 100 m east of the modern roads known to follow them. Reading the coordinates as OSGB36 latitude and longitude (EPSG:4277) instead of WGS84 removes the offset. On the A429 (Fosse Way), for example, the median gap falls from 106 m to 8 m. On Environment Agency lidar the corrected lines sit on the surviving aggers, at Downham, Ackling Dyke and Stane Street. `analysis.py` applies this correction, and `results/itinere_gb_corrected.geojson` is the corrected file.

## Method

1. Each A-road is cut into pieces of about 20 m.
2. A piece counts as Roman if it lies within 40 m of an Itiner-e road and runs within 20 degrees of the same direction. This rule means crossings are not counted.
3. One-way OpenStreetMap ways count at half length, because dual carriageways are mapped twice.
4. All lengths are measured on the British National Grid.

Sensitivity runs at 20, 80 and 150 m are in `results/`. They change the overall share (3.7% to 6.6%) but hardly change the county ranking.

## Files

| Path | What it is |
|---|---|
| `data/itinere_gb.geojson` | Itiner-e static version 2024, Britain subset, coordinates as published (EPSG:3395 converted to longitude/latitude, no datum fix) |
| `data/osm_aroads.json.gz` | OpenStreetMap ways tagged motorway, trunk or primary with an A-road `ref`, downloaded 26 October 2026 via the Overpass API. Format: `[way id, ref, highway, oneway, name, [lon*1e5, lat*1e5, ...]]` |
| `data/counties.geojson` | Ceremonial counties (England), preserved counties (Wales) and council areas (Scotland), built by `counties.py` from ONS 2025 local authority boundaries (`data/ons/`, from onsvisual/uk-topojson) |
| `analysis.py` | Main analysis: `python3 analysis.py 40` (the buffer width in metres is the argument) |
| `roman_cov.py` | Reverse view: the share of Roman road length now under an A-road |
| `build.py`, `template.html` | Build `index.html` and the map layers in `map/` |
| `results/` | Results per buffer width, corrected Roman roads, and the A-road stretches on Roman lines |
| `img/downham-lidar.jpg` | Lidar hillshade near Downham, Lancashire, with the Ribchester to Ilkley road marked |

## Sources and licences

- **Roman roads:** de Soto, P., Pažout, A., Brughmans, T. and others (2025). *Itiner-e: a high-resolution dataset of roads of the Roman Empire.* Scientific Data. [Zenodo 17122148](https://zenodo.org/records/17122148). CC BY 4.0.
- **A-roads:** © OpenStreetMap contributors, ODbL.
- **Boundaries:** Office for National Statistics. Contains OS data © Crown copyright and database right. Open Government Licence v3.
- **Lidar:** Environment Agency LIDAR Composite DTM 1 m hillshade. Open Government Licence v3.
- **Further reading:** the Roman Roads Research Association gazetteer, https://www.romanroads.org/.

Code in this repository is MIT licensed. Derived data follow the licences of their sources; the A-road extract stays under the ODbL.

AI use: written with drafting, data and coding help from Claude (Anthropic).

Tristan Hotham, independent researcher, 2026.

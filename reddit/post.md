# Reddit post: How Roman is your road?

## Title

[OC] How Roman is your road? 5.0% of Great Britain's A-road length (2,346 of 46,684 km) still runs on a Roman road line; Gloucestershire leads at 17.6% and the A5 has 135 km on Watling Street

## Body (optional)

I laid the Itiner-e atlas of Roman roads over every A-road in Great Britain in OpenStreetMap and measured how much of each county's network still runs on a Roman line. A stretch counts if it lies within 40 m of a Roman road and runs on the same heading, so crossings are not counted. Overall it is 5.0%: 6.5% in England, 4.8% in Wales and 0.7% in Scotland. Gloucestershire is the most Roman county at 17.6%, mostly the Fosse Way (A429), and the A5 has more Roman kilometres than any other A-road. Caveat: every British route in Itiner-e is marked conjectured or hypothetical, and I had to correct a roughly 100 m datum shift in its British lines.

Interactive version: https://tristan-hotham.github.io/how-roman-is-your-road/

## Source comment

Source: Roman roads from Itiner-e, static version 2024 (de Soto, P., Pažout, A., Brughmans, T. and others, 2025, Itiner-e: a high-resolution dataset of roads of the Roman Empire, Scientific Data; Zenodo 17122148), CC BY 4.0, British lines corrected from OSGB36 to WGS84; A-roads from OpenStreetMap (motorway, trunk and primary ways with an A-road number, downloaded 26 October 2026), © OpenStreetMap contributors, ODbL; county boundaries from the Office for National Statistics 2025 local authority boundaries, contains OS data © Crown copyright and database right, Open Government Licence v3. Sensitivity runs at 20, 80 and 150 m give 3.7% to 6.6% overall with nearly the same county ranking.

Tools: Python (geopandas, shapely, pyproj, pandas, NumPy, matplotlib)

Interactive: https://tristan-hotham.github.io/how-roman-is-your-road/
Data and code: https://doi.org/10.5281/zenodo.23673516

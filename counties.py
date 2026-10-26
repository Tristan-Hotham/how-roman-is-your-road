"""Build ceremonial counties (England), preserved counties (Wales) and council areas (Scotland)
by dissolving ONS lower-tier local authorities (2025), from onsvisual/uk-topojson."""
import geopandas as gpd, pandas as pd
l = gpd.read_file('data/ons/ltla.geojson'); l = l[l['end'].isna()].copy()
cty = gpd.read_file('data/ons/cty.geojson'); cty = cty[cty['end'].isna()]
mc = gpd.read_file('data/ons/mcty.geojson'); mc = mc[mc['end'].isna()] if 'end' in mc else mc
E06 = {
 'Bath and North East Somerset':'Somerset','Bedford':'Bedfordshire','Blackburn with Darwen':'Lancashire','Blackpool':'Lancashire',
 'Bournemouth, Christchurch and Poole':'Dorset','Bracknell Forest':'Berkshire','Brighton and Hove':'East Sussex','Bristol, City of':'Bristol',
 'Buckinghamshire':'Buckinghamshire','Central Bedfordshire':'Bedfordshire','Cheshire East':'Cheshire','Cheshire West and Chester':'Cheshire',
 'Cornwall':'Cornwall','County Durham':'Durham','Cumberland':'Cumbria','Darlington':'Durham','Derby':'Derbyshire','Dorset':'Dorset',
 'East Riding of Yorkshire':'East Riding of Yorkshire','Halton':'Cheshire','Hartlepool':'Durham','Herefordshire, County of':'Herefordshire',
 'Isle of Wight':'Isle of Wight','Isles of Scilly':'Cornwall','Kingston upon Hull, City of':'East Riding of Yorkshire','Leicester':'Leicestershire',
 'Luton':'Bedfordshire','Medway':'Kent','Middlesbrough':'North Yorkshire','Milton Keynes':'Buckinghamshire','North East Lincolnshire':'Lincolnshire',
 'North Lincolnshire':'Lincolnshire','North Northamptonshire':'Northamptonshire','North Somerset':'Somerset','North Yorkshire':'North Yorkshire',
 'Northumberland':'Northumberland','Nottingham':'Nottinghamshire','Peterborough':'Cambridgeshire','Plymouth':'Devon','Portsmouth':'Hampshire',
 'Reading':'Berkshire','Redcar and Cleveland':'North Yorkshire','Rutland':'Rutland','Shropshire':'Shropshire','Slough':'Berkshire',
 'Somerset':'Somerset','South Gloucestershire':'Gloucestershire','Southampton':'Hampshire','Southend-on-Sea':'Essex','Stockton-on-Tees':'Durham',
 'Stoke-on-Trent':'Staffordshire','Swindon':'Wiltshire','Telford and Wrekin':'Shropshire','Thurrock':'Essex','Torbay':'Devon',
 'Warrington':'Cheshire','West Berkshire':'Berkshire','West Northamptonshire':'Northamptonshire','Westmorland and Furness':'Cumbria',
 'Wiltshire':'Wiltshire','Windsor and Maidenhead':'Berkshire','Wokingham':'Berkshire','York':'North Yorkshire'}
W06 = {'Isle of Anglesey':'Gwynedd','Gwynedd':'Gwynedd','Conwy':'Clwyd','Denbighshire':'Clwyd','Flintshire':'Clwyd','Wrexham':'Clwyd',
 'Powys':'Powys','Ceredigion':'Dyfed','Pembrokeshire':'Dyfed','Carmarthenshire':'Dyfed','Swansea':'West Glamorgan','Neath Port Talbot':'West Glamorgan',
 'Bridgend':'Mid Glamorgan','Rhondda Cynon Taf':'Mid Glamorgan','Merthyr Tydfil':'Mid Glamorgan','Caerphilly':'Gwent','Blaenau Gwent':'Gwent',
 'Torfaen':'Gwent','Monmouthshire':'Gwent','Newport':'Gwent','Vale of Glamorgan':'South Glamorgan','Cardiff':'South Glamorgan'}
pts = l.copy(); pts['geometry'] = l.representative_point()
def within(layer):
    j = gpd.sjoin(pts[['areacd','geometry']], layer[['areanm','geometry']].rename(columns={'areanm':'up'}), predicate='within')
    return dict(zip(j.areacd, j.up))
c1, c2 = within(cty), within(mc)
def county(r):
    p = r.areacd[:3]
    if p == 'E07': return c1[r.areacd]
    if p == 'E08': return c2[r.areacd]
    if p == 'E09': return 'Greater London'
    if p == 'E06': return E06[r.areanm]
    if p == 'W06': return W06[r.areanm]
    if p == 'S12': return r.areanm
    return None
l['geometry'] = l.geometry.make_valid()
l['county'] = l.apply(county, axis=1)
l['nation'] = l.areacd.str[0].map({'E':'England','W':'Wales','S':'Scotland','N':'Northern Ireland'})
l = l[l.nation != 'Northern Ireland']
c = l.dissolve(by=['county','nation'], as_index=False)[['county','nation','geometry']]
c.to_file('data/counties.geojson', driver='GeoJSON')
print(len(c), c.nation.value_counts().to_dict())
print(sorted(c[c.nation=='England'].county))

"""Builds index.html for BU SoundScape.  python build_site.py
Reads the same CSV + GeoJSON as the map; every chart is computed in the browser from this data,
so update the CSV, re-run, and all numbers/graphs/rankings change."""
import json, os, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); P = lambda f: os.path.join(HERE, f)
DATA_FILE = 'NoiseDataAvg.csv'
MAP_FILE = 'noise_map.html'
STUDY_CATEGORIES = ['Academic', 'Silence Zone', 'Administrative']   # zone categories counted as study places
d = pd.read_csv(P(DATA_FILE), encoding='utf-8-sig')
g = json.load(open(P('zones.geojson'), encoding='utf-8'))
cat = {f['properties']['zone_name'].replace('<br>', ' ').strip(): f['properties'].get('zone_category', 'Other') for f in g['features']}
rows = [[r.zone, r.time_slot, round(float(r.decibels), 1), r.point_id] for r in d.itertuples()]
payload = json.dumps(dict(rows=rows, cat=cat, study=STUDY_CATEGORIES))
html = open(P('site_template.html'), encoding='utf-8').read().replace('__DATA__', payload).replace('__MAP__', MAP_FILE)
open(P('index.html'), 'w', encoding='utf-8').write(html); print('Saved index.html |', len(rows), 'rows')

import csv
import json
import glob
import os

print("--- CSV FILES ---")
for f in glob.glob('*.csv'):
    print(f"\nFile: {f}")
    with open(f, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader, None)
        first_row = next(reader, None)
        print(f"Headers: {headers}")
        print(f"First Row: {first_row}")

print("\n--- GEOJSON FILE ---")
geojson_file = 'india_district.geojson'
if os.path.exists(geojson_file):
    with open(geojson_file, 'r', encoding='utf-8') as gfile:
        data = json.load(gfile)
        if 'features' in data and len(data['features']) > 0:
            print("Feature properties:")
            print(data['features'][0]['properties'])
        else:
            print("No features found or invalid GeoJSON")
else:
    print("GeoJSON not found")

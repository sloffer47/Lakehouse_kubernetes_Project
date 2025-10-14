import json

print("🧹 Silver: Nettoyage...")

with open('/data/bronze/vehicles/data.json', 'r') as f:
    data = json.load(f)

cleaned = []
for row in data:
    if (0 <= row.get('battery', -1) <= 100 and
        -90 <= row.get('latitude', -999) <= 90 and
        -180 <= row.get('longitude', -999) <= 180 and
        row.get('vehicleId')):
        cleaned.append(row)

print(f"✓ Bronze: {len(data)} lignes")
print(f"✓ Silver: {len(cleaned)} lignes")

import os
os.makedirs('/data/silver/vehicles', exist_ok=True)
with open('/data/silver/vehicles/data.json', 'w') as f:
    json.dump(cleaned, f, indent=2)

print("✅ Silver complété")
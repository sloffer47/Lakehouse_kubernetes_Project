import json
import os
import time

print("📈 Gold: Attente de Silver...")

# Attends que Silver termine
for i in range(10):
    if os.path.exists('/data/silver/vehicles/data.json'):
        break
    print(f"  Attente {i+1}/10...")
    time.sleep(3)

if not os.path.exists('/data/silver/vehicles/data.json'):
    print("❌ Silver pas prêt")
    exit(1)

print("✓ Silver trouvé")

with open('/data/silver/vehicles/data.json', 'r') as f:
    data = json.load(f)

from collections import defaultdict
stats = defaultdict(lambda: {'total': 0, 'batteries': []})

for row in data:
    t = row['type']
    stats[t]['total'] += 1
    stats[t]['batteries'].append(row['battery'])

results = []
for vehicle_type, values in stats.items():
    results.append({
        'type': vehicle_type,
        'total': values['total'],
        'avg_battery': round(sum(values['batteries']) / len(values['batteries']), 1)
    })

print("\n📊 RÉSULTATS FINAUX:")
for r in results:
    print(f"  ✓ {r['type']}: {r['total']} véhicules, {r['avg_battery']}% batterie")

os.makedirs('/data/gold/stats', exist_ok=True)
with open('/data/gold/stats/results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n✅ PIPELINE TERMINÉ!")
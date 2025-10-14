import json
from kafka import KafkaConsumer

print("📥 Bronze: Lecture Kafka...")

consumer = KafkaConsumer(
    'vehicles-events',
    bootstrap_servers=['kafka:9092'],
    auto_offset_reset='earliest',
    consumer_timeout_ms=10000,  # Timeout 10 sec
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

messages = []
for msg in consumer:
    messages.append(msg.value)
    print(f"✓ Message {len(messages)}")
    if len(messages) >= 30:
        break

print(f"Total: {len(messages)} messages")

import os
os.makedirs('/data/bronze/vehicles', exist_ok=True)
with open('/data/bronze/vehicles/data.json', 'w') as f:
    json.dump(messages, f, indent=2)

print("✅ Bronze terminé")
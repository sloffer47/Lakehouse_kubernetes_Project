# Data Lakehouse Migration vers Kubernetes

Architecture complète pour migrer un pipeline data de Docker Compose vers Kubernetes.

## 📊 Architecture

```
┌─────────────────────────────────────────────┐
│       KUBERNETES CLUSTER                    │
├─────────────────────────────────────────────┤
│                                             │
│  1. KAFKA (Message Broker)                  │
│     ├── Kafka Broker (Port 9092)            │
│     └── Zookeeper (Port 2181)               │
│                                             │
│  2. PRODUCER (Générateur de données)        │
│     └── Job Kubernetes                      │
│                                             │
│  3. SPARK JOBS (Traitement)                 │
│     ├── Bronze (Données brutes)             │
│     ├── Silver (Données nettoyées)          │
│     └── Gold (Statistiques)                 │
│                                             │
│  4. STORAGE (Données persistantes)          │
│     └── PersistentVolume                    │
│                                             │
└─────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Prérequis
- Kubernetes (Docker Desktop, Minikube, Kind)
- kubectl configuré
- Maven (pour compiler le Producer)
- Docker Desktop / Docker CLI

### 2. Structure du Projet

```
lakehouse-kubernetes-project/
├── producer/              # Code Java du Producer
│   ├── Producer.java      # Source
│   ├── pom.xml           # Dépendances Maven
│   └── Dockerfile        # Build Docker
├── spark-jobs/            # Jobs Spark (Python)
│   ├── bronze.py         # Lecture Kafka
│   ├── silver.py         # Nettoyage
│   └── gold.py           # Agrégations
├── kubernetes/            # Configuration K8s
│   ├── namespace.yaml     # Namespace
│   ├── kafka-deployment.yaml
│   ├── topic-creation.yaml
│   ├── producer-job.yaml
│   ├── storage.yaml
│   └── spark-jobs.yaml
└── README.md             # Ce fichier
```

### 3. Étapes de Déploiement

#### Étape 1 : Créer le namespace
```bash
kubectl apply -f kubernetes/namespace.yaml
```

#### Étape 2 : Déployer Kafka
```bash
kubectl apply -f kubernetes/kafka-deployment.yaml
kubectl apply -f kubernetes/topic-creation.yaml

# Attends que les pods soient Running
kubectl get pods -n lakehouse -w
```

#### Étape 3 : Builder l'image Docker du Producer
```bash
cd producer
docker build -t producer:1.0 .
cd ..
```

#### Étape 4 : Déployer le Producer
```bash
kubectl apply -f kubernetes/producer-job.yaml

# Vérifie que le job s'exécute
kubectl get jobs -n lakehouse -w
```

#### Étape 5 : Vérifier les données dans Kafka
```bash
kubectl run -it --rm --restart=Never \
  --image=confluentinc/cp-kafka:7.4.0 \
  -n lakehouse test \
  -- kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic vehicles-events \
  --max-messages 5
```

#### Étape 6 : Déployer les jobs Spark
```bash
# D'abord, créer une ConfigMap avec les scripts Spark
kubectl create configmap spark-scripts \
  --from-file=spark-jobs/ \
  -n lakehouse

# Puis déployer les jobs
kubectl apply -f kubernetes/spark-jobs.yaml
```

### 4. Monitoring

```bash
# Voir tous les pods
kubectl get pods -n lakehouse

# Voir les logs d'un pod
kubectl logs -n lakehouse <pod-name>

# Voir les jobs
kubectl get jobs -n lakehouse

# Décrire une ressource
kubectl describe pod -n lakehouse <pod-name>
```

### 5. Nettoyage

```bash
# Supprimer tout
kubectl delete namespace lakehouse
```

## 📈 Flux de Données

1. **Producer** → Génère 30 événements GPS
2. **Kafka** → Stocke les événements
3. **Bronze** → Lit Kafka, écrit Parquet brut
4. **Silver** → Valide les données, filtre
5. **Gold** → Agrège par type de véhicule

## 🔧 Configuration

### Variables d'environnement

#### Producer
```
KAFKA_BOOTSTRAP_SERVER=kafka:9092  # URL Kafka
```

### Ressources Kubernetes

- **CPU Request**: 100m - 500m
- **Memory Request**: 256Mi - 1Gi
- **Storage**: 10Gi

## 📝 Exemple de Message Kafka

```json
{
  "vehicleId": "CAR_000",
  "type": "car",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "battery": 75,
  "timestamp": 1697203200000
}
```

## 🎯 Résultats Attendus

### Bronze
- Lit les événements Kafka
- Écrit `/data/bronze/vehicles/part-*.parquet`
- 30 lignes minimum

### Silver
- Valide batterie (0-100)
- Valide coordonnées (lat: -90 à 90, lon: -180 à 180)
- Écrit `/data/silver/vehicles/part-*.parquet`
- ~28-30 lignes (après filtrage)

### Gold
- Agrège par type (car, bike, scooter)
- Calcule moyennes et min/max
- Écrit `/data/gold/stats/part-*.parquet`
- 3 lignes (une par type)

## 🐛 Troubleshooting

### Le Producer n'envoie pas de messages
```bash
# Vérifier que Kafka est accessible
kubectl exec -it kafka-xxx -n lakehouse -- \
  kafka-broker-api-versions --bootstrap-server localhost:9092
```

### Les Spark jobs ne trouvent pas les données
```bash
# Vérifier le PersistentVolume
kubectl get pv
kubectl describe pv data-pv

# Vérifier le PersistentVolumeClaim
kubectl get pvc -n lakehouse
```

### Pas de messages dans Kafka
```bash
# Regarde les logs du Producer
kubectl logs -n lakehouse job/producer-job

# Regarde les logs de Kafka
kubectl logs -n lakehouse kafka-xxx
```

## 📚 Ressources

- [Kafka Documentation](https://kafka.apache.org/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Spark Documentation](https://spark.apache.org/)

---

**Créé avec ❤️ pour la migration Kubernetes**

#!/usr/bin/env python3
"""
Setup.py - Générateur de Projet Data Lakehouse Kubernetes
Crée une structure complète avec tous les fichiers nécessaires
"""

import os
import sys
from pathlib import Path

def create_directory(path):
    """Crée un répertoire s'il n'existe pas"""
    Path(path).mkdir(parents=True, exist_ok=True)
    print(f"✓ Créé: {path}")

def create_file(path, content):
    """Crée un fichier avec le contenu spécifié"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Fichier: {path}")

def main():
    # Chemin du projet
    project_root = Path("C:/lakehouse-kubernetes-project")
    
    if project_root.exists():
        response = input(f"Le dossier {project_root} existe déjà. Continuer ? (y/n): ")
        if response.lower() != 'y':
            print("Annulé.")
            return
    
    print("\n🚀 Génération du projet Data Lakehouse Kubernetes...\n")
    
    # Créer la structure de dossiers
    dirs = [
        project_root,
        project_root / "producer",
        project_root / "spark-jobs",
        project_root / "kubernetes",
        project_root / "docs",
    ]
    
    for dir_path in dirs:
        create_directory(dir_path)
    
    # ==================== FICHIERS PRODUCER JAVA ====================
    
    create_file(
        project_root / "producer" / "Producer.java",
        '''import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerRecord;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.*;

/**
 * Producer Java pour Kafka
 * Génère 30 événements GPS simulés toutes les 3 secondes
 * Envoie les messages au topic "vehicles-events"
 */
public class Producer {
    public static void main(String[] args) throws Exception {
        // Configuration du producteur Kafka
        Properties props = new Properties();
        props.put("bootstrap.servers", System.getenv("KAFKA_BOOTSTRAP_SERVER"));
        props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("acks", "all");
        props.put("retries", "3");
        
        KafkaProducer<String, String> producer = new KafkaProducer<>(props);
        ObjectMapper mapper = new ObjectMapper();
        Random random = new Random();
        
        String[] types = {"car", "bike", "scooter"};
        
        System.out.println("📍 Démarrage du Producer...");
        System.out.println("🎯 Cible: " + props.getProperty("bootstrap.servers"));
        
        // Génère 30 événements
        for (int i = 0; i < 30; i++) {
            Map<String, Object> event = new HashMap<>();
            String type = types[i % 3];
            
            event.put("vehicleId", type.toUpperCase() + "_" + String.format("%03d", i));
            event.put("type", type);
            event.put("latitude", 48.8566 + (random.nextDouble() - 0.5) * 0.1);
            event.put("longitude", 2.3522 + (random.nextDouble() - 0.5) * 0.1);
            event.put("battery", 50 + random.nextInt(51));
            event.put("timestamp", System.currentTimeMillis());
            
            String json = mapper.writeValueAsString(event);
            producer.send(new ProducerRecord<>("vehicles-events", json));
            System.out.println("✓ Event " + (i+1) + "/30: " + json);
        }
        
        producer.flush();
        producer.close();
        System.out.println("✅ 30 événements envoyés à Kafka");
    }
}
'''
    )
    
    create_file(
        project_root / "producer" / "pom.xml",
        '''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.kafka</groupId>
  <artifactId>producer</artifactId>
  <version>1.0</version>
  <packaging>jar</packaging>
  
  <!-- Dépendances pour Kafka et JSON -->
  <dependencies>
    <!-- Kafka Client -->
    <dependency>
      <groupId>org.apache.kafka</groupId>
      <artifactId>kafka-clients</artifactId>
      <version>3.4.0</version>
    </dependency>
    
    <!-- Jackson pour JSON -->
    <dependency>
      <groupId>com.fasterxml.jackson.core</groupId>
      <artifactId>jackson-databind</artifactId>
      <version>2.14.0</version>
    </dependency>
  </dependencies>

  <build>
    <plugins>
      <!-- Maven Shade Plugin pour créer un FAT JAR -->
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-shade-plugin</artifactId>
        <version>3.2.4</version>
        <executions>
          <execution>
            <phase>package</phase>
            <goals>
              <goal>shade</goal>
            </goals>
            <configuration>
              <transformers>
                <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                  <mainClass>Producer</mainClass>
                </transformer>
              </transformers>
              <outputFile>${project.build.directory}/${project.artifactId}-${project.version}-fat.jar</outputFile>
            </configuration>
          </execution>
        </executions>
      </plugin>
    </plugins>
  </build>
</project>
'''
    )
    
    create_file(
        project_root / "producer" / "Dockerfile",
        '''# Stage 1: Build avec Maven
FROM maven:3.8.1-openjdk-11 AS builder
WORKDIR /app

# Copie et compile
COPY pom.xml .
RUN mvn dependency:resolve

COPY Producer.java .
RUN mvn clean package -DskipTests

# Stage 2: Runtime
FROM openjdk:11-jre-slim
WORKDIR /app

# Copie le JAR depuis le builder
COPY --from=builder /app/target/producer-1.0-fat.jar .

# Variable d'environnement pour Kafka
ENV KAFKA_BOOTSTRAP_SERVER=kafka:9092

# Lance le Producer
CMD ["java", "-jar", "producer-1.0-fat.jar"]
'''
    )
    
    # ==================== FICHIERS SPARK ====================
    
    create_file(
        project_root / "spark-jobs" / "bronze.py",
        '''"""
Bronze Layer - Lecture depuis Kafka
Lit les événements bruts depuis Kafka et les écrit en Parquet
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, schema_of_json

def main():
    # Création de la session Spark
    spark = SparkSession.builder \\
        .appName("bronze-layer") \\
        .getOrCreate()
    
    # Schéma JSON des événements
    schema = "vehicleId STRING, type STRING, latitude DOUBLE, longitude DOUBLE, battery INT, timestamp LONG"
    
    # Lecture streaming depuis Kafka
    df = spark.readStream \\
        .format("kafka") \\
        .option("kafka.bootstrap.servers", "kafka:9092") \\
        .option("subscribe", "vehicles-events") \\
        .option("startingOffsets", "earliest") \\
        .load()
    
    print("📥 Bronze: Lecture depuis Kafka...")
    
    # Parse JSON et sélectionne les colonnes
    parsed_df = df.select(
        from_json(col("value"), schema).alias("data")
    ).select("data.*")
    
    # Écriture en Parquet (streaming)
    query = parsed_df.writeStream \\
        .format("parquet") \\
        .option("path", "/data/bronze/vehicles") \\
        .option("checkpointLocation", "/data/bronze/checkpoint") \\
        .start()
    
    # Attends 60 secondes puis arrête
    query.awaitTermination(60000)
    print("✅ Bronze complété")

if __name__ == "__main__":
    main()
'''
    )
    
    create_file(
        project_root / "spark-jobs" / "silver.py",
        '''"""
Silver Layer - Nettoyage et validation
Filtre les données invalides (batterie, coordonnées)
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json

def main():
    spark = SparkSession.builder \\
        .appName("silver-layer") \\
        .getOrCreate()
    
    print("🧹 Silver: Nettoyage des données...")
    
    # Lecture des données Bronze
    df = spark.read.parquet("/data/bronze/vehicles")
    
    # Parse JSON
    schema = "vehicleId STRING, type STRING, latitude DOUBLE, longitude DOUBLE, battery INT, timestamp LONG"
    parsed = df.select(from_json(col("value"), schema).alias("data")).select("data.*")
    
    # Filtres de validation
    cleaned = parsed \\
        .filter(col("battery").between(0, 100)) \\
        .filter(col("latitude").between(-90, 90)) \\
        .filter(col("longitude").between(-180, 180)) \\
        .filter(col("vehicleId").isNotNull()) \\
        .filter(col("type").isin("car", "bike", "scooter"))
    
    count_before = parsed.count()
    count_after = cleaned.count()
    
    print(f"📊 Bronze: {count_before} lignes")
    print(f"✓ Silver: {count_after} lignes (${count_before - count_after} rejetées)")
    
    # Écriture en Parquet
    cleaned.write.mode("overwrite").parquet("/data/silver/vehicles")
    print("✅ Silver complété")

if __name__ == "__main__":
    main()
'''
    )
    
    create_file(
        project_root / "spark-jobs" / "gold.py",
        '''"""
Gold Layer - Agrégations et statistiques
Génère les statistiques finales par type de véhicule
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg, min, max

def main():
    spark = SparkSession.builder \\
        .appName("gold-layer") \\
        .getOrCreate()
    
    print("📈 Gold: Agrégation des données...")
    
    # Lecture des données Silver
    df = spark.read.parquet("/data/silver/vehicles")
    
    # Agrégations
    stats = df.groupBy("type").agg(
        count("*").alias("total"),
        avg("battery").alias("avg_battery"),
        min("latitude").alias("min_lat"),
        max("latitude").alias("max_lat"),
        min("longitude").alias("min_lon"),
        max("longitude").alias("max_lon")
    )
    
    # Affiche les résultats
    print("\\n📊 Statistiques finales:")
    stats.show()
    
    # Écriture en Parquet
    stats.write.mode("overwrite").parquet("/data/gold/stats")
    print("✅ Gold complété")

if __name__ == "__main__":
    main()
'''
    )
    
    # ==================== FICHIERS KUBERNETES ====================
    
    create_file(
        project_root / "kubernetes" / "namespace.yaml",
        '''# Crée le namespace pour isoler le projet
apiVersion: v1
kind: Namespace
metadata:
  name: lakehouse
  labels:
    name: lakehouse
'''
    )
    
    create_file(
        project_root / "kubernetes" / "kafka-deployment.yaml",
        '''# Déploiement Kafka et Zookeeper
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zookeeper
  namespace: lakehouse
spec:
  replicas: 1
  selector:
    matchLabels:
      app: zookeeper
  template:
    metadata:
      labels:
        app: zookeeper
    spec:
      containers:
      - name: zookeeper
        image: confluentinc/cp-zookeeper:7.4.0
        ports:
        - containerPort: 2181
        env:
        - name: ZOOKEEPER_CLIENT_PORT
          value: "2181"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kafka
  namespace: lakehouse
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kafka
  template:
    metadata:
      labels:
        app: kafka
    spec:
      containers:
      - name: kafka
        image: confluentinc/cp-kafka:7.4.0
        ports:
        - containerPort: 9092
        env:
        - name: KAFKA_BROKER_ID
          value: "1"
        - name: KAFKA_ZOOKEEPER_CONNECT
          value: "zookeeper:2181"
        - name: KAFKA_ADVERTISED_LISTENERS
          value: "PLAINTEXT://kafka:9092"
        - name: KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR
          value: "1"

---
apiVersion: v1
kind: Service
metadata:
  name: kafka
  namespace: lakehouse
spec:
  selector:
    app: kafka
  ports:
  - port: 9092
    targetPort: 9092
  clusterIP: None

---
apiVersion: v1
kind: Service
metadata:
  name: zookeeper
  namespace: lakehouse
spec:
  selector:
    app: zookeeper
  ports:
  - port: 2181
    targetPort: 2181
  clusterIP: None
'''
    )
    
    create_file(
        project_root / "kubernetes" / "topic-creation.yaml",
        '''apiVersion: batch/v1
kind: Job
metadata:
  name: create-topics
  namespace: lakehouse
spec:
  ttlSecondsAfterFinished: 3600
  template:
    spec:
      containers:
      - name: kafka-topic-creator
        image: confluentinc/cp-kafka:7.4.0
        command:
        - sh
        - -c
        - |
          sleep 20
          kafka-topics --create --bootstrap-server kafka:9092 --topic vehicles-events --partitions 1 --replication-factor 1 --if-not-exists
          echo "Topic created successfully"
      restartPolicy: Never
  backoffLimit: 3
'''
    )
    
    create_file(
        project_root / "kubernetes" / "producer-job.yaml",
        '''# Job Kubernetes pour le Producer
apiVersion: batch/v1
kind: Job
metadata:
  name: producer-job
  namespace: lakehouse
spec:
  template:
    spec:
      containers:
      - name: producer
        image: producer:1.0
        imagePullPolicy: Never
        env:
        - name: KAFKA_BOOTSTRAP_SERVER
          value: "kafka:9092"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
      restartPolicy: Never
  backoffLimit: 3
'''
    )
    
    create_file(
        project_root / "kubernetes" / "storage.yaml",
        '''# PersistentVolume et PersistentVolumeClaim pour Spark
apiVersion: v1
kind: PersistentVolume
metadata:
  name: data-pv
  namespace: lakehouse
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: "/data/lakehouse"

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
  namespace: lakehouse
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
'''
    )
    
    create_file(
        project_root / "kubernetes" / "spark-jobs.yaml",
        '''# Jobs Spark pour Bronze, Silver, Gold
apiVersion: batch/v1
kind: Job
metadata:
  name: bronze-job
  namespace: lakehouse
spec:
  template:
    spec:
      containers:
      - name: spark
        image: apache/spark:3.3.0
        command: ["spark-submit", "--master", "local[2]", "--deploy-mode", "client"]
        args: ["/scripts/bronze.py"]
        volumeMounts:
        - name: scripts
          mountPath: /scripts
        - name: data
          mountPath: /data
      volumes:
      - name: scripts
        configMap:
          name: spark-scripts
      - name: data
        persistentVolumeClaim:
          claimName: data-pvc
      restartPolicy: Never
  backoffLimit: 1

---
apiVersion: batch/v1
kind: Job
metadata:
  name: silver-job
  namespace: lakehouse
spec:
  template:
    spec:
      containers:
      - name: spark
        image: apache/spark:3.3.0
        command: ["spark-submit", "--master", "local[2]", "--deploy-mode", "client"]
        args: ["/scripts/silver.py"]
        volumeMounts:
        - name: scripts
          mountPath: /scripts
        - name: data
          mountPath: /data
      volumes:
      - name: scripts
        configMap:
          name: spark-scripts
      - name: data
        persistentVolumeClaim:
          claimName: data-pvc
      restartPolicy: Never
  backoffLimit: 1

---
apiVersion: batch/v1
kind: Job
metadata:
  name: gold-job
  namespace: lakehouse
spec:
  template:
    spec:
      containers:
      - name: spark
        image: apache/spark:3.3.0
        command: ["spark-submit", "--master", "local[2]", "--deploy-mode", "client"]
        args: ["/scripts/gold.py"]
        volumeMounts:
        - name: scripts
          mountPath: /scripts
        - name: data
          mountPath: /data
      volumes:
      - name: scripts
        configMap:
          name: spark-scripts
      - name: data
        persistentVolumeClaim:
          claimName: data-pvc
      restartPolicy: Never
  backoffLimit: 1
'''
    )
    
    # ==================== README ====================
    
    create_file(
        project_root / "README.md",
        '''# Data Lakehouse Migration vers Kubernetes

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
kubectl run -it --rm --restart=Never \\
  --image=confluentinc/cp-kafka:7.4.0 \\
  -n lakehouse test \\
  -- kafka-console-consumer \\
  --bootstrap-server kafka:9092 \\
  --topic vehicles-events \\
  --max-messages 5
```

#### Étape 6 : Déployer les jobs Spark
```bash
# D'abord, créer une ConfigMap avec les scripts Spark
kubectl create configmap spark-scripts \\
  --from-file=spark-jobs/ \\
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
kubectl exec -it kafka-xxx -n lakehouse -- \\
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
'''
    )
    
    # ==================== BUILD SCRIPT ====================
    
    create_file(
        project_root / "build.sh",
        '''#!/bin/bash
# Script de build pour le projet Kubernetes

echo "🚀 Build du projet Lakehouse Kubernetes"

# 1. Build le Producer
echo "\\n📦 Build du Producer..."
cd producer
mvn clean package -DskipTests
if [ $? -eq 0 ]; then
    echo "✓ Producer compilé"
    docker build -t producer:1.0 .
    echo "✓ Image Docker créée"
else
    echo "❌ Erreur lors du build du Producer"
    exit 1
fi
cd ..

# 2. Créer le namespace
echo "\\n🏗️  Création du namespace..."
kubectl create namespace lakehouse --dry-run=client -o yaml | kubectl apply -f -

# 3. Déployer Kafka
echo "\\n🔌 Déploiement de Kafka..."
kubectl apply -f kubernetes/kafka-deployment.yaml
kubectl apply -f kubernetes/topic-creation.yaml

# 4. Attendre que Kafka soit prêt
echo "\\n⏳ Attente de Kafka..."
sleep 30

# 5. Déployer le Producer
echo "\\n📤 Déploiement du Producer..."
kubectl apply -f kubernetes/producer-job.yaml

echo "\\n✅ Build complète!"
echo "Commandes utiles:"
echo "  kubectl get pods -n lakehouse -w       # Voir les pods"
echo "  kubectl logs -n lakehouse <pod>        # Voir les logs"
echo "  kubectl delete namespace lakehouse     # Nettoyer"
'''
    )
    
    print("\n" + "="*60)
    print("✅ PROJET CRÉÉ AVEC SUCCÈS!")
    print("="*60)
    print(f"\n📁 Localisation: {project_root}")
    print("\n📋 Fichiers créés:")
    print("  ✓ Producer Java (avec Maven)")
    print("  ✓ Jobs Spark Python (Bronze/Silver/Gold)")
    print("  ✓ Configuration Kubernetes YAML")
    print("  ✓ README complet")
    print("  ✓ Build script")
    print("\n🚀 Prochaines étapes:")
    print("  1. cd C:/lakehouse-kubernetes-project")
    print("  2. mvn -v  # Vérifier Maven")
    print("  3. docker build -t producer:1.0 producer/")
    print("  4. kubectl create namespace lakehouse")
    print("  5. kubectl apply -f kubernetes/")
    print("\n💡 Besoin d'aide?")
    print("  - Lire le README.md")
    print("  - Vérifier les YAML")
    print("  - Voir les logs avec kubectl logs")

if __name__ == "__main__":
    main()
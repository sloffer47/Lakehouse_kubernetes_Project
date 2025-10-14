#!/bin/bash
# Script de build pour le projet Kubernetes

echo "🚀 Build du projet Lakehouse Kubernetes"

# 1. Build le Producer
echo "\n📦 Build du Producer..."
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
echo "\n🏗️  Création du namespace..."
kubectl create namespace lakehouse --dry-run=client -o yaml | kubectl apply -f -

# 3. Déployer Kafka
echo "\n🔌 Déploiement de Kafka..."
kubectl apply -f kubernetes/kafka-deployment.yaml
kubectl apply -f kubernetes/topic-creation.yaml

# 4. Attendre que Kafka soit prêt
echo "\n⏳ Attente de Kafka..."
sleep 30

# 5. Déployer le Producer
echo "\n📤 Déploiement du Producer..."
kubectl apply -f kubernetes/producer-job.yaml

echo "\n✅ Build complète!"
echo "Commandes utiles:"
echo "  kubectl get pods -n lakehouse -w       # Voir les pods"
echo "  kubectl logs -n lakehouse <pod>        # Voir les logs"
echo "  kubectl delete namespace lakehouse     # Nettoyer"

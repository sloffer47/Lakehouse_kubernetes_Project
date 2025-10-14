# Stage 1: Build avec Maven
FROM maven:3.8.1-openjdk-11 AS builder
WORKDIR /app

# Copie les fichiers
COPY pom.xml .
COPY Producer.java .

# Compile (le JAR sera dans target/)
RUN mvn clean package -DskipTests

# Stage 2: Runtime
FROM openjdk:11-jre-slim
WORKDIR /app

# Copie le FAT JAR
COPY --from=builder /app/target/producer-1.0-fat.jar app.jar

# Variable d'environnement
ENV KAFKA_BOOTSTRAP_SERVER=kafka:9092

# Lance avec le bon JAR
CMD ["java", "-jar", "app.jar"]
// SUPPRIME le "package" s'il existe et commence directement par:

import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerRecord;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.*;

public class Producer {
    public static void main(String[] args) throws Exception {
        Properties props = new Properties();
        String kafkaServer = System.getenv("KAFKA_BOOTSTRAP_SERVER");
        if (kafkaServer == null)
            kafkaServer = "kafka:9092";

        props.put("bootstrap.servers", kafkaServer);
        props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("acks", "all");

        KafkaProducer<String, String> producer = new KafkaProducer<>(props);
        ObjectMapper mapper = new ObjectMapper();
        Random random = new Random();

        String[] types = { "car", "bike", "scooter" };

        System.out.println("📍 Producer démarré - Envoi à: " + kafkaServer);

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
            System.out.println("✓ [" + (i + 1) + "/30] " + event.get("vehicleId"));
            Thread.sleep(100);
        }

        producer.flush();
        producer.close();
        System.out.println("✅ TERMINÉ - 30 événements envoyés");
        System.exit(0);
    }
}
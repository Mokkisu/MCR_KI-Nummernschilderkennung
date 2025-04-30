#include "mqtt_handler.h"
#include <WiFi.h>
#include <PubSubClient.h>

// MQTT-Konfiguration
const char* mqtt_server = "172.5.232.150";  // IP-Adresse des MQTT-Brokers
const int mqtt_port = 1883;
const char* mqtt_topic = "parkhaus/status";

WiFiClient espClient;
PubSubClient client(espClient);

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.println("Verbinde mit MQTT...");
    String clientId = "mqttx_8823d287";
    clientId += String(random(0xffff), HEX);
    if (client.connect(clientId.c_str())) {
      Serial.println("MQTT verbunden");
      // Erneutes Abonnieren der Topics nach Wiederverbindung
      client.subscribe("erlaubnis/");
    } else {
      Serial.print("Fehlgeschlagen, rc=");
      Serial.print(client.state());
      Serial.println(" versuche erneut in 5s...");
      delay(5000);
    }
  }
}

void mqtt_setup() {
  client.setServer(mqtt_server, mqtt_port);
}

void mqtt_loop() {
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();
}

void mqtt_sendeStatus(int fahrzeuge, int maxFahrzeuge) {
  if (!client.connected()) {
    Serial.println("MQTT nicht verbunden, versuche erneut zu verbinden...");
    reconnectMQTT();
  }

  String status = (fahrzeuge >= maxFahrzeuge) ? "VOLL" : "FREI";
  String payload = "Geparkt " + String(fahrzeuge) + "/" + String(maxFahrzeuge) + ", Status: " + status;

  if (client.publish(mqtt_topic, payload.c_str())) {
    Serial.println("MQTT gesendet: " + payload);
  } else {
    Serial.println("MQTT senden fehlgeschlagen");
  }

  delay(1000);
}

void mqtt_setCallback(void (*callback)(char*, byte*, unsigned int)) {
  client.setCallback(callback);
}

void mqtt_subscribe(const char* topic) {
  if (client.connected()) {
    client.subscribe(topic);
    Serial.println("Abonniert: " + String(topic));
  } else {
    Serial.println("Nicht verbunden, kann nicht abonnieren: " + String(topic));
  }
}
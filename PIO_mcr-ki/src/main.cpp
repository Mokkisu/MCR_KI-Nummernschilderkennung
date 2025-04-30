//main.cpp
#include <Wire.h>
#include <Arduino.h>
#include <ESP32Servo.h>
#include <LiquidCrystal_I2C.h>
#include <WiFi.h>
#include <time.h>
#include "lcd1602.h"
#include "mqtt_handler.h"

// === Konfiguration ===
#define DEBUG true
const char* ssid = "SCHB001";
const char* password = "schb001!";

// Zeitzone (für Mitteleuropa inkl. Sommerzeit)
const char* ntpServer = "pool.ntp.org";
const char* timezone = "CET-1CEST,M3.5.0,M10.5.0/3";

// Pins
const int servoPin = 13;
const int buttonPin = 14;
const int sensorPin = 33;
const int ledRot = 25;
const int ledGruen = 26;

// Steuerung
Servo servo;
bool schrankeOffen = false;
unsigned long zeitGeoeffnet = 0;
const unsigned long offenDauer = 3000;

// Fahrzeugzählung
int fahrzeuge = 0;
const int maxFahrzeuge = 3;

// === Hilfsfunktionen ===
void debug(String text) {
  if (DEBUG) Serial.println(text);
}

void connectToWiFi() {
  WiFi.begin(ssid, password);
  debug("WLAN verbinden...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    debug(".");
  }
  debug("WLAN verbunden: " + WiFi.localIP().toString());
}

void setupTime() {
  configTzTime(timezone, ntpServer);
  debug("Warte auf NTP-Zeit...");
  struct tm timeinfo;
  while (!getLocalTime(&timeinfo)) {
    delay(500);
    debug("...");
  }
  debug("Zeit synchronisiert");
}

String getTimeHHMM() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) return "00:00";
  char timeStr[6];
  snprintf(timeStr, sizeof(timeStr), "%02d:%02d", timeinfo.tm_hour, timeinfo.tm_min);
  return String(timeStr);
}

bool tasterGedrueckt() {
  if (digitalRead(buttonPin) == LOW) {
    delay(50); // Entprellung
    if (digitalRead(buttonPin) == LOW) {
      while (digitalRead(buttonPin) == LOW) delay(10); // Warten, bis der Taster losgelassen wird
      return true;
    }
  }
  return false;
}

void schrankeOeffnen() {
  debug("Schranke öffnet...");
  servo.write(100);
  schrankeOffen = true;
  zeitGeoeffnet = millis();
}

void lcd_updateZeilen() {
  lcd_setCursor(0, 0);
  lcd.print("Zeit: " + getTimeHHMM());

  lcd_setCursor(0, 1);
  if (fahrzeuge < maxFahrzeuge) {
    lcd.print("Frei: " + String(maxFahrzeuge - fahrzeuge) + "          ");
  } else {
    lcd.print("Parkhaus VOLL!   ");
  }
}

// MQTT Callback-Funktion
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  debug("MQTT Nachricht empfangen: Topic=" + String(topic) + ", Nachricht=" + message);

  if (String(topic) == "erlaubnis/") {
    if (fahrzeuge < maxFahrzeuge) {
      // Kennzeichen auf LCD anzeigen
      lcd.clear();
      lcd_setCursor(0, 0);
      lcd.print("Kennzeichen:");
      lcd_setCursor(0, 1);
      lcd.print(message);
      schrankeOeffnen();
      delay(8000); // 8 Sekunden anzeigen
      lcd.clear();
      lcd_updateZeilen();
    } else {
      debug("Parkhaus voll, Schranke bleibt geschlossen");
    }
  }
}

void setup() {
  Serial.begin(115200);

  connectToWiFi();
  setupTime();
  mqtt_setup();
  lcd_setup();

  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(sensorPin, INPUT);
  pinMode(ledRot, OUTPUT);
  pinMode(ledGruen, OUTPUT);

  servo.attach(servoPin);
  servo.write(0);

  // MQTT Callback und Subscription einrichten
  mqtt_setCallback(mqttCallback);
  mqtt_subscribe("erlaubnis/");

  mqtt_sendeStatus(fahrzeuge, maxFahrzeuge); // Initialer Status
}

void loop() {
  mqtt_loop(); // MQTT-Verbindung aufrechterhalten
  lcd_updateZeilen();

  // LED-Status
  digitalWrite(ledRot, fahrzeuge >= maxFahrzeuge ? HIGH : LOW);
  digitalWrite(ledGruen, fahrzeuge < maxFahrzeuge ? HIGH : LOW);

  // Schranke automatisch schließen
  if (schrankeOffen && millis() - zeitGeoeffnet >= offenDauer) {
    debug("Schranke schließt...");
    servo.write(0);
    schrankeOffen = false;
  }

  // Fahrzeug fährt ein (nur zählen)
  static bool bewegungErkannt = false;
  if (digitalRead(sensorPin) == HIGH && !bewegungErkannt) {
    bewegungErkannt = true;
    if (fahrzeuge < maxFahrzeuge) {
      fahrzeuge++;
      debug("Bewegung erkannt → Fahrzeug gezählt");
      mqtt_sendeStatus(fahrzeuge, maxFahrzeuge);
    } else {
      debug("Parkhaus voll → keine Zählung");
    }
  }
  if (digitalRead(sensorPin) == LOW) {
    bewegungErkannt = false;
  }

  // Fahrzeug fährt aus (Taster gedrückt)
  if (tasterGedrueckt() && !schrankeOffen) {
    debug("Taster gedrückt – Schranke öffnet (Ausfahrt)");
    schrankeOeffnen();

    if (fahrzeuge > 0) {
      fahrzeuge--; // Zähler reduzieren
      debug("Fahrzeug ausgefahren → Zähler reduziert auf: " + String(fahrzeuge));
      mqtt_sendeStatus(fahrzeuge, maxFahrzeuge); // Aktualisierten Status senden
    } else {
      debug("Kein Fahrzeug mehr drin → Zähler bleibt bei 0");
      mqtt_sendeStatus(fahrzeuge, maxFahrzeuge); // Status bleibt bei 0/3
    }
  }
  delay(200);
}
//mqtt_handler.h
#pragma once
#include <Arduino.h>

void mqtt_setup();
void mqtt_loop();
void mqtt_sendeStatus(int fahrzeuge, int maxFahrzeuge);
void mqtt_setCallback(void (*callback)(char*, byte*, unsigned int));
void mqtt_subscribe(const char* topic);
//lcd1602.h
#pragma once
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

extern LiquidCrystal_I2C lcd;

void lcd_setup(int sda_pin = 21, int scl_pin = 22);
void lcd_clear();
void lcd_setCursor(int x, int y);
void lcd_print(const String& message);
void lcd_updateZeilen();
void lcd_printKennzeichen(const String& kennzeichen);
void lcd_printStatus(const String& status);
void lcd_printFahrzeuge(int fahrzeuge, int maxFahrzeuge);

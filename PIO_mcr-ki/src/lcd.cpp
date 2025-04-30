//lcd.cpp
#include "lcd1602.h"
#include <Arduino.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);

void lcd_setup(int sda_pin, int scl_pin) {

  sda_pin = 21; // SDA pin
  scl_pin = 22; // SCL pin
  Wire.begin(sda_pin, scl_pin);
 // Serial.println("IST DA");
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Ready!");
  //Serial.println("LCD sollte ready zeigen!");
  delay(3000);
}

void lcd_clear() {
  lcd.clear();
}

void lcd_setCursor(int x, int y) {
  lcd.setCursor(x, y);
}

void lcd_print(const String& message) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(message);
  delay(2000);
}

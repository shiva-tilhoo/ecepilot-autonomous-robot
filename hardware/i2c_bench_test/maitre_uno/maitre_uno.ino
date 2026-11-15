#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ---------- Config OLED ----------
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1          // Pas de reset matériel
#define OLED_ADDR     0x3C        // Adresse I2C classique des SSD1306

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// ---------- Config I2C ----------
#define SLAVE_ADDR    0x08        // Adresse I2C de l'ESP-01

// ---------- Variables de test ----------
uint32_t lastValue    = 0;
bool     firstFrame   = true;
uint32_t lostFrames   = 0;
uint32_t totalFrames  = 0;
uint32_t readErrors   = 0;

unsigned long lastRefreshSerial = 0;

void setup() {
  // Moniteur série pour debug
  Serial.begin(115200);
  delay(500);
  Serial.println(F("=== Test I2C Master + OLED ==="));

  // I2C Master
  Wire.begin();  // UNO en maitre sur A4/A5

  // Init OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    Serial.println(F("Erreur init OLED !"));
    while (1);
  }

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(F("Init I2C test..."));
  display.display();
  delay(1000);
}

void loop() {
  // 1) Lire une trame I2C (4 octets = uint32_t)
  uint32_t value;
  bool ok = lireTrameI2C(value);

  if (ok) {
    totalFrames++;

    if (!firstFrame) {
      if (value != lastValue + 1) {
        if (value > lastValue) {
          uint32_t diff = value - lastValue;
          if (diff > 0) {
            uint32_t perdues = diff - 1;
            lostFrames += perdues;
            Serial.print(F("[LOSS] Saut detecte: dernier="));
            Serial.print(lastValue);
            Serial.print(F(" recu="));
            Serial.print(value);
            Serial.print(F("  (trames perdues estimees: "));
            Serial.print(perdues);
            Serial.println(F(")"));
          }
        } else {
          Serial.print(F("[WARN] Ordre inverse: recu "));
          Serial.print(value);
          Serial.print(F(" apres "));
          Serial.println(lastValue);
        }
      }
    } else {
      firstFrame = false;
    }

    lastValue = value;
  } else {
    readErrors++;
  }

  // 2) Affichage OLED
  afficherOLED(ok, lastValue);

  // 3) Debug série périodique
  unsigned long now = millis();
  if (now - lastRefreshSerial >= 2000) {
    lastRefreshSerial = now;
    Serial.println(F("----- STATUT I2C -----"));
    Serial.print(F("Trames recues       : "));
    Serial.println(totalFrames);
    Serial.print(F("Trames perdues (est): "));
    Serial.println(lostFrames);
    Serial.print(F("Erreurs lecture I2C : "));
    Serial.println(readErrors);
    Serial.print(F("Derniere valeur     : "));
    Serial.println(lastValue);
    Serial.println(F("----------------------"));
  }

  delay(50); // fréquence de demande ~20 Hz
}

// ----------- Fonctions -----------

bool lireTrameI2C(uint32_t &value) {
  const uint8_t toRead = 4;

  Wire.requestFrom((int)SLAVE_ADDR, (int)toRead);
  if (Wire.available() != toRead) {
    // Pas assez d'octets -> erreur de lecture
    return false;
  }

  uint8_t b0 = Wire.read();
  uint8_t b1 = Wire.read();
  uint8_t b2 = Wire.read();
  uint8_t b3 = Wire.read();

  value  = (uint32_t)b0;
  value |= (uint32_t)b1 << 8;
  value |= (uint32_t)b2 << 16;
  value |= (uint32_t)b3 << 24;

  return true;
}

void afficherOLED(bool ok, uint32_t currentValue) {
  display.clearDisplay();
  display.setCursor(0, 0);

  display.println(F("Test I2C ESP-01"));

  display.print(F("Etat I2C: "));
  display.println(ok ? F("OK") : F("ERREUR"));

  display.print(F("Val recu : "));
  display.println(currentValue);

  display.print(F("Trames OK : "));
  display.println(totalFrames);

  display.print(F("Perdues   : "));
  display.println(lostFrames);

  display.print(F("Err lecture: "));
  display.println(readErrors);

  display.display();
}

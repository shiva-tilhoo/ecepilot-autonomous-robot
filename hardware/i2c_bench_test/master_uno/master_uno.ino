#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ---------- Config OLED ----------
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1          // No hardware reset
#define OLED_ADDR     0x3C        // Usual I2C address of the SSD1306

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// ---------- Config I2C ----------
#define SLAVE_ADDR    0x08        // I2C address of the ESP-01

// ---------- Test variables ----------
uint32_t lastValue    = 0;
bool     firstFrame   = true;
uint32_t lostFrames   = 0;
uint32_t totalFrames  = 0;
uint32_t readErrors   = 0;

unsigned long lastRefreshSerial = 0;

void setup() {
  // Serial monitor for debugging
  Serial.begin(115200);
  delay(500);
  Serial.println(F("=== Test I2C Master + OLED ==="));

  // I2C Master
  Wire.begin();  // UNO as master on A4/A5

  // Init OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    Serial.println(F("OLED init error!"));
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
  // 1) Read an I2C frame (4 bytes = uint32_t)
  uint32_t value;
  bool ok = readI2CFrame(value);

  if (ok) {
    totalFrames++;

    if (!firstFrame) {
      if (value != lastValue + 1) {
        if (value > lastValue) {
          uint32_t diff = value - lastValue;
          if (diff > 0) {
            uint32_t lost = diff - 1;
            lostFrames += lost;
            Serial.print(F("[LOSS] Gap detected: last="));
            Serial.print(lastValue);
            Serial.print(F(" received="));
            Serial.print(value);
            Serial.print(F("  (estimated lost frames: "));
            Serial.print(lost);
            Serial.println(F(")"));
          }
        } else {
          Serial.print(F("[WARN] Out of order: received "));
          Serial.print(value);
          Serial.print(F(" after "));
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

  // 2) OLED display
  showOnOLED(ok, lastValue);

  // 3) Periodic serial debug
  unsigned long now = millis();
  if (now - lastRefreshSerial >= 2000) {
    lastRefreshSerial = now;
    Serial.println(F("----- I2C STATUS -----"));
    Serial.print(F("Frames received     : "));
    Serial.println(totalFrames);
    Serial.print(F("Frames lost (est.)  : "));
    Serial.println(lostFrames);
    Serial.print(F("I2C read errors     : "));
    Serial.println(readErrors);
    Serial.print(F("Last value          : "));
    Serial.println(lastValue);
    Serial.println(F("----------------------"));
  }

  delay(50); // request rate ~20 Hz
}

// ----------- Functions -----------

bool readI2CFrame(uint32_t &value) {
  const uint8_t toRead = 4;

  Wire.requestFrom((int)SLAVE_ADDR, (int)toRead);
  if (Wire.available() != toRead) {
    // Not enough bytes -> read error
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

void showOnOLED(bool ok, uint32_t currentValue) {
  display.clearDisplay();
  display.setCursor(0, 0);

  display.println(F("Test I2C ESP-01"));

  display.print(F("I2C state: "));
  display.println(ok ? F("OK") : F("ERROR"));

  display.print(F("Value rx : "));
  display.println(currentValue);

  display.print(F("Frames OK : "));
  display.println(totalFrames);

  display.print(F("Lost      : "));
  display.println(lostFrames);

  display.print(F("Read errors: "));
  display.println(readErrors);

  display.display();
}

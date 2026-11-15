# Hardware

## `remote_control_pcb/` — Wi-Fi remote control

Board of the rover's remote control, designed in KiCad (revision 1.2).

- ATmega328P with an external crystal: joystick and button readout, RGB LED, buzzer
- ESP-01S: wireless gateway to the rover, connected to the ATmega over I²C
- LD1117V33 regulator for the 3.3 V rail

Board designed by the team (Mathéo Léon, Amandine Soyez, Shiva Tilhoo).
Open `technicalProject.kicad_pro` with KiCad 9; `ESP8266.lib` provides the ESP-01S symbol.

## `i2c_bench_test/` — I²C test bench

Arduino Uno sketch acting as I²C master against the ESP-01 (slave at address `0x08`), used to validate the link before integrating it on the board. An SSD1306 OLED display shows received frames, lost frames and read errors in real time.

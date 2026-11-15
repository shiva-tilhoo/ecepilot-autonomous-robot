# ESP32 firmware

PlatformIO project (`esp32dev`, Arduino framework, micro-ROS Humble over Wi-Fi).

| File | Role |
|---|---|
| `src/main.cpp` | LiDAR, IMU and publish FreeRTOS tasks, connection to the micro-ROS agent, `/cmd_vel` subscriber |
| `src/motors.cpp`, `include/motors.h` | Differential PWM drive of the two motors |
| `include/config.h` | Subsystem switches (`ENABLE_MOTORS`, `ENABLE_LIDAR`, `ENABLE_IMU`) and pin mapping |
| `include/secrets.example.h` | Template for the Wi-Fi credentials |

## Build and upload

```bash
cp include/secrets.example.h include/secrets.h   # network SSID and password
pio run --target upload
pio device monitor
```

`secrets.h` is ignored by git. The `micro_ros_platformio` library builds under Linux or WSL; the default serial port is `/dev/ttyUSB0` (change it in `platformio.ini`).

## Connecting to the agent

The firmware first resolves the agent by name (`microros-agent.local`), then tries two fallback addresses defined at the top of `main.cpp`, on UDP port 8888. If the link drops, it goes back to waiting and reconnects by itself.

## Pin mapping

| Signal | GPIO |
|---|---|
| LD06 LiDAR RX | 16 |
| Left motor AIN1 / AIN2 / PWM | 21 / 17 / 25 |
| Right motor BIN1 / BIN2 / PWM | 22 / 23 / 26 |

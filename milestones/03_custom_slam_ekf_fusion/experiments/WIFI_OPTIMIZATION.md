# 🔧 WiFi Optimisations for a Connection Shared from a Phone

## 🚨 Problems with shared connections
- **Limited bandwidth** (mobile data sharing)
- **Variable latency** (unstable mobile network)
- **Packet loss** (WiFi with a weak signal)

---

## ✅ Solutions for the ESP32

### 1. **Reduce the message size (mini-scan instead of 360 points)**

In `main.cpp`, instead of publishing 360 points:

```cpp
// Only publish the relevant points (e.g. 90 points instead of 360)
#define PTS_PUBLISH 90  // Instead of 360

// In publishTask:
for(int i = 0; i < 360; i += 4) {  // Take 1 point out of 4
  lidar_ranges[j] = lidar_buffer[i].distance;
  j++;
}
msg_lidar.ranges.size = j;  // Dynamic
```

**Gain**: -75% bandwidth, 4x faster ✅

---

### 2. **Configure the WiFi for the best throughput**

**To add in the ESP32 `setup()`**:

```cpp
// Reduce the WiFi power (saves battery + reduces noise)
WiFi.setTxPower(WIFI_POWER_8dBm);  // Minimum power

// 802.11 B WiFi mode (slow but stable on a bad signal)
esp_wifi_set_phy_mode(WIFI_PHY_MODE_11B);

// Reduced WiFi buffer
WiFi.setAutoReconnect(true);
WiFi.setSleep(false);  // Keep the radio active
```

---

### 3. **Data compression**

Instead of 360 floats, use **uint8_t** values (distance / 10):

```cpp
// Before: 360 * 4 bytes = 1440 bytes
// After: 360 * 1 byte = 360 bytes = 4x smaller!

uint8_t compressed_ranges[360];
for(int i = 0; i < 360; i++) {
  compressed_ranges[i] = (uint8_t)(lidar_buffer[i].distance * 10);  // Precision: 10cm
}
```

---

### 4. **Optimised QoS** (in the bridge)

**In the ROS2 terminal**:

```bash
ros2 launch foxglove_bridge foxglove_bridge_launch.xml \
  port:=8765 \
  ros_qos_profile:=sensor_data  # Instead of default
```

---

### 5. **Monitor the WiFi quality**

**On the ESP32, add to the loop**:

```cpp
if(WiFi.status() == WL_CONNECTED) {
  int rssi = WiFi.RSSI();  // Signal strength (-30 to -100 dBm)
  Serial.printf("[WiFi] Signal: %d dBm | Quality: %d%%\n", 
                rssi, (rssi + 100) * 2);
}
```

**Interpretation**:
- `-30 to -50 dBm`: Excellent ✅
- `-50 to -70 dBm`: Good
- `-70 to -80 dBm`: Acceptable
- `-80 to -100 dBm`: Weak 🚨

---

### 6. **UDP fragmentation**

**If the connection drops often**: reduce the MTU

```cpp
// Default MTU: 1500 bytes (too large for weak WiFi)
// Reduce to 512 to avoid fragmentation
#define UDP_PACKET_MAX 512
```

---

## 🎯 Priority of the optimisations

| Solution | Impact | Effort |
|---|---|---|
| 1. Reduce the LIDAR points (90 instead of 360) | **~80% bandwidth** | ⭐ Easy |
| 2. Use compressed uint8_t | **4x smaller** | ⭐⭐ Medium |
| 3. Reduce the WiFi power | **Better stability** | ⭐ Easy |
| 4. Optimised ROS QoS | **Fewer retransmissions** | ⭐ Easy |
| 5. Monitor the signal | **Debug the problems** | ⭐ Easy |

---

## 🚀 Quick test

**Try solution #1 first** (reduce the points):

```cpp
// In publishTask, replace:
for(int i = 0; i < 360; i++) {
  lidar_ranges[i] = lidar_buffer[i].distance;
}
msg_lidar.ranges.size = 360;

// With:
uint16_t count = 0;
for(int i = 0; i < 360; i += 4) {  // 1 point out of 4
  lidar_ranges[count++] = lidar_buffer[i].distance;
}
msg_lidar.ranges.size = count;  // ~90 points
```

**Result**: bandwidth divided by 4, lower latency! 🚀

# IMU Filtering Strategy - MPU6050

## MPU6050 specifications

### Sampling frequency
- **Internal clock**: ~8 MHz
- **Default sampling rate**: 1 kHz (configurable through register 0x19)
- **Divider (SMPRT_DIV)**: `actual_rate = 1000 / (1 + SMPRT_DIV)`
  - SMPRT_DIV=9 → 100 Hz ✅ (recommended for robots)
  - SMPRT_DIV=4 → 200 Hz (faster)
  - SMPRT_DIV=19 → 50 Hz (slower)

### I2C specifications
- Standard I2C: up to 400 kHz
- Typical transfer speed: 100-400 kHz
- **Latency**: ~10-20 ms

### Measurement ranges (configurable)
- **Accelerometer**: ±2g, ±4g, ±8g, ±16g
- **Gyroscope**: ±250°/s, ±500°/s, ±1000°/s, ±2000°/s

---

## Common noise problems

### Typical noise sources
1. **Motor vibrations** (50-100 Hz)
2. **PWM frequency** (5-10 kHz, rarely visible in the acceleration)
3. **Thermal noise** (white, broadband)
4. **I2C/electrical noise** (depends on the wiring)
5. **Power supply**: harmonic frequencies of the supply voltage

---

## Filtering workflow

### Step 1: FFT analysis
```bash
# Start the stack as usual (agent + IMU)
./start_stack.sh

# In another terminal, capture and analyse
python3 imu_fft_analysis.py --duration 30 --sample-rate 100
```

**This produces:**
- `imu_raw_data.csv` - Raw data
- `imu_fft_analysis.png` - FFT plot with the peaks identified
- Console - Main parasitic frequencies

### Step 2: FIR filter design

Based on the FFT analysis, choose:

#### Option A: Simple low-pass filter (for white noise)
```bash
# Cutoff at 20 Hz (good for slow robots)
python3 imu_fir_filter.py --cutoff 20 --order 21 --sample-rate 100
```

#### Option B: Filter with notches (for a specific parasitic frequency)
```bash
# Cutoff at 20 Hz + notches at 50 Hz and 100 Hz (typical motor vibrations)
python3 imu_fir_filter.py --cutoff 20 --order 21 --sample-rate 100 --notch 50 100
```

#### Option C: Less aggressive filter (to preserve the dynamics)
```bash
# Cutoff at 30 Hz (lets more frequencies through)
python3 imu_fir_filter.py --cutoff 30 --order 15 --sample-rate 100
```

---

## Reading the FFT results

### Example: typical results
```
Accel x: Top peaks:
  45.2Hz: 0.234    ← Motor vibration
  92.1Hz: 0.089    ← 2x harmonic
  White noise: 0.001-0.010

Gyro z: Top peaks:
  45.2Hz: 0.012    ← Same frequency, lower amplitude
```

**Interpretation:**
- Dominant peak at ~45 Hz → notch filter at 45 Hz
- Harmonic at 92 Hz → a notch at 92 Hz can be added too
- Low white noise → a low-pass filter is enough

---

## FIR filter parameters

### Cutoff Frequency
- **Too low** (5 Hz): excellent filtering but very slow (lag)
- **Recommended** (15-25 Hz): good speed/accuracy balance
- **Too high** (50+ Hz): does not filter enough

### FIR Order
- **Order 11**: fast, light filtering
- **Order 21** (recommended): good balance
- **Order 31+**: better filtering, more latency

**Rule**: `Latency ≈ (Order / 2) / sample_rate`
- Order 21 @ 100 Hz → latency ≈ 100 ms
- Order 15 @ 100 Hz → latency ≈ 75 ms

### Notch Filters
- Use them when the FFT shows a very dominant peak
- Example: 50 Hz (mains frequency), 60 Hz (United States)
- 2-3 notches at most (beyond that, instability)

---

## Comparison: EMA vs FIR vs Kalman

| Filter | Latency | White noise | Parasitic noise | Complexity |
|--------|---------|-------------|-----------------|------------|
| **EMA** | Low | Medium | Poor | Very low |
| **FIR** (this script) | Medium | Very good | Very good | Medium |
| **Kalman** | Low | Excellent | Medium | High |

**For this project**: FIR + Kalman Filter Fusion = optimal

---

## Recommended configuration for the robot

### Default configuration (slow, noisy robot)
```bash
# In start_stack.sh, replace:
python3 imu_kalman_filter.py

# With:
python3 imu_fir_filter.py --cutoff 20 --order 21 --sample-rate 100
```

### Configuration for a fast robot (less lag)
```bash
python3 imu_fir_filter.py --cutoff 25 --order 15 --sample-rate 100
```

### Configuration after the FFT analysis
```bash
# If a dominant peak shows up at 45 Hz:
python3 imu_fir_filter.py --cutoff 20 --order 21 --sample-rate 100 --notch 45
```

---

## Debugging

### Check the latency
```bash
# Compare the timestamps of /imu/data and /imu/data_filtered
ros2 topic echo /imu/data | grep "sec"
ros2 topic echo /imu/data_filtered | grep "sec"
```

### Check the filtering
```bash
# Capture and compare raw vs filtered
python3 -c "
import csv
import numpy as np

with open('imu_raw_data.csv') as f:
    reader = csv.DictReader(f)
    raw = [float(row['accel_x']) for row in reader]

print(f'Raw std: {np.std(raw):.4f}')
print(f'Raw mean: {np.mean(raw):.4f}')
print(f'Raw range: {np.max(raw)-np.min(raw):.4f}')
"
```

### Fine tuning
If the filtering is too aggressive:
- Lower the cutoff by 2-3 Hz
- Lower the FIR order by 5-10

If noise remains:
- Raise the cutoff by 5 Hz
- Raise the FIR order by 10
- Add notches at the parasitic frequencies

---

## Next steps

1. ✅ Run `imu_fft_analysis.py` (capture 30 s)
2. ✅ Analyse `imu_fft_analysis.png` (identify the peaks)
3. ✅ Configure `imu_fir_filter.py` with suitable parameters
4. ✅ Validate with the Kalman Filter Fusion
5. ✅ Test navigation with Nav2

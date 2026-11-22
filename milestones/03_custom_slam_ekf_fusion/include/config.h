#ifndef CONFIG_H
#define CONFIG_H

// ============================================================
// Global configuration
// ============================================================

// Enable/disable the subsystems
#define ENABLE_MOTORS 0
#define ENABLE_LIDAR 1
#define ENABLE_IMU 1

// ============================================================
// Motor configuration
// ============================================================

#if ENABLE_MOTORS

// Motor A (left)
#define MOTOR_LEFT_DIR1 21    // GPIO21 - AIN1
#define MOTOR_LEFT_DIR2 17    // GPIO17 - AIN2
#define MOTOR_LEFT_PWM 25     // GPIO25 - PWMA

// Motor B (right)
#define MOTOR_RIGHT_DIR1 22   // GPIO22 - BIN1
#define MOTOR_RIGHT_DIR2 23   // GPIO23 - BIN2
#define MOTOR_RIGHT_PWM 26    // GPIO26 - PWMB

// PWM configuration
#define PWM_FREQ 100000       // 100 kHz (as in the Waveshare code)
#define PWM_RESOLUTION 8      // 8-bit (0-255)
#define PWM_CHANNEL_LEFT 0
#define PWM_CHANNEL_RIGHT 1
#define MAX_SPEED 255         // 0-255

#endif // ENABLE_MOTORS

#endif // CONFIG_H

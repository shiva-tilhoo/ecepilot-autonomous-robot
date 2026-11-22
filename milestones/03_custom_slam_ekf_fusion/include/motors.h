#ifndef MOTORS_H
#define MOTORS_H

// ============================================================
// Motor control - Interface
// ============================================================

#include <Arduino.h>
#include "config.h"

#if ENABLE_MOTORS

// Initialise the pins and the PWM
void motors_init();

// Left motor control (-255 to +255)
void motor_left(int speed);

// Right motor control (-255 to +255)
void motor_right(int speed);

// Stop both motors
void motors_stop();

// Differential control (throttle + steering)
// throttle: -255 (backward) to +255 (forward)
// steering: -255 (left) to +255 (right)
void motors_drive(int throttle, int steering);

#else

// Empty stubs when the motors are disabled
inline void motors_init() {}
inline void motor_left(int) {}
inline void motor_right(int) {}
inline void motors_stop() {}
inline void motors_drive(int, int) {}

#endif // ENABLE_MOTORS

#endif // MOTORS_H

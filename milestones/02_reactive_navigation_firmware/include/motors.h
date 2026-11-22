// ============================================================
// Motor control - Simplified version
// ============================================================

#ifndef MOTORS_H
#define MOTORS_H

#include <Arduino.h>

// Initialise the motors
void motors_init();

// Left motor control: speed = -255 to +255
void motor_left(int speed);

// Right motor control: speed = -255 to +255
void motor_right(int speed);

// Full stop
void motors_stop();

// RC-car style control: throttle (-255 to +255), steering (-255 to +255)
void motors_drive(int throttle, int steering);

#endif // MOTORS_H

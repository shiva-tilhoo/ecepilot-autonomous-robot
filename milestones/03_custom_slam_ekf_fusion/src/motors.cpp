// ============================================================
// Motor control - Implementation
// ============================================================

#include "motors.h"
#include "config.h"

#if ENABLE_MOTORS

void motors_init() {
    Serial.println("[MOTORS] Init start");
    delay(100);  // Safety delay
    
    // Left motor pin configuration
    pinMode(MOTOR_LEFT_DIR1, OUTPUT);
    pinMode(MOTOR_LEFT_DIR2, OUTPUT);
    digitalWrite(MOTOR_LEFT_DIR1, LOW);
    digitalWrite(MOTOR_LEFT_DIR2, LOW);
    
    // Right motor pin configuration
    pinMode(MOTOR_RIGHT_DIR1, OUTPUT);
    pinMode(MOTOR_RIGHT_DIR2, OUTPUT);
    digitalWrite(MOTOR_RIGHT_DIR1, LOW);
    digitalWrite(MOTOR_RIGHT_DIR2, LOW);
    
    delay(50);
    
    // Setup PWM channels
    ledcSetup(PWM_CHANNEL_LEFT, PWM_FREQ, PWM_RESOLUTION);
    ledcAttachPin(MOTOR_LEFT_PWM, PWM_CHANNEL_LEFT);
    ledcWrite(PWM_CHANNEL_LEFT, 0);
    
    delay(50);
    
    ledcSetup(PWM_CHANNEL_RIGHT, PWM_FREQ, PWM_RESOLUTION);
    ledcAttachPin(MOTOR_RIGHT_PWM, PWM_CHANNEL_RIGHT);
    ledcWrite(PWM_CHANNEL_RIGHT, 0);
    
    delay(50);
    Serial.println("[MOTORS] Initialized");
}

void motor_left(int speed) {
    // Clamp the speed (MIN_PWM to avoid stalling)
    const int MIN_PWM = MAX_SPEED / 5;  // 51 (20% of 255)
    
    if (speed > 0) {
        // Forward - per the datasheet: AIN1=LOW, AIN2=HIGH
        digitalWrite(MOTOR_LEFT_DIR1, LOW);
        digitalWrite(MOTOR_LEFT_DIR2, HIGH);
        // Apply the minimum PWM to avoid stalling
        int pwm = constrain(abs(speed), MIN_PWM, MAX_SPEED);
        ledcWrite(PWM_CHANNEL_LEFT, pwm);
    } else if (speed < 0) {
        // Backward - per the datasheet: AIN1=HIGH, AIN2=LOW
        digitalWrite(MOTOR_LEFT_DIR1, HIGH);
        digitalWrite(MOTOR_LEFT_DIR2, LOW);
        int pwm = constrain(abs(speed), MIN_PWM, MAX_SPEED);
        ledcWrite(PWM_CHANNEL_LEFT, pwm);
    } else {
        // Stop
        digitalWrite(MOTOR_LEFT_DIR1, LOW);
        digitalWrite(MOTOR_LEFT_DIR2, LOW);
        ledcWrite(PWM_CHANNEL_LEFT, 0);
    }
}

void motor_right(int speed) {
    // Clamp the speed (MIN_PWM to avoid stalling)
    const int MIN_PWM = MAX_SPEED / 5;  // 51 (20% of 255)
    
    if (speed > 0) {
        // Forward - per the datasheet: BIN1=LOW, BIN2=HIGH
        digitalWrite(MOTOR_RIGHT_DIR1, LOW);
        digitalWrite(MOTOR_RIGHT_DIR2, HIGH);
        int pwm = constrain(abs(speed), MIN_PWM, MAX_SPEED);
        ledcWrite(PWM_CHANNEL_RIGHT, pwm);
    } else if (speed < 0) {
        // Backward - per the datasheet: BIN1=HIGH, BIN2=LOW
        digitalWrite(MOTOR_RIGHT_DIR1, HIGH);
        digitalWrite(MOTOR_RIGHT_DIR2, LOW);
        int pwm = constrain(abs(speed), MIN_PWM, MAX_SPEED);
        ledcWrite(PWM_CHANNEL_RIGHT, pwm);
    } else {
        // Stop
        digitalWrite(MOTOR_RIGHT_DIR1, LOW);
        digitalWrite(MOTOR_RIGHT_DIR2, LOW);
        ledcWrite(PWM_CHANNEL_RIGHT, 0);
    }
}

void motors_stop() {
    motor_left(0);
    motor_right(0);
}

void motors_drive(int throttle, int steering) {
    // Converts joystick-style commands into differential wheel speeds
    // throttle: -255 (backward) to +255 (forward)
    // steering: -255 (left) to +255 (right)
    
    throttle = constrain(throttle, -MAX_SPEED, MAX_SPEED);
    steering = constrain(steering, -MAX_SPEED, MAX_SPEED);
    
    // Compute the differential speeds
    int leftSpeed = throttle + steering;
    int rightSpeed = throttle - steering;
    
    // Clamp to avoid overflow
    leftSpeed = constrain(leftSpeed, -MAX_SPEED, MAX_SPEED);
    rightSpeed = constrain(rightSpeed, -MAX_SPEED, MAX_SPEED);
    
    motor_left(leftSpeed);
    motor_right(rightSpeed);
}

#endif

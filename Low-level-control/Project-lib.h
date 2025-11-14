#pragma once

//============================================================== INCLUDE ==============================================================//
#include "Arduino.h"
#include "ESP32Servo.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"

//============================================================== DEFINE ==============================================================//

#define INPUT_SENSOR_PIN 36
#define MEASURE_SENSOR_PIN 39
#define SORTING_SENSOR_PIN 34

#define CONVEYOR_MOTOR_PIN 26

#define GATE_SERVO_PIN 27
#define GATE_CLOSE_ANGLE 180
#define GATE_OPEN_ANGLE 90

#define GRIPPER_HOMING_SWITCH_PIN 13
#define GRIPPER_STEPPER_PUL_PIN 16
#define GRIPPER_STEPPER_DIR_PIN 17
#define GRIPPER_STEPPER_ENABLE_PIN 14

#define GRIPPER_CYLINDER_GRIP_VALVE_PIN 21
#define GRIPPER_CYLINDER_RELEASE_VALVE_PIN 19
#define GRIPPER_DETECT_CONTACT_SWITCH_PIN_1 22
#define GRIPPER_DETECT_CONTACT_SWITCH_PIN_2 18

#define PROBE_CYLINDER_EXTEND_VALVE_PIN 32
#define PROBE_CYLINDER_RETRACT_VALVE_PIN 33
#define PROBE_DETECT_CONTACT_SWITCH_PIN 23

#define SORTING_SERVO_PIN 25

#define SORTING_ANGLE_TYPE_1 0
#define SORTING_ANGLE_TYPE_2 180

#define PRESET_ANGLE_BETWEEN_TWO_MEASUREMENT 10
#define STEPPER_PULSE_IN_uS 2000
#define STEPPER_STEP_PER_REV 800


#define NO_PAYLOAD -1
#define FRUIT_LIST_LENGTH 5

//============================================================== STATES ==============================================================//
enum Fruit_state 
{
    NOT_ENGAGED,
    INPUT_ENTERED,
    INPUT_PASSED,
    MEASURE_ENTERED,
    MEASURE_PROCESSING,
    MEASURE_PASSED,
    SORTING_PASSED
};

enum Task_state 
{
    TRIGGER_WAIT,
    MEASURING_DIA,
    CENTERING,
    MEASURING_SPECTRAL
};

//============================================================== FRUIT STRUCT ==============================================================//
struct Fruit 
{
    long id;                           // Fruit number
    Fruit_state current_fruit_state;   // Current state of the fruit
    long dia_measure;                  // Time taken to pass the diameter sensor
    bool is_centered;                  // Whether the fruit is centered at the measurement module
    unsigned int sorting_type;         // Type/category of the fruit
    bool is_sorted;                    // Whether the fruit has been sorted 
    bool point_measure_done;          // Whether a measurement point has been completed
    int point_measured;
};

//============================================================== FRUIT DATA STRUCT ==============================================================//
struct Fruit_data 
{
    long fruit_id;           // ID of the fruit
    Fruit_state fruit_state; // State of the fruit
    int payload;          // Data value associated with the fruit
};

//=============================================================== MOTOR CLASS ==============================================================//
class myMotor
{
    public:
        int motor_pin = 0;
    
    public:
        myMotor(int motor_pin)
        :motor_pin(motor_pin)
        {
            ledcAttach(motor_pin, 1000, 10);
            ledcWrite(motor_pin, 0);
        }

        void run(int speed)
        {
            speed = constrain(speed, 0, 100);
            int duty = speed * 1023/100;
            ledcWrite(motor_pin, duty);
        }
};

//=============================================================== PNEUMATIC VALVE CLASS ==============================================================//
class myPneumaticValve
{
    public:
        int position_A_pin = 0;
        int position_B_pin = 0;
    
    public:
        myPneumaticValve(int position_A_pin, int position_B_pin)
        :position_A_pin(position_A_pin), position_B_pin(position_B_pin)
        {
            pinMode(position_A_pin, OUTPUT);
            pinMode(position_B_pin, OUTPUT);
        }

        void position_A()
        {
            digitalWrite(position_B_pin, LOW);
            digitalWrite(position_A_pin, HIGH);
        }

        void mid_position()
        {
            digitalWrite(position_B_pin, LOW);
            digitalWrite(position_A_pin, LOW);
        }

        void position_B()
        {
            digitalWrite(position_A_pin, LOW);
            digitalWrite(position_B_pin, HIGH);
        }
};
//=============================================================== STEPPER CLASS ==============================================================//
class myStepper
{
    private:
        int pul_pin;
        int dir_pin;
        int home_switch_pin;
        int enable_pin;

        long current_position;    // current position in steps
        long target_position;     // target position in steps

        float steps_per_rev;      // steps per revolution
        float mm_per_rev;         // mm moved per revolution (for linear actuator)

        int pulse_delay_us;       // microsecond delay between steps

    public:
        myStepper(int pul_pin, int dir_pin, int enable_pin, int home_switch_pin, float steps_per_rev = STEPPER_STEP_PER_REV, float mm_per_rev = 8.0f, int pulse_delay_us = STEPPER_PULSE_IN_uS)
        : pul_pin(pul_pin), dir_pin(dir_pin), home_switch_pin(home_switch_pin), enable_pin(enable_pin),
        steps_per_rev(steps_per_rev), mm_per_rev(mm_per_rev), pulse_delay_us(pulse_delay_us)
        {
            current_position = 0;
            target_position = 0;

            pinMode(pul_pin, OUTPUT);
            pinMode(dir_pin, OUTPUT);
            pinMode(enable_pin, OUTPUT);
            pinMode(home_switch_pin, INPUT_PULLUP);
        }

        void home(bool homing_dir)
        {
            digitalWrite(enable_pin, HIGH);
            Serial.println("Homing...");

            digitalWrite(dir_pin, homing_dir ? LOW : HIGH);

            while (digitalRead(home_switch_pin) == HIGH)
            {
                pulse_once();
            }

            current_position = 0;
            Serial.println("Homing complete");
        }

        void run_by_step(long step, bool is_relative = false)
        {
            if (is_relative)
                target_position = current_position + step;
            else
                target_position = step;

            move_to_target();
        }

        void run_by_distance(float distance_mm, bool is_relative = false)
        {
            long step = (distance_mm / mm_per_rev) * steps_per_rev;

            if (is_relative)
                target_position = current_position + step;
            else
                target_position = step;

            move_to_target();
        }

        void run_by_angle(float angle_deg, bool is_relative = false)
        {
            Serial.println("run by angle" + String(angle_deg));
            long step = (angle_deg / 360.0f) * steps_per_rev;

            if (is_relative)
                target_position = current_position + step;
            else
                target_position = step;

            move_to_target();
        }

        long get_current_position()
        {
            return current_position;
        }

    private:
        void move_to_target()
        {
            long step_difference = target_position - current_position;

            if (step_difference == 0)
                return;

            bool direction = (step_difference > 0);
            digitalWrite(dir_pin, direction ? HIGH : LOW);

            long steps_to_move = abs(step_difference);

            for (long i = 0; i < steps_to_move; i++)
            {
                pulse_once();
                current_position += direction ? 1 : -1;
            }
        }

        void pulse_once()
        {
            digitalWrite(pul_pin, HIGH);
            delayMicroseconds(pulse_delay_us);
            digitalWrite(pul_pin, LOW);
            delayMicroseconds(pulse_delay_us);
        }
};
//=============================================================== SERVO CLASS ==============================================================//

class myServo
{
    private:
        int servo_pin;
        double freq = 50.0;              // 50 Hz = 20 ms period
        int resolution_bits = 16;        // Max resolution for stable 50 Hz
        uint32_t max_duty;               // 2^resolution_bits - 1

        // Pulse width range (µs)
        const int min_pulse_us = 1000;   // 1 ms → 0°
        const int max_pulse_us = 2000;   // 2 ms → 180°

    public:
        myServo(int pin)
        {
            servo_pin = pin;
            // Configure LEDC pin, frequency, and resolution
            ledcAttach(servo_pin, freq, resolution_bits);
            max_duty = (1 << resolution_bits) - 1;
        }

        void set_angle(int angle)
        {
            angle = constrain(angle, 0, 180);

            // Map angle → pulse width (1000–2000 µs)
            int pulse_us = map(angle, 0, 180, min_pulse_us, max_pulse_us);

            // Convert pulse width to duty cycle
            const int period_us = 1000000 / freq; // 20,000 µs at 50 Hz
            uint32_t duty = (uint32_t)((pulse_us * (double)max_duty) / period_us);

            ledcWrite(servo_pin, duty);
        }
};

//============================================================== VARIABLE DECORATION ==============================================================//
extern int preset_measure_times;
extern long initial_fruit;
extern int preset_conveyor_speed;

extern long input_fruit_id;
extern Fruit* input_fruit_pointer;

extern long measure_fruit_id;
extern Fruit* measure_fruit_pointer;

extern long sorting_fruit_id;
extern Fruit* sorting_fruit_pointer;

extern QueueHandle_t messages_sending_queue;

extern Task_state input_task_state;
extern Task_state measure_task_state;
extern Task_state sorting_task_state;

extern TaskHandle_t input_task_handle;
extern TaskHandle_t measure_task_handle;
extern TaskHandle_t sorting_task_handle;
extern TaskHandle_t uart_receive_task_handle;

extern Fruit fruit_list[FRUIT_LIST_LENGTH];

extern myMotor conveyor_motor;
extern myStepper gripper_stepper;
extern myServo gate_servo;
extern myServo sorting_servo;
extern myPneumaticValve probe_valve;
extern myPneumaticValve gripper_valve;

//============================================================== FUNCTION DECORATION ==============================================================//
Fruit* search_fruit(long fruit_id);
void reset_fruit(Fruit* f);
void initialize_system();
void send_fruit_message(Fruit *fruit, int payload);
void system_start();


bool check_trigger(int sensor_pin);
void conveyor_run();
void conveyor_stop();
void gripper_release(bool all_the_way);
void gripper_grip();
void gripper_position_fruit(int measure_position);
void gripper_home();
void probe_attach();
void probe_deattach(int measure_position);
void sorting_bin_write(int angle);
void gate_open();
void gate_close();
void process_sending_queue();
void hardware_init();
void system_stop();

//============================================================== TASK DECORATION ==============================================================//
void Supervisor_Task(void* parameter);
void Input_Task(void* parameter);
void Measure_Task(void* parameter);
void Sorting_Task(void* parameter);
void UartReceiveTask(void* parameter);


#include "Project-lib.h"

int preset_measure_times = 0;
long initial_fruit = 0;
int preset_conveyor_speed = 0;

long input_fruit_id = 0;
Fruit* input_fruit_pointer = nullptr;

long measure_fruit_id = 0;
Fruit* measure_fruit_pointer = nullptr;

long sorting_fruit_id = 0;
Fruit* sorting_fruit_pointer = nullptr;

QueueHandle_t messages_sending_queue = nullptr;

Task_state input_task_state;
Task_state measure_task_state;
Task_state sorting_task_state;

TaskHandle_t input_task_handle = NULL;
TaskHandle_t measure_task_handle = NULL;
TaskHandle_t sorting_task_handle = NULL;
TaskHandle_t uart_receive_task_handle = NULL;

Fruit fruit_list[FRUIT_LIST_LENGTH] = {
    {0, NOT_ENGAGED, 0, false, 0, false, false, 0}
};

myMotor conveyor_motor(CONVEYOR_MOTOR_PIN);
myStepper gripper_stepper(GRIPPER_STEPPER_PUL_PIN, GRIPPER_STEPPER_DIR_PIN, GRIPPER_STEPPER_ENABLE_PIN, GRIPPER_HOMING_SWITCH_PIN);
myServo gate_servo(GATE_SERVO_PIN);
myServo sorting_servo(SORTING_SERVO_PIN);
myPneumaticValve probe_valve(PROBE_CYLINDER_EXTEND_VALVE_PIN, PROBE_CYLINDER_RETRACT_VALVE_PIN);
myPneumaticValve gripper_valve(GRIPPER_CYLINDER_GRIP_VALVE_PIN, GRIPPER_CYLINDER_RELEASE_VALVE_PIN);
#include "Project-lib.h"

Fruit* search_fruit(long fruit_id) 
{
    for (int i = 0; i < FRUIT_LIST_LENGTH; i++) 
    {
        if (fruit_list[i].id == fruit_id) 
        {
            return &fruit_list[i];
        }
    }
    return nullptr;  // Return null pointer if not found
}

void reset_fruit(Fruit* f)
{
    if (f == nullptr) return;
    *f = {f->id + (sizeof(fruit_list) / sizeof(fruit_list[0])), NOT_ENGAGED, 0, false, 0, false, false, 0};
}

void process_sending_queue()
{
    if (messages_sending_queue == nullptr) return;

    Fruit_data msg;
    while (xQueueReceive(messages_sending_queue, &msg, 0) == pdTRUE)
    {
        String state_str;

        switch (msg.fruit_state)
        {
            case NOT_ENGAGED:        state_str = "NOT_ENGAGED"; break;
            case INPUT_ENTERED:      state_str = "INPUT_ENTERED"; break;
            case INPUT_PASSED:       state_str = "INPUT_PASSED"; break;
            case MEASURE_ENTERED:    state_str = "MEASURE_ENTERED"; break;
            case MEASURE_PROCESSING: state_str = "MEASURE_PROCESSING"; break;
            case MEASURE_PASSED:     state_str = "MEASURE_PASSED"; break;
            case SORTING_PASSED:     state_str = "SORTING_PASSED"; break;
            default:                 state_str = "UNKNOWN"; break;
        }

        Serial.print(msg.fruit_id);
        Serial.print("|");
        Serial.print(state_str);
        Serial.print("|");
        Serial.println(msg.payload);
    }
}

void initialize_system() 
{

    while (!Serial.available()) delay(10);

    String received_message = Serial.readStringUntil('\n');
    received_message.trim();
    
    if (received_message.startsWith("wake?")) 
    {
        Serial.println("awake");
    }
    
    while (true)
    {
        // Wait for confirmation message: "confirm|initial_fruit_id|preset_measurement_times|preset_conveyor_speed"
        while (!Serial.available()) delay(10);

        received_message = Serial.readStringUntil('\n');
        received_message.trim();

        // Example expected message: "confirm|3|12|50"
        if (received_message.startsWith("confirm|")) 
        {
            char message_buffer[64];
            received_message.toCharArray(message_buffer, sizeof(message_buffer));

            // Example message: "confirm|3|12|50"
            char* token = strtok(message_buffer, "|");  // "confirm"

            // Collect all data needed for initilization
            token = strtok(NULL, "|");                  // first data: initial fruit id
            if (token != NULL) initial_fruit = atol(token);
            token = strtok(NULL, "|");                  // second data: preset measurement times
            if (token != NULL) preset_measure_times = atoi(token);
            token = strtok(NULL, "|");                  // second data: preset measurement times
            if (token != NULL) preset_conveyor_speed = atoi(token);

            // Assign fruit IDs sequentially
            for (int i = 0; i < FRUIT_LIST_LENGTH; i++) fruit_list[i].id = initial_fruit + i;


            // Set current fruit IDs
            input_fruit_id = initial_fruit;
            measure_fruit_id = initial_fruit;
            sorting_fruit_id = initial_fruit;

            // Update fruit pointers
            input_fruit_pointer = search_fruit(initial_fruit);
            measure_fruit_pointer = search_fruit(initial_fruit);
            sorting_fruit_pointer = search_fruit(initial_fruit);

            // Sending queue initialization
            messages_sending_queue = xQueueCreate(15, sizeof(Fruit_data));

            Serial.println("initial fruit: " + String(initial_fruit) + 
                        " | preset_measure_times: " + String(preset_measure_times) + 
                        " | preset_conveyor_speed: " + String(preset_conveyor_speed));
            Serial.println("System initialized successfully! Starting system....");

            // Initialize hardware
            hardware_init();
            delay(1000);
            
            // Start all tasks
            system_start();
            delay(1000);

            Serial.println("System started");
            break;
        } 
        else 
        {
            Serial.println("Initialization failed: invalid confirmation message. (must be \"confirm|<fruit id>|<preset measure times>|<conveyor speed in %>\")");
        }
    }
}

void send_fruit_message(Fruit *fruit, int payload)
{
    Fruit_data msg;
    msg.fruit_id = fruit -> id;
    msg.fruit_state = fruit -> current_fruit_state;
    msg.payload = payload;

    xQueueSend(messages_sending_queue, &msg, 0);
}

void hardware_init()
{
    pinMode(INPUT_SENSOR_PIN, INPUT);
    pinMode(MEASURE_SENSOR_PIN, INPUT);
    pinMode(SORTING_SENSOR_PIN, INPUT);
    pinMode(GRIPPER_DETECT_CONTACT_SWITCH_PIN_1, INPUT_PULLUP);
    pinMode(GRIPPER_DETECT_CONTACT_SWITCH_PIN_2, INPUT_PULLUP);
    pinMode(PROBE_DETECT_CONTACT_SWITCH_PIN, INPUT_PULLUP);
    pinMode(GRIPPER_HOMING_SWITCH_PIN, INPUT_PULLUP);
}

void system_start()
{
    // --- Create main tasks ---
    xTaskCreatePinnedToCore(Input_Task, "Input_Task", 4096, NULL, 1, &input_task_handle, 1);
    xTaskCreatePinnedToCore(Measure_Task, "Measure_Task", 8000, NULL, 1, &measure_task_handle, 1);
    xTaskCreatePinnedToCore(Sorting_Task, "Sorting_Task", 4096, NULL, 1, &sorting_task_handle, 1);

    // --- Ensure UART task is running ---
    if (uart_receive_task_handle == NULL || eTaskGetState(uart_receive_task_handle) == eDeleted)
    xTaskCreatePinnedToCore(UartReceiveTask, "UartReceiveTask", 4096, NULL, 1, &uart_receive_task_handle, 1);

    // --- Initialize system hardware ---
    delay(200);

    gripper_release(true);
    probe_valve.position_B();
    vTaskDelay(2000 / portTICK_PERIOD_MS);
    probe_valve.position_A();
    vTaskDelay(200 / portTICK_PERIOD_MS);
    probe_valve.mid_position();
    gate_open();
    sorting_bin_write((SORTING_ANGLE_TYPE_1 + SORTING_ANGLE_TYPE_2) / 2);
    gripper_home();
    conveyor_run();

    printf("System started.\n");
}

void system_stop()
{
    // --- Stop all tasks except UART ---
    if (input_task_handle != NULL)
    {
        vTaskDelete(input_task_handle);
        input_task_handle = NULL;
    }

    if (measure_task_handle != NULL)
    {
        vTaskDelete(measure_task_handle);
        measure_task_handle = NULL;
    }

    if (sorting_task_handle != NULL)
    {
        vTaskDelete(sorting_task_handle);
        sorting_task_handle = NULL;
    }

    // Leave UART task alive because this function is called by it
    printf("System tasks stopped (UART task still running).\n");

    // --- Delete and reset queue ---
    if (messages_sending_queue != nullptr)
    {
        vQueueDelete(messages_sending_queue);
        messages_sending_queue = nullptr;
    }

    // --- Reset global variables ---
    preset_measure_times = 0;
    initial_fruit = 0;
    preset_conveyor_speed = 0;

    input_fruit_id = 0;
    input_fruit_pointer = nullptr;

    measure_fruit_id = 0;
    measure_fruit_pointer = nullptr;

    sorting_fruit_id = 0;
    sorting_fruit_pointer = nullptr;

    // --- Reset fruit list ---
    memset(fruit_list, 0, sizeof(fruit_list));
    fruit_list[0] = {0, NOT_ENGAGED, 0, false, 0, false, false, 0};

    myMotor conveyor_motor(CONVEYOR_MOTOR_PIN);
    myStepper gripper_stepper(GRIPPER_STEPPER_PUL_PIN, GRIPPER_STEPPER_DIR_PIN, GRIPPER_STEPPER_ENABLE_PIN, GRIPPER_HOMING_SWITCH_PIN);
    myServo gate_servo(GATE_SERVO_PIN);
    myServo sorting_servo(SORTING_SERVO_PIN);
    myPneumaticValve probe_valve(PROBE_CYLINDER_EXTEND_VALVE_PIN, PROBE_CYLINDER_RETRACT_VALVE_PIN);
    myPneumaticValve gripper_valve(GRIPPER_CYLINDER_GRIP_VALVE_PIN, GRIPPER_CYLINDER_RELEASE_VALVE_PIN);

    printf("All global variables reset.\n");

    initialize_system();
}


bool check_trigger(int sensor_pin)
{
    return !digitalRead(sensor_pin);
}

void conveyor_run()
{
    conveyor_motor.run(preset_conveyor_speed);
}

void conveyor_stop()
{
    conveyor_motor.run(0);
}

void gripper_position_fruit(int current_point)
{
    if ((preset_measure_times % 4) == 0)
    {
        if (current_point == 1)
        {
            gripper_grip();
        }
        else if (preset_measure_times == 4 || 
                (current_point > (preset_measure_times / 4) && 
                current_point % (preset_measure_times / 4) == 1))
        {
            gripper_stepper.run_by_angle((float) (90 - PRESET_ANGLE_BETWEEN_TWO_MEASUREMENT * ((preset_measure_times/4) - 1)), true);
            gripper_release(false);
            gripper_stepper.home(-1);

            gripper_grip();
            gripper_valve.mid_position();
        }
        else 
        {
            gripper_stepper.run_by_angle((float)PRESET_ANGLE_BETWEEN_TWO_MEASUREMENT, true);
        }
    }
    else
    {
        if (current_point == 1)
        {
            gripper_valve.position_A();
            while (check_trigger(GRIPPER_DETECT_CONTACT_SWITCH_PIN_1) == false || 
                check_trigger(GRIPPER_DETECT_CONTACT_SWITCH_PIN_2) == false) 
                vTaskDelay(10 / portTICK_PERIOD_MS);
            gripper_valve.mid_position();
        }
        else 
        {
            gripper_stepper.run_by_angle((float)PRESET_ANGLE_BETWEEN_TWO_MEASUREMENT, true);
        }
    }
}

void gripper_release(bool all_the_way)
{
    if (all_the_way)
    {
        gripper_valve.position_B();
        return;
    }
    else
    {
        gripper_valve.position_B();
        while (check_trigger(GRIPPER_DETECT_CONTACT_SWITCH_PIN_1) == true || 
            check_trigger(GRIPPER_DETECT_CONTACT_SWITCH_PIN_2) == true) 
            vTaskDelay(10 / portTICK_PERIOD_MS);
        gripper_valve.mid_position();
    }
}

void gripper_grip()
{
    gripper_valve.position_A();
    while (check_trigger(GRIPPER_DETECT_CONTACT_SWITCH_PIN_1) == false || 
        check_trigger(GRIPPER_DETECT_CONTACT_SWITCH_PIN_2) == false) 
        vTaskDelay(10 / portTICK_PERIOD_MS);
    gripper_valve.mid_position();
}

void gripper_home()
{
    gripper_stepper.home(-1);
}

void probe_attach()
{
    probe_valve.position_A();
    while (check_trigger(PROBE_DETECT_CONTACT_SWITCH_PIN) == false) vTaskDelay(10 / portTICK_PERIOD_MS);
    probe_valve.mid_position();
}

void probe_deattach(int measure_position)
{
    if (measure_position == preset_measure_times)
    {
        probe_valve.position_B();
        vTaskDelay(200 / portTICK_PERIOD_MS);
        probe_valve.mid_position();

    }
    else
    {
        probe_valve.position_B();
        while (check_trigger(PROBE_DETECT_CONTACT_SWITCH_PIN) == true) vTaskDelay(10 / portTICK_PERIOD_MS);
        vTaskDelay(100 / portTICK_PERIOD_MS);
        probe_valve.mid_position();
    }
}

void sorting_bin_write(int angle)
{
    sorting_servo.set_angle(angle);
}

void gate_open()
{
    gate_servo.set_angle(GATE_OPEN_ANGLE);
}

void gate_close()
{
    gate_servo.set_angle(GATE_CLOSE_ANGLE);
}
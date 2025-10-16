#include "Project-lib.h"

Fruit* search_fruit(long fruit_id) 
{
    for (int i = 0; i < 5; i++) 
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
    *f = {furthest_fruit, NOT_ENGAGED, 0, false, 0, false, false, 0};
    furthest_fruit++;
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
        Serial.println(msg.fruit_data);
    }
}

void initialize_system() 
{
    // Send initialization request to head computer
    Serial.println("initialize system");

    // Wait for confirmation message: "confirm|initial_fruit_id|preset_measurement|preset_conveyor_speed"
    while (!Serial.available()) delay(10);

    String received_message = Serial.readStringUntil('\n');
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
        for (int i = 0; i < 5; i++) fruit_list[i].id = initial_fruit + i;

        // Set furthest fruit
        furthest_fruit = fruit_list[4].id + 1;

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

        Serial.println("System initialized successfully. Please start!");
    } 
    else 
    {
        Serial.println("Initialization failed: invalid confirmation message.");
    }

    while (true) 
    {
        if (Serial.available()) 
        {
            String cmd = Serial.readStringUntil('\n');
            cmd.trim();

            if (cmd.equalsIgnoreCase("system start")) 
            {
                Serial.println("Starting system...");

                // Hardware_initialization
                hardware_init();
                // Start all tasks
                system_start();

                Serial.println("System started");
                break;
            }
        }

        delay(10);
    }
}

void send_fruit_message(long fruit_id, Fruit_state fruit_state, int fruit_data)
{
    if (messages_sending_queue == nullptr) return;

    Fruit_data msg;
    msg.fruit_id = fruit_id;
    msg.fruit_state = fruit_state;
    msg.fruit_data = fruit_data;

    xQueueSend(messages_sending_queue, &msg, 0);
}

void hardware_init()
{
    pinMode(INPUT_SENSOR_PIN, INPUT);
    pinMode(MEASURE_SENSOR_PIN, INPUT);
    pinMode(SORTING_SENSOR_PIN, INPUT);
    pinMode(GRIPPER_DETECT_CONTACT_SWITCH_PIN, INPUT_PULLUP);
    pinMode(PROBE_DETECT_CONTACT_SWITCH_PIN, INPUT_PULLUP);
    pinMode(GRIPPER_HOMING_SWITCH_PIN, INPUT_PULLUP);

    gripper_home(1);
    conveyor_run();
    
}

void system_start()
{
    xTaskCreatePinnedToCore(Input_Task, "Input_Task", 4096, NULL, 1, NULL, 1);
    xTaskCreatePinnedToCore(Measure_Task, "Measure_Task", 8000, NULL, 1, NULL, 1);
    xTaskCreatePinnedToCore(Sorting_Task, "Sorting_Task", 4096, NULL, 1, NULL, 1);
    xTaskCreatePinnedToCore(UartReceiveTask, "UartReceiveTask", 4096, NULL, 1, NULL, 1);

    delay(200);
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

void gripper_position_fruit(int measure_position)
{
    
    if (measure_position == 1)
    {
        gripper_valve.position_A();
        while (check_trigger(GRIPPER_DETECT_CONTACT_SWITCH_PIN) == false) vTaskDelay(10 / portTICK_PERIOD_MS);
        gripper_valve.mid_position();
    }
    else
    {
        if ((measure_position % (preset_measure_times / 4)) == 0) gripper_stepper.run_by_angle((float) (90 - PRESET_ANGLE_BETWEEN_TWO_MEASUREMENT), true);
        else gripper_stepper.run_by_angle((float)PRESET_ANGLE_BETWEEN_TWO_MEASUREMENT, true);
    }
    
}

void gripper_release()
{
    gripper_valve.position_B();
}

void gripper_home(bool homing_direction)
{
    gripper_stepper.home(homing_direction);
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
    }
    else
    {
        probe_valve.position_B();
        vTaskDelay(1000 / portTICK_PERIOD_MS);
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
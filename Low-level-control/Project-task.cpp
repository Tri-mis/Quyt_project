#include "Project-lib.h"

void Input_Task(void* parameter) 
{
    unsigned long start_time = 0;
    unsigned long stop_time = 0;
    bool measuring = false;
    bool trigger_state = false;

    for (;;) 
    {
        switch (input_task_state) 
        {
            case TRIGGER_WAIT:
                // Wait for the fruit to block the trigger sensor
                if (check_trigger(INPUT_SENSOR_PIN) && 
                    input_fruit_pointer != nullptr &&
                    input_fruit_pointer->current_fruit_state == NOT_ENGAGED) 
                {
                    input_fruit_pointer->current_fruit_state = INPUT_ENTERED;
                    send_fruit_message(input_fruit_pointer, NO_PAYLOAD);
                    input_task_state = MEASURING_DIA;
                }
                break;

            case MEASURING_DIA:
                trigger_state = check_trigger(INPUT_SENSOR_PIN);

                // Start timing when fruit enters
                if (measuring == false && trigger_state == true) 
                {
                    measuring = true;
                    start_time = millis();
                }

                // Stop timing when fruit leaves
                if (measuring == true && trigger_state == false) 
                {
                    stop_time = millis();
                    measuring = false;

                    // set the diameter and fruit state then report throught UART
                    input_fruit_pointer->dia_measure = stop_time - start_time;
                    input_fruit_pointer->current_fruit_state = INPUT_PASSED;
                    send_fruit_message(input_fruit_pointer, input_fruit_pointer->dia_measure);

                    // Move to next fruit
                    input_fruit_id++;
                    input_fruit_pointer = search_fruit(input_fruit_id);

                    // Close the input gate (servo control)
                    gate_close();

                    // update the task
                    input_task_state = TRIGGER_WAIT;
                }
                break;

            default:
                // Stay idle if an undefined state occurs
                vTaskDelay(10 / portTICK_PERIOD_MS);
                break;
        }
        vTaskDelay(1 / portTICK_PERIOD_MS); // small delay to prevent CPU overload
    }
}


void Measure_Task(void* parameter)
{
    // Initial state
    measure_task_state = TRIGGER_WAIT;

    unsigned long start_time = 0;
    bool measuring = false;

    unsigned long elapsed = 0;
    unsigned long half_time = 0;

    for (;;)
    {
        switch (measure_task_state)
        {
            case TRIGGER_WAIT:
            {
                if (check_trigger(MEASURE_SENSOR_PIN) && 
                    measure_fruit_pointer != nullptr && 
                    measure_fruit_pointer->current_fruit_state == INPUT_PASSED)
                {
                    // change fruit state and report through UART
                    measure_fruit_pointer->current_fruit_state = MEASURE_ENTERED;
                    send_fruit_message(measure_fruit_pointer, NO_PAYLOAD);

                    measure_task_state = CENTERING;
                }

                break;
            }

            case CENTERING:

                // Start measuring if not already
                if (measuring == false)
                {
                    // set measureing flag and start timming
                    measuring = true;
                    start_time = millis();
                }

                // calculate elapsed time
                elapsed = millis() - start_time;

                // If elapsed time * 2 >= dia_measure, stop conveyor
                if (elapsed * 2 >= measure_fruit_pointer->dia_measure)
                {
                    // stop conveyor
                    conveyor_stop();

                    // change fruit state and report through UART
                    measure_fruit_pointer->current_fruit_state = MEASURE_PROCESSING;
                    send_fruit_message(measure_fruit_pointer, NO_PAYLOAD);

                    // Reset measuring flag for next use
                    measuring = false;

                    // change state of task
                    measure_task_state = MEASURING_SPECTRAL;
                }

                break;

            case MEASURING_SPECTRAL:

                for (int current_point = 1; 
                    current_point <= preset_measure_times; 
                    current_point++)
                {
                    // actual measurement point start from 1
                    measure_fruit_pointer->point_measured = current_point;

                    // Prepare to take measurement
                    measure_fruit_pointer->point_measure_done = false;

                    // prepare for the scan according to the current point to scan
                    gripper_position_fruit(current_point);
                    probe_attach();

                    //expect respone with the same message to confirm the measureing is done
                    send_fruit_message(measure_fruit_pointer, current_point);

                    //wait until UART task set the point_measure_done to true
                    while (measure_fruit_pointer->point_measure_done == false)
                    {
                        // prevent watchdog reset
                        vTaskDelay(10 / portTICK_PERIOD_MS); 
                    }

                    // deattach probe but not all the way out
                    probe_deattach(current_point);
                }

                // release the current and get ready for the next fruit
                gripper_release(true);
                gripper_home();
                conveyor_run();
                gate_open();

                // Update fruit state to MEASURE_PASSED
                measure_fruit_pointer->current_fruit_state = MEASURE_PASSED;

                // expect response with the type of the fruit
                send_fruit_message(measure_fruit_pointer, NO_PAYLOAD);

                // Move to next fruit
                measure_fruit_id++;
                measure_fruit_pointer = search_fruit(measure_fruit_id);

                // change back state to trigger wait
                measure_task_state = TRIGGER_WAIT;

                break;

            default:

                // Undefined state
                vTaskDelay(10 / portTICK_PERIOD_MS);

                break;
        }
        // keep loop cooperative
        vTaskDelay(5 / portTICK_PERIOD_MS); 
    }
}


void Sorting_Task(void* parameter)
{
    // Initial state
    sorting_task_state = TRIGGER_WAIT;
    bool old_trigger_state = false;
    bool current_trigger_state = false;

    for (;;)
    {
        switch (sorting_task_state)
        {
            case TRIGGER_WAIT:
            {
                if (sorting_fruit_pointer == nullptr )
                {
                    vTaskDelay(10 / portTICK_PERIOD_MS);
                    break;
                }

                // Check fruit sorting type
                if (sorting_fruit_pointer->sorting_type == 0)
                {
                    // Not yet sorted — wait a little
                    vTaskDelay(10 / portTICK_PERIOD_MS);
                }
                else
                {
                    // Sorting type 1 or 2 → rotate bin servo to correct position
                    if (sorting_fruit_pointer->sorting_type == 1) sorting_bin_write(SORTING_ANGLE_TYPE_1);
                    else if (sorting_fruit_pointer->sorting_type == 2) sorting_bin_write(SORTING_ANGLE_TYPE_2);
                }

                // Get the current trigger state
                current_trigger_state = check_trigger(SORTING_SENSOR_PIN);

                // Check if fruit is detected at sorting sensor
                if (current_trigger_state != old_trigger_state &&
                    current_trigger_state == true)
                {
                    if (sorting_fruit_pointer -> current_fruit_state == MEASURE_PASSED)
                    {

                    // Update fruit state and report throught UART
                    sorting_fruit_pointer->current_fruit_state = SORTING_PASSED;
                    send_fruit_message(sorting_fruit_pointer, sorting_fruit_pointer->sorting_type);

                    // Reset fruit data for reuse
                    reset_fruit(sorting_fruit_pointer);

                    // Move to next fruit in process
                    sorting_fruit_id++;
                    sorting_fruit_pointer = search_fruit(sorting_fruit_id);
                    
                    // Update trigger state
                    

                    }
                    old_trigger_state = current_trigger_state;
                }
                break;
            }

            default:
            {
                // Undefined or idle state
                vTaskDelay(10 / portTICK_PERIOD_MS);
                break;
            }
        }

        // Cooperative delay
        vTaskDelay(1 / portTICK_PERIOD_MS);
    }
}


void UartReceiveTask(void* parameter)
{
    char buffer[64];
    int index = 0;

    for (;;)
    {
        // Read all available serial data
        while (Serial.available() > 0)
        {
            char c = Serial.read();

            if (c == '\n')
            {
                buffer[index] = '\0';
                index = 0;

                // Check for "stop" command first
                if (strcasecmp(buffer, "stop") == 0)
                {
                    Serial.println("Stop command received, stopping system...");
                    system_stop();
                    continue;
                }

                // Parse message like "123|MEASURE_PROCESSING|5"
                char* token = strtok(buffer, "|");
                if (token == NULL) continue;

                long id = atol(token);

                token = strtok(NULL, "|");
                if (token == NULL) continue;
                String state_str = String(token);

                token = strtok(NULL, "|");
                if (token == NULL) continue;
                int value = atoi(token);

                // Search for the fruit
                Fruit* f = search_fruit(id);
                if (f == nullptr) continue;

                // Update fields depending on message type
                if (state_str.equalsIgnoreCase("MEASURE_PROCESSING"))
                {
                    f->point_measure_done = true;
                }
                else if (state_str.equalsIgnoreCase("MEASURE_PASSED"))
                {
                    f->sorting_type = value;
                }
            }
            else if (index < sizeof(buffer) - 1)
            {
                buffer[index++] = c;
            }
        }

        vTaskDelay(10 / portTICK_PERIOD_MS);
    }
}

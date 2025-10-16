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
                if (check_trigger(INPUT_SENSOR_PIN)) 
                {
                    if (input_fruit_pointer != nullptr) 
                    {
                        input_fruit_pointer->current_fruit_state = INPUT_ENTERED;
                        send_fruit_message(input_fruit_pointer->id, input_fruit_pointer->current_fruit_state, -1);
                    }
                    input_task_state = MEASURING_DIA;
                }
                break;

            case MEASURING_DIA: 
                trigger_state = check_trigger(INPUT_SENSOR_PIN);

                // Start timing when fruit enters
                if (!measuring && trigger_state == true) 
                {
                    measuring = true;
                    start_time = millis();
                }

                // Stop timing when fruit leaves
                if (measuring && trigger_state == false) 
                {
                    stop_time = millis();
                    measuring = false;

                    if (input_fruit_pointer != nullptr) 
                    {
                        input_fruit_pointer->dia_measure = stop_time - start_time;
                        input_fruit_pointer->current_fruit_state = INPUT_PASSED;
                        send_fruit_message(input_fruit_pointer->id, input_fruit_pointer->current_fruit_state, input_fruit_pointer->dia_measure);
                    }

                    // Move to next fruit
                    input_fruit_id++;
                    input_fruit_pointer = search_fruit(input_fruit_id);

                    // Close the input gate (servo control)
                    gate_close();

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
                if (check_trigger(MEASURE_SENSOR_PIN))
                {
                    if (measure_fruit_pointer != nullptr)
                    {
                        measure_fruit_pointer->current_fruit_state = MEASURE_ENTERED;
                        send_fruit_message(measure_fruit_pointer->id, measure_fruit_pointer->current_fruit_state, -1);
                    }
                    measure_task_state = CENTERING;
                }
                break;
            }

            case CENTERING:

                // Start timing to wait until fruit is halfway through diameter sensor
                // Use fruit's dia_measure (in ms) to determine half time
                if (measure_fruit_pointer == nullptr)
                {
                    // Nothing to do if pointer invalid — go back to wait
                    measure_task_state = TRIGGER_WAIT;
                    break;
                }

                // Start measuring if not already
                if (!measuring)
                {
                    measuring = true;
                    start_time = millis();
                }

                // If elapsed time >= half of dia_measure, stop conveyor and move to spectral measurement
                elapsed = millis() - start_time;
                half_time = (unsigned long)(measure_fruit_pointer->dia_measure / 2);

                if (elapsed >= half_time)
                {
                    // stop conveyor
                    conveyor_stop();

                    if (measure_fruit_pointer != nullptr)
                    {
                        measure_fruit_pointer->current_fruit_state = MEASURE_PROCESSING;
                        send_fruit_message(measure_fruit_pointer->id, measure_fruit_pointer->current_fruit_state, -1);
                    }

                    // Reset measuring flag for next use
                    measuring = false;

                    measure_task_state = MEASURING_SPECTRAL;
                }
                break;

            case MEASURING_SPECTRAL:

                if (measure_fruit_pointer == nullptr)
                {
                    measure_task_state = TRIGGER_WAIT;
                    break;
                }

                for (int i = 1; i <= preset_measure_times; i++)
                {
                    // actual measurement point start from 1
                    measure_fruit_pointer->point_measured = i;
                    // Prepare to take measurement
                    measure_fruit_pointer->point_measure_done = false;

                    gripper_position_fruit(i);
                    probe_attach();

                    // send the fruit measuring point number, expect respone to confirm the measuring is done and set the point_measure_done to true
                    send_fruit_message(measure_fruit_pointer->id, measure_fruit_pointer->current_fruit_state, measure_fruit_pointer->point_measured);

                    while (!measure_fruit_pointer->point_measure_done)
                    {
                        // A short delay
                        vTaskDelay(10 / portTICK_PERIOD_MS);
                    }

                    probe_deattach(i);
                }

                gripper_home(1);
                conveyor_run();
                gate_open();

                // Update fruit state to MEASURE_PASSED
                measure_fruit_pointer->current_fruit_state = MEASURE_PASSED;
                send_fruit_message(measure_fruit_pointer->id, measure_fruit_pointer->current_fruit_state, -1); // when the main loop receive this message, it should response with the type of the fruit

                // Move to next fruit
                measure_fruit_id++;
                measure_fruit_pointer = search_fruit(measure_fruit_id);

                measure_task_state = TRIGGER_WAIT;

                break;

            default:
                // Undefined state
                vTaskDelay(10 / portTICK_PERIOD_MS);
                break;
        }
        vTaskDelay(5 / portTICK_PERIOD_MS); // keep loop cooperative
    }
}


void Sorting_Task(void* parameter)
{
    // Initial state
    sorting_task_state = TRIGGER_WAIT;
    bool old_trigger_state = true;
    bool current_trigger_state = true;

    for (;;)
    {
        switch (sorting_task_state)
        {
            case TRIGGER_WAIT:
            {

                if (sorting_fruit_pointer == nullptr)
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

                current_trigger_state = check_trigger(SORTING_SENSOR_PIN);

                // Check if fruit is detected at sorting sensor
                if (current_trigger_state != old_trigger_state)
                {
                    if (current_trigger_state )
                    {
                        // Update fruit state
                        sorting_fruit_pointer->current_fruit_state = SORTING_PASSED;
                        send_fruit_message( sorting_fruit_pointer->id, sorting_fruit_pointer->current_fruit_state, sorting_fruit_pointer->sorting_type);

                        // Reset fruit data for reuse
                        reset_fruit(sorting_fruit_pointer);

                        // Move to next fruit in process
                        sorting_fruit_id++;
                        sorting_fruit_pointer = search_fruit(sorting_fruit_id);
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
#include "Project-lib.h"

void SupervisorTask(void* parameter) 
{
    Fruit_data message;

    for (;;) 
    {
        for (int i = 0; i < 5; i++) 
        {
            // Skip empty slot
            if (fruit_list[i].id == 0) 
            {
                vTaskDelay(10 / portTICK_PERIOD_MS);
                continue;
            }

            Fruit* fruit = &fruit_list[i];

            // Skip if state hasn't changed
            if (fruit->current_fruit_state == fruit->previous_fruit_state) 
            {
                vTaskDelay(10 / portTICK_PERIOD_MS);
                continue;
            }

            // If fruit has finished sorting
            if (fruit->current_fruit_state == SORTING_PASSED) {
                // Send final report
                message.fruit_id = fruit->id;
                message.fruit_state = fruit->current_fruit_state;
                message.fruit_data = 0;
                xQueueSend(messages_sending_queue, &message, 0);

                // Reset fruit data
                fruit->id = furthest_fruit;
                fruit->previous_fruit_state = NOT_ENGAGED;
                fruit->current_fruit_state = NOT_ENGAGED;
                fruit->dia_measure = 0;
                fruit->is_centered = false;
                fruit->is_sorted = false;
                fruit->sorting_type = 0;
                fruit->point_measure_done = false;

                // Increment furthest fruit
                furthest_fruit++;
            } 
            else 
            {
                // Send progress update
                message.fruit_id = fruit->id;
                message.fruit_state = fruit->current_fruit_state;
                message.fruit_data = 0;
                xQueueSend(messages_sending_queue, &message, 0);

                // Update previous state
                fruit->previous_fruit_state = fruit->current_fruit_state;
            }
            vTaskDelay(10 / portTICK_PERIOD_MS);
        }
        // Small delay between full iterations
        vTaskDelay(10 / portTICK_PERIOD_MS);
    }
}


void InputTask(void* parameter) 
{
    unsigned long start_time = 0;
    unsigned long stop_time = 0;
    bool measuring = false;

    for (;;) 
    {
        switch (input_task_state) 
        {
            case TRIGGER_WAIT:
                // Wait for the fruit to block the trigger sensor
                if (check_input_trigger()) 
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
                bool trigger_state = check_input_trigger();

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
                        senf_fruit_message(input_fruit_pointer->id, input_fruit_pointer->current_fruit_state, input_fruit_pointer->dia_measure);
                    }

                    // Move to next fruit
                    input_fruit_id++;
                    input_fruit_pointer = search_fruit(input_fruit_id);

                    // Close the input gate (servo control)
                    servo_gate.write(CLOSED_ANGLE);

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



void MeasureTask(void* parameter)
{
    // Initial state
    measure_task_state = TRIGGER_WAIT;

    unsigned long start_time = 0;
    bool measuring = false;

    for (;;)
    {
        switch (measure_task_state)
        {
            case TRIGGER_WAIT:
            {
                if (check_measure_trigger())
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
                unsigned long elapsed = millis() - start_time;
                unsigned long half_time = (unsigned long)(measure_fruit_pointer->dia_measure / 2);

                if (elapsed >= half_time)
                {
                    // stop conveyor motor
                    conveyor_motor.stop();

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

                    gripper.position_fruit(i);
                    probe.attatch();

                    send_fruit_message(measure_fruit_pointer->id, measure_fruit_pointer->current_fruit_state, measure_fruit_pointer->point_measured);

                    const uint32_t wait_timeout_ms = 10000; // 10 seconds timeout (adjust as needed)
                    unsigned long wait_start = millis();
                    while (!measure_fruit_pointer->point_measure_done)
                    {
                        // A short delay
                        vTaskDelay(10 / portTICK_PERIOD_MS);

                        // Timeout check
                        if ((millis() - wait_start) >= wait_timeout_ms) break;
                    }

                    probe.deattch(i);
                }

                // Update fruit state to MEASURE_PASSED
                measure_fruit_pointer->current_fruit_state = MEASURE_PASSED;
                send_fruit_message(measure_fruit_pointer->id, measure_fruit_pointer->current_fruit_state, -1)

                // Move to next fruit
                measure_fruit_id++;
                measure_fruit_pointer = search_fruit(measure_fruit_id);

                measure_task_state = TRIGGER_WAIT;

                break;
            }

            default:
            {
                // Undefined state
                vTaskDelay(10 / portTICK_PERIOD_MS);
                break;
            }
        }

        vTaskDelay(1 / portTICK_PERIOD_MS); // keep loop cooperative
    }
}

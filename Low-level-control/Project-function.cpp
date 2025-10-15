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


void initialize_system() 
{
    // Send initialization request to head computer
    Serial.println("initialize system");

    // Wait for confirmation message: "confirm|initial_fruit_id|preset_measurement"
    while (!Serial.available()) delay(10);

    String received_message = Serial.readStringUntil('\n');
    received_message.trim();

    // Example expected message: "confirm|3|12"
    if (received_message.startsWith("confirm|")) 
    {
        // Split the message
        int first_sep = received_message.indexOf('|');
        int second_sep = received_message.indexOf('|', first_sep + 1);

        // Extract data
        String initial_fruit_str = received_message.substring(first_sep + 1, second_sep);
        String preset_measure_str = received_message.substring(second_sep + 1);

        // Convert to numbers
        initial_fruit = initial_fruit_str.toInt();
        preset_measure_times = preset_measure_str.toInt();

        // Assign fruit IDs sequentially
        for (int i = 0; i < 5; i++) 
        {
            fruit_list[i].id = initial_fruit + i;
        }

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
        messages_sending_queue = xQueueCreate(10, sizeof(Fruit_data));

        // Task creation
        xTaskCreatePinnedToCore(Input_Task, "Input_Task", 4096, NULL, 1, NULL, 1);
        xTaskCreatePinnedToCore(Measure_Task, "Measure_Task", 4096, NULL, 1, NULL, 1);
        xTaskCreatePinnedToCore(Sorting_Task, "Sorting_Task", 4096, NULL, 1, NULL, 1);
        xTaskCreatePinnedToCore(Supervisor_Task, "Supervisor_Task", 4096, NULL, 1, NULL, 1);

        Serial.println("System initialized successfully.");
    } 
    else 
    {
        Serial.println("Initialization failed: invalid confirmation message.");
    }
}

void send_fruit_message(Fruit* fruit_ptr)
{
    if (fruit_ptr == nullptr || messages_sending_queue == nullptr)
    {
        return;
    }

    Fruit_data msg;
    msg.fruit_id = fruit_ptr->id;
    msg.fruit_state = fruit_ptr->current_fruit_state;
    msg.fruit_data = 0; // the main loop or PC handler interprets the data

    xQueueSend(messages_sending_queue, &msg, 0);
}
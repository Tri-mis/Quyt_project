#include "Project-lib.h"

int preset_measure_times = 0;
long initial_fruit = 0;
long furthest_fruit = 0;

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

Fruit fruit_list[5] = 
{
  {0, NOT_ENGAGED, NOT_ENGAGED, 0, false, 0, false, false, 0},
  {0, NOT_ENGAGED, NOT_ENGAGED, 0, false, 0, false, false, 0},
  {0, NOT_ENGAGED, NOT_ENGAGED, 0, false, 0, false, false, 0},
  {0, NOT_ENGAGED, NOT_ENGAGED, 0, false, 0, false, false, 0},
  {0, NOT_ENGAGED, NOT_ENGAGED, 0, false, 0, false, false, 0}
};
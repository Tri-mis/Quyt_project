#pragma once

//============================================================== INCLUDE ==============================================================//
#include "Arduino.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"

//============================================================== DEFINE ==============================================================//

//============================================================== STATES ==============================================================//
enum Fruit_state {
  NOT_ENGAGED,
  INPUT_ENTERED,
  INPUT_PASSED,
  MEASURE_ENTERED,
  MEASURE_PROCESSING,
  MEASURE_PASSED,
  SORTING_PASSED
};

enum Task_state {
  TRIGGER_WAIT,
  MEASURING_DIA,
  CENTERING,
  MEASURING_SPECTRAL
};

//============================================================== FRUIT STRUCT ==============================================================//
struct Fruit {
  long id;                           // Fruit number
  Fruit_state current_fruit_state;   // Current state of the fruit
  Fruit_state previous_fruit_state;  // Previous state of the fruit
  long dia_measure;                  // Time taken to pass the diameter sensor
  bool is_centered;                  // Whether the fruit is centered at the measurement module
  unsigned int sorting_type;         // Type/category of the fruit
  bool is_sorted;                    // Whether the fruit has been sorted 
  bool point_measure_done;          // Whether a measurement point has been completed
  int point_measured;
};

//============================================================== FRUIT DATA STRUCT ==============================================================//
struct Fruit_data {
  long fruit_id;           // ID of the fruit
  Fruit_state fruit_state; // State of the fruit
  int fruit_data;          // Data value associated with the fruit
};

//============================================================== VARIABLE DECORATION ==============================================================//
extern int preset_measure_times;
extern long initial_fruit;
extern long furthest_fruit;

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

extern Fruit fruit_list[5];

//============================================================== FUNCTION DECORATION ==============================================================//
Fruit* search_fruit(long fruit_id);
void initialize_system();
void send_fruit_message(Fruit* fruit_ptr)


//============================================================== TASK DECORATION ==============================================================//
void SupervisorTask(void* parameter);
void InputTask(void* parameter);



=============================================== 13/10/25 ===============================================

- There are four tasks: InputTask, MeasureTask, SortingTask, SupervisorTask

- Each task has their own set of states, however an enum structure that has all the stats is defined globally.

- The communication with the computer will be caried out by the main loop using uart

- Each fruit is a struct that has these parameters:
    - id: this is a long parameter, telling the number of the fruit
    - current_fruit_state: this is an enum that tell what module is the fruit at (NOT_ENGAGED, INPUT_ENTERED, INPUT_PASSED, MEASURE_ENTERED, 
    MEASURE_PROCESSING, MEASURE_PASSED, SORTING_PASSED)
    - previous_fruit_state: same as current_fruit_state, but store the previous state
    - dia_measure: this is a long parameter, telling the time the fruit take to pass the diameter sensor
    - is_centered: a boolean parameter telling if the fruit is centered at the measure module or not
    - sorting_type: this is an unsigned int, it has the type of the fruit
    - is_sorted: a boolen parameter telling if the fruit is sorted
    - point_measure_done: this is a boolean that is used to track wherthere a point is measured

- global variables:
    - preset_measure_times = 0
    - initial_fruit = 0
    - furthest_fruit = 0
    - input_fruit_id = 0
    - input_fruit_pointer: this is a pointer to the Fruit object
    - measure_fruit_id = 0
    - measure_fruit_pointer: this is a pointer to the Fruit object
    - sorting_fruit_id = 0
    - sorting_fruit_pointer: this is a pointer to the Fruit object
    - messages_sending_queue: this is a queue of the data type
    - input_task_state 
    - measure_task_state
    - sorting_task_state

- At the start of the programe, a globle list of 5 fruit is initialised the same way:
    - id = 0 (fruit are always counted from 1, so 0 is set like a place holder)
    - previous_fruit_state: NOT_ENGAGED
    - current_fruit_state: NOT_ENGAGED
    - dia_measure = 0
    - is_centered: false
    - point_measured = 0
    - point_measured_done = false
    - is_sorted: false

- In setup, there is an initialization step, which will send a message to the head computer to ask for the initial fruit, and the preset_measure_time
 the initial fruit is set by user through interface on a head PC, let's say the initial fruit is fruit 3. 
 After receiving the imformation, the initialization function will:
    - set initial_fruit = 3
    - set the preset_measure_time
    - set the id of the first fruit in the fruit_list = the inital fruit number and the rest 
    with increment by one.
    - set the furthest_fruit = the largest id in the list + 1
    - set input_fruit_id = initial_fruit, measure_fruit_id = initial_fruit, sorting_fruit_id = initial_fruit
    - set the input_fruit_pointer, the measure_fruit_pointer and the sorting_fruit_pointer all pointing to the first fruit 
    in the fruit_list (it is the initial fruit)
    - begins SupervisorTask, InputTask, MeasureTask, and SortingTask

- The SupervisorTask:
    - It always check the fruit list, it continuously iterate through the list like this:
        - It first read the id of the fruit, if it is 0, leave a small delay then simply pass
        - If it is not 0 (let's take id = 3 for example) then it read the current_fruit_state of the fruit to see if it is different from 
        the previous_fruit_state or not if no, delay and pass, if yes then:
            - if it see the current_fruit_state = SORTING_PASSED
                - it add to the send queue a message to report the state of the fruit 3
                - it reset the object like this:
                    - id = furthest_fruit
                    - previous_fruit_state: NOT_ENGAGED
                    - current_fruit_state: NOT_ENGAGED
                    - dia_measure = 0
                    - is_centered: false
                    - is_sorted: false
                    - sorting_type = 0
                    - point_measure_done = false
                - then it increase the furthest_fruit by one
            - for all other cases of current_fruit_state:
                - it add to the messages_sending_queue a Fruit_data object with the fruit_id = fruit_id and the fruit_state = current_fruit_state, 
                leaving the fruit_data = 0 so that the main loop can report the state of the fruit 3
                - then it set the previous_fruit_state = current_fruit_state
            *note: it will never run into current_fruit_state = NOT_ENGAGE because from the start the condition check or 
            (current_fruit_state != previous_fruit_state) and because NOT_ENGAGE is the first ever state so when current_fruit_state = NOT_ENGAGE
            the previous_fruit_state = NOT_ENGAGE as well

- The InputTask:
    - When started, its state is input_task_state = TRIGGER_WAIT, in this state it wait for the fruit to block the diameter sensor, which
    is also its trigger sensor.
    - When input_task_state = TRIGGER_WAIT:
        - wait for the fruit to block the trigger sensor
        - When the fruit block the trigger sensor:
            - set the current_fruit_state = INPUT_ENTERED using the input_fruit_pointer
            - input_task_state = MEASURING_DIA
    - When input_task_state = MEASURING_DIA:
        - a timer is started (using the millis(), current_time, previsou_time continuous updating mechanism), and count the time the fruit 
        take to pass the diameter sensor
        - When the fruit pass the diameter sensor:
            - the timer stop, and the result is recorded in the dia_measure of the fruit object using the input_fruit_pointer
            - set the current_fruit_state = INPUT_PASSED using the input_fruit_pointer
            - the input_fruit_id is increased by one
            - search in the fruit_list and then change the input_fruit_pointer to point at the fruit_object that has the current input_fruit_id
            - close the input gate (its a servo) to avoid jamming
            - set input_task_state = TRIGGER_WAIT

- The MeasureTask:
    - Similarly, its state when started is measure_task_state = TRIGGER_WAIT, the sensor that trigger this task is called the centering sensor
    - when measure_task_state = TRIGGER_WAIT
        - Wait for the fruit to block the trigger sensor
        - When the fruit block the trigger sensor:
            - set the current_fruit_state = MEASURE_ENTERED using the measure_fruit_pointer
            - measure_task_state = CENTERING
    - When measure_task_state = CENTERING
        - a timer start 
        - When the count of the timer is half of the dia_measure of the fruit (accessed using the measure_fruit_pointer)
            - stop the conveyor (DC motor)
            - set the current_fruit_state = MEASURE_PROCESSING
            - measure_task_state = MEASURING_SPECTRAL
    - When measure_task_state = MEASURING_SPECTRAL
        - lower the gripper to grip the fruit (DC motor), stop the gripper when the limit switch is triggered (toching the fruit)
        - enable the spectral probe to approach the fruit (dc motor), stop it when the limit switch is triggered (touching the fruit)
        - set the point_measure_done = false
        - then leave the message in the queue, so that the main loop will send it to the pc which tell the NIR spectrometer to take measurement.
        - check if the point_measure_done = true
        - if yes, increase the point_measured by 1
        - then check if the point_measured = preset_measure_times
        - if no, retreat the spectral probe then spin the fruit to a new position (stepper motor)
        - then push the spectral probe again
        - repeat until point_measured = preset_measure_times then:
            - open the gripper completetly
            - set the current_fruit_state = MEASURE_PASSED using measure_fruit_pointer
            - the measure_fruit_id is increased by one
            - search in the fruit_list and then change the measure_fruit_pointer to point at the fruit_object that has the current measure_fruit_id
            - open the input gate (servo)
            - set measure_task_state = TRIGGER_WAIT
        
- The SortingTask:
    - Similarly, its state when started is sorting_task_state = TRIGGER_WAIT, the sensor that trigger this task is called the sorting sensor, the check_sorting_sensor()
    will return true if the fruit block the sensor
    - When sorting_task_state = TRIGGER_WAIT:
        - continuously read the sorting_type of the fruit (using the sorting_fruit_pointer), if the sorting_type = 0, it is not sorted yet, 
        so, give a small delay and do nothing, if it is  1, or 2 then spin the sorting bin (servo motor) to the correct type.
        - continuously check if the sensor is blocked
        - when the sorting sensor is blocked:
            - set the current_fruit_state = SORTING_PASSED using the sorting_fruit_pointer
            - send the information of the queue with the data = 0
            - reset the fruit:
                - id = furthest_fruit
                - previous_fruit_state: NOT_ENGAGED
                - current_fruit_state: NOT_ENGAGED
                - dia_measure = 0
                - is_centered: false
                - is_sorted: false
                - sorting_type = 0
                - point_measure_done = false
            - then it increase the furthest_fruit by one
            - the sorting_fruit_id is increased by one
            - search in the fruit_list and then change the sorting_fruit_pointer to point at the fruit_object that has the current sorting_fruit_id


- The main loop:
    - The loop will handle all UART communication, minimizing crashing the program by not letting FreeRTOS task do it.
    - Sending:
        - Message is packed under struct, they are placed in the mesasge_sending_queue, when there is a message in the queue, the main loop compose
        the sendign string and send it
    - Receiving:
        - Message is received through uart under string form, read this string and tack action upon it.











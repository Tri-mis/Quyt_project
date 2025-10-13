=============================================== 13/10/25 ===============================================

- There are four tasks: InputTask, MeasureTask, SortingTask, SupervisorTask

- Each task has their own states defined as under enumtype. A couple of states are similar between the tasks but they have different states, 
each of them need a specific defined of state. =======(I think an enum that has all the stats should be defined globally)

- The communication with the computer will be caried out by the main loop using uart
- Each fruit is a struct that has these parameters:
    - id: this is a long parameter, telling the number of the fruit
    - current_module_state: this is an enum that tell what module is the fruit at (NOT_ENGAGED, INPUT_ENTERED, INPUT_PASSED, MEASURE_ENTERED, 
    MEASURE_PASSED, SORTING_ENTERED, SORTING_PASSED)
    - previous_module_state: same as current_module_state, but store the previous state
    - dia_measure: this is a long parameter, telling the time the fruit take to pass the diameter sensor
    - is_centered: a boolean parameter telling if the fruit is centered at the measure module or not
    - is_sorted: a boolen parameter telling if the fruit is sorted

- global variables:
    - initial_fruit = 0
    - furthest_fruit = 0
    - input_expected_fruit = 0
    - input_processing_fruit = 0 ===== (may be this is not necessary)
    - input_ passed_fruit = 0  ===== (may be this is not necessary)
    - measure_expected_fruit = 0
    - measure_processing_fruit = 0
    - measure_passed_fruit = 0
    - sorting_processing_fruit = 0
    - sorting_passed_fruit = 0
    - a queue for sending messages
    - a queue for receiving messages
    - input_task_state
    - measure_task_state
    - sorting_task_state

- At the start of the programe, a globle list of 5 fruit is initialised the same way:
    - id = 0 (fruit are always counted from 1, so 0 is set like a place holder)
    - previous_module_state: NOT_ENGAGED
    - current_module_state: NOT_ENGAGED
    - dia_measure = 0
    - is_centered: false
    - is_sorted: false

- Then SupervisorTask put a message into the queue asking for the initial fruit number from the head computer. let's say the user set to start from 3
- The main loop when receive the answer it will:
    - set the initial_fruit = 3
    - set the id of the first fruit in the list = the inital fruit number and the rest 
    with increment by one.
    - set the input_expected_fruit = the initial fruit number.
    - set the furthest_fruit = the largest id of the list at that time.
    - it begins SupervisorTask, InputTask, MeasureTask, and SortingTask

- The SupervisorTask always check the fruit list, it continuously iterate through the list like this:
    - It first read the id of the fruit, if it is 0, leave a small delay then simply pass
    - If it is not 0 (let's take id = 3 for example) then it read the current_module_state of the fruit it see if it is different from 
    the previous_module_state or not if no, delay and pass, if yes then it leads to these cases:
        - if it see the current_module_state = INPUT_ENTERED
            => it set input_expected_fruit = 4
            => it add to the send queue a message to report the state of the fruit 3
            => it set the previous_module_state = current_module_state
        - if it see the current_module_state = INPUT_PASSED 
            => it set measure_expected_fruit = 3
            => it add to the send queue a message to report the state of the fruit 3
            => it set the previous_module_state = current_module_state
        - if it see the current_module_state = MEASURE_ENTERED 
            => it set measure_expected_fruit = 4
            => it add to the send queue a message to report the state of the fruit 3
            => it set the previous_module_state = current_module_state
        - if it see the current_module_state = MEASURE_PASSED 
            => it set sorting_expected_fruit = 3
            => it add to the send queue a message to report the state of the fruit 3
            => it set the previous_module_state = current_module_state
        - if it see the current_module_state = SORTING_ENTERED 
            => it set sorting_expected_fruit = 4
            => it add to the send queue a message to report the state of the fruit 3
            => it set the previous_module_state = current_module_state
        - if it see the current_module_state = SORTING_PASSED
            => it add to the send queue a message to report the state of the fruit 3
            => it reset the object like this:
                - id = furthest_fruit
                - previous_module_state: NOT_ENGAGED
                - current_module_state: NOT_ENGAGED
                - dia_measure = 0
                - is_centered: false
                - is_sorted: false
            => it increase the furthest_fruit by one
        - if it see the current_module_state = NOT_ENGAGED, simply pass

- First, for the InputTask:
    - When it begins, it is in WAIT_TRIGGER state, it simply asks if there is any fruit block the diameter sensor:
    - it also crea
        























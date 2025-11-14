#include "Project-lib.h"

void setup() 
{
  Serial.begin(115200);
  initialize_system();
}

void loop() 
{
  process_sending_queue();
  delay(10); 
}

#include <DigiCDC.h>
#include <string.h>

const uint8_t RELAY_PIN = 1;
const bool RELAY_ACTIVE_LOW = false;

char command[4];
uint8_t commandLength = 0;

void setRelay(bool enabled) {
  digitalWrite(RELAY_PIN, enabled ^ RELAY_ACTIVE_LOW ? HIGH : LOW);
}

void processCommand() {
  command[commandLength] = '\0';

  if (strcmp(command, "ON") == 0) {
    setRelay(true);
  } else if (strcmp(command, "OFF") == 0) {
    setRelay(false);
  }

  commandLength = 0;
}

void setup() {
  pinMode(RELAY_PIN, OUTPUT);
  setRelay(false);
  DigiCDC.begin();
}

void loop() {
  DigiCDC.refresh();

  while (DigiCDC.available()) {
    char value = DigiCDC.read();

    if (value == '\r') {
      continue;
    }

    if (value == '\n') {
      processCommand();
    } else if (commandLength < sizeof(command) - 1) {
      command[commandLength++] = value;
    } else {
      commandLength = 0;
    }
  }

  DigiCDC.delay(5);
}

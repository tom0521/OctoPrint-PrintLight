#include <DigiCDC.h>
#include <string.h>

const uint8_t LIGHT_RELAY_PIN = 1;
const uint8_t PSU_RELAY_PIN = 2;
const bool LIGHT_RELAY_ACTIVE_LOW = false;
const bool PSU_RELAY_ACTIVE_LOW = false;

char command[10];
uint8_t commandLength = 0;

void setRelay(uint8_t pin, bool activeLow, bool enabled) {
  digitalWrite(pin, enabled ^ activeLow ? HIGH : LOW);
}

void processCommand() {
  command[commandLength] = '\0';

  if (strcmp(command, "LIGHT ON") == 0) {
    setRelay(LIGHT_RELAY_PIN, LIGHT_RELAY_ACTIVE_LOW, true);
  } else if (strcmp(command, "LIGHT OFF") == 0) {
    setRelay(LIGHT_RELAY_PIN, LIGHT_RELAY_ACTIVE_LOW, false);
  } else if (strcmp(command, "PSU ON") == 0) {
    setRelay(PSU_RELAY_PIN, PSU_RELAY_ACTIVE_LOW, true);
  } else if (strcmp(command, "PSU OFF") == 0) {
    setRelay(PSU_RELAY_PIN, PSU_RELAY_ACTIVE_LOW, false);
  }

  commandLength = 0;
}

void setup() {
  pinMode(LIGHT_RELAY_PIN, OUTPUT);
  pinMode(PSU_RELAY_PIN, OUTPUT);
  setRelay(LIGHT_RELAY_PIN, LIGHT_RELAY_ACTIVE_LOW, false);
  setRelay(PSU_RELAY_PIN, PSU_RELAY_ACTIVE_LOW, false);
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

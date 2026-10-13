#include <Adafruit_MCP3008.h>

#include <SoftwareSerial.h>

#include <EEPROM.h>

#include <math.h>

// Version 3 Day 2 student sketch. Edit ONLY the marked exercise block.
// Positive motor command = wheel forward; negative = reverse; range -100..100.
// Six of eight learning modules are supplied (75% by module coverage).
struct MotorPair { int left; int right; };
MotorPair studentMotors(char movement, int speed);
char studentChoose(bool left, bool straight, bool right);

// BEGIN STUDENT EXERCISES
// Example: Incorrect: left pivot motor signs swapped
MotorPair studentMotors(char movement, int speed) {
  if (movement == 'F') return {speed, speed};
  if (movement == 'L') return {speed, -speed}; // BUG: these signs pivot right
  if (movement == 'R') return {speed, -speed};
  if (movement == 'B') return {speed, -speed};
  return {0, 0};
}
char studentChoose(bool left, bool straight, bool right) {
  if (left) return 'L';
  if (straight) return 'F';
  if (right) return 'R';
  return 'B';
}
// END STUDENT EXERCISES

// Filled automatically by Export passed Arduino sketch. Motors stay stopped
// on power-up; use the armed dashboard to start a real run.
const char WORKSHOP_REPLAY[] = "";
bool workshopLeft = false, workshopRight = false;
void workshopDrive(char movement, int speed);

Adafruit_MCP3008 adc;
SoftwareSerial bluetooth(9, 10); // RX, TX: motor and software SPI pins preserved
#define MAX_PATH 100
const uint8_t PWM1 = 5,
  INA1 = 2,
  INB1 = 3,
  PWM2 = 6,
  INA2 = 4,
  INB2 = 7,
  BUTTON = 8;
enum State {
  IDLE,
  CALIBRATION,
  MANUAL,
  SCAN,
  PATH_READY,
  RUN_PATH,
  PAUSED,
  STOPPED,
  ERROR
};
void stop(State s); // Prevent Arduino from generating this prototype before the State enum.
State state = IDLE, previous = IDLE;
Stream * link = & Serial;
char rawPath[101] = {
  0
}, shortPath[101] = {
  0
}, pending[101] = {
  0
};
uint8_t rawLength = 0, shortLength = 0, pathIndex = 0, pendingLength = 0, expectedLength = 0;
uint16_t low[8] = {
  100,
  100,
  100,
  100,
  100,
  100,
  100,
  100
}, high[8] = {
  800,
  800,
  800,
  800,
  800,
  800,
  800,
  800
};
uint16_t raw[8], norm[8];
int position = 3500, lastPosition = 0, error = 0, lastError = 0, leftMotor = 0, rightMotor = 0, threshold = 450, baseSpeed = 30;
float kp = .01, ki = 0, kd = .08, integral = 0, pTerm = 0, iTerm = 0, dTerm = 0, correction = 0;
uint16_t statusSequence = 0;
uint8_t controller = 2, background = 0, hz = 5, telemetryPart = 0;
unsigned long lastHeartbeat = 0, lastControl = 0, lastTelemetry = 0, phaseStart = 0, runStart = 0, manualDeadline = 0;
uint8_t phase = 0; // 0 follow, 1 probe, 2 pre-turn advance, 3 turn, 4 settle, 5 junction release
char turn = 'F';
uint16_t advanceMs = 0;
bool junctionLatched = false;
char serialBuf[80], btBuf[80];
uint8_t serialLen = 0, btLen = 0;
bool serialOverflow = false, btOverflow = false;
const uint16_t MAP_META = 128,
  MAP_DATA = 136,
  MAP_MAX = 888;
uint16_t mapExpected = 0, mapReceived = 0;
unsigned int previousId = 65535;
bool previousSuccess = false;
const __FlashStringHelper * modeName() {
  switch (state) {
  case IDLE:
    return F("IDLE");
  case CALIBRATION:
    return F("CALIBRATION");
  case MANUAL:
    return F("MANUAL");
  case SCAN:
    return F("SCAN");
  case PATH_READY:
    return F("PATH_READY");
  case RUN_PATH:
    return F("RUN_PATH");
  case PAUSED:
    return F("PAUSED");
  case STOPPED:
    return F("STOPPED");
  default:
    return F("ERROR");
  }
}
void Motors(int l, int r) {
  leftMotor = constrain(l, -100, 100);
  rightMotor = constrain(r, -100, 100);
  int vals[2] = {
    leftMotor,
    rightMotor
  };
  const uint8_t a[2] = {
      INA1,
      INA2
    },
    b[2] = {
      INB1,
      INB2
    },
    pwm[2] = {
      PWM1,
      PWM2
    };
  for (uint8_t i = 0; i < 2; i++) {
    digitalWrite(a[i], vals[i] < 0 ? HIGH : LOW);
    digitalWrite(b[i], vals[i] > 0 ? HIGH : LOW);
    analogWrite(pwm[i], abs(vals[i]) * 255 / 100);
  }
}
void workshopDrive(char movement, int speed) {
  MotorPair command = studentMotors(movement, speed);
  Motors(command.left, command.right);
}
void stop(State s) {
  Motors(0, 0);
  state = s;
  phase = 0;
  junctionLatched = false;
  integral = 0;
}
void event(const __FlashStringHelper * e) {
  link -> print(F("EVENT,"));
  link -> println(e);
}
void statusPacket() {
  link -> print(F("STATUS,"));
  link -> print(modeName());
  link -> print(',');
  link -> print(pathIndex);
  link -> print(',');
  link -> println(statusSequence++);
}
void configPacket() {
  link -> print(F("CONFIG,"));
  link -> print(controller);
  link -> print(',');
  link -> print(baseSpeed);
  link -> print(',');
  link -> print(threshold);
  link -> print(',');
  link -> print(background);
  link -> print(',');
  link -> println(hz);
}
void paths() {
  link -> print(F("PATH_RAW,"));
  link -> println(rawPath);
  link -> print(F("PATH_SHORT,"));
  link -> println(shortPath);
}
uint16_t checksum(const char * s) {
  uint16_t sum = 0;
  while ( * s) sum += (uint8_t) * s++;
  return sum;
}
int angle(char c) {
  return c == 'L' ? 270 : c == 'R' ? 90 : c == 'B' ? 180 : 0;
}
void optimize() {
  shortLength = 0;
  for (uint8_t i = 0; i < rawLength; i++) {
    shortPath[shortLength++] = rawPath[i];
    while (shortLength >= 3 && shortPath[shortLength - 2] == 'B' && shortPath[shortLength - 3] != 'B' && shortPath[shortLength - 1] != 'B') {
      int a = (angle(shortPath[shortLength - 3]) + 180 + angle(shortPath[shortLength - 1])) % 360;
      shortLength -= 3;
      shortPath[shortLength++] = a == 0 ? 'F' : a == 90 ? 'R' : a == 180 ? 'B' : 'L';
    }
  }
  shortPath[shortLength] = 0;
}
void Read() {
  unsigned long weighted = 0;
  unsigned int sum = 0;
  bool onLine = false;
  for (uint8_t i = 0; i < 8; i++) {
    raw[i] = adc.readADC(i);
    norm[i] = constrain(((long) raw[i] - low[i]) * 1000 / max(1, (int) high[i] - (int) low[i]), 0, 1000);
    if (background) norm[i] = 1000 - norm[i];
    if (norm[i] > 200) onLine = true;
    if (norm[i] > 50) {
      weighted += (unsigned long) norm[i] * i * 1000;
      sum += norm[i];
    }
  }
  position = onLine ? (int)(weighted / sum) : (lastPosition < 3500 ? 0 : 7000);
  if (onLine) lastPosition = position;
  error = position - 3500;
}
bool b(uint8_t i) {
  return background ? raw[i] < threshold : raw[i] > threshold;
}
bool w(uint8_t i) {
  return !b(i);
}
void Pid() {
  pTerm = kp * error;
  float nextIntegral = constrain(integral + error, -20000, 20000);
  iTerm = (controller == 1 || controller == 3) ? ki * nextIntegral : 0;
  dTerm = (controller == 2 || controller == 3) ? kd * (error - lastError) : 0;
  correction = pTerm + iTerm + dTerm;
  if (abs(correction) < 100 - baseSpeed) integral = nextIntegral; // anti-windup
  lastError = error;
  MotorPair forward = studentMotors('F', baseSpeed);
  Motors(forward.left + correction, forward.right - correction);
}
void beginTurn(char dir, uint16_t advance) {
  turn = dir;
  advanceMs = advance;
  phase = 2;
  phaseStart = millis();
  workshopDrive('F', baseSpeed);
}
void addDecision(char dir, uint16_t advance) {
  if (dir != 'L' && dir != 'F' && dir != 'R' && dir != 'B') {
    stop(ERROR);
    event(F("STUDENT_LSRB_INCOMPLETE"));
    return;
  }
  if (state == SCAN) {
    if (rawLength >= 100) {
      event(F("PATH_OVERFLOW"));
      stop(ERROR);
      return;
    }
    rawPath[rawLength++] = dir;
    rawPath[rawLength] = 0;
    link -> print(F("PATH_RAW,"));
    link -> println(rawPath);
  }
  link -> print(F("EVENT,JUNCTION,"));
  link -> println(dir);
  beginTurn(dir, advance);
}
void finish() {
  optimize();
  stop(PATH_READY);
  event(F("FINISH"));
  paths();
}
void robotTick() {
  unsigned long now = millis();
  if (state == CALIBRATION) {
    for (uint8_t i = 0; i < 8; i++) {
      low[i] = min(low[i], raw[i]);
      high[i] = max(high[i], raw[i]);
    }
    return;
  }
  if (state == MANUAL) {
    if (now > manualDeadline) {
      stop(STOPPED);
      event(F("MANUAL_TIMEOUT"));
    }
    return;
  }
  if (state != SCAN && state != RUN_PATH) return;
  if (phase == 1) {
    workshopDrive('F', baseSpeed);
    if (now - phaseStart < advanceMs) return;
    // A broad finish marker is supplied on the printable physical field.
    if (b(1) && b(2) && b(5) && b(6)) {
      if (state == SCAN) finish();
      else { stop(PATH_READY); event(F("FINISH")); }
      return;
    }
    addDecision(studentChoose(workshopLeft, b(2) || b(3) || b(4) || b(5), workshopRight), 0);
    return;
  }
  if (phase == 2) {
    workshopDrive('F', baseSpeed);
    if (now - phaseStart < advanceMs) return;
    phase = turn == 'F' ? 4 : 3;
    phaseStart = now;
  }
  if (phase == 3) {
    workshopDrive(turn, baseSpeed);
    if (now - phaseStart > 2500) {
      stop(ERROR);
      event(F("TURN_TIMEOUT"));
      return;
    }
    if (now - phaseStart >= 50 && norm[turn == 'L' ? 0 : 7] >= 100) {
      phase = 4;
      phaseStart = now;
    }
    return;
  }
  if (phase == 4) {
    Pid();
    if (now - phaseStart >= 50) {
      phase = 5;
      phaseStart = now;
    }
    return;
  }
  if (phase == 5) {
    Pid();
    if (now - phaseStart > 120 && !((b(0) && b(1)) || (b(6) && b(7)))) {
      phase = 0;
      junctionLatched = false;
    }
    return;
  }
  bool junction = (b(0) && b(1)) || (b(6) && b(7));
  if (junction && !junctionLatched) {
    junctionLatched = true;
    if (state == RUN_PATH) {
      if (pathIndex >= shortLength) {
        stop(PATH_READY);
        event(F("FINISH"));
        return;
      }
      char c = shortPath[pathIndex++];
      addDecision(c, c == 'F' ? 50 : c == 'B' ? 100 : 30);
      return;
    }
    workshopLeft = b(0) && b(1);
    workshopRight = b(6) && b(7);
    phase = 1;
    phaseStart = now;
    advanceMs = 30;
    workshopDrive('F', baseSpeed);
    return;
  } else if (w(2) && w(3) && w(4) && w(5)) {
    if (state == RUN_PATH) {
      if (pathIndex >= shortLength) {
        stop(PATH_READY);
        event(F("FINISH"));
        return;
      }
      if (shortPath[pathIndex++] != 'B') {
        stop(ERROR);
        event(F("PATH_MISMATCH"));
        return;
      }
    }
    addDecision(state == RUN_PATH ? 'B' : studentChoose(false, false, false), 100);
    return;
  }
  Pid();
}
void ack(unsigned int id,
  const char * cmd) {
  link -> print(F("ACK,"));
  link -> print(id);
  link -> print(',');
  link -> println(cmd);
}
void err(unsigned int id,
  const __FlashStringHelper * why) {
  link -> print(F("ERR,"));
  link -> print(id);
  link -> print(',');
  link -> println(why);
}
long number(const char * s, long fallback = -1) {
  if (!s || ! * s) return fallback;
  char * end;
  long n = strtol(s, & end, 10);
  return * end ? fallback : n;
}
uint16_t mapWord(uint16_t address) {
  uint16_t v;
  EEPROM.get(address, v);
  return v;
}
uint16_t mapSum(uint16_t n) {
  uint16_t sum = 0;
  for (uint16_t i = 0; i < n; i++) sum += EEPROM.read(MAP_DATA + i);
  return sum;
}
bool mapShape(uint16_t n) {
  uint8_t nodes = EEPROM.read(MAP_DATA + 1), edges = EEPROM.read(MAP_DATA + 2), start = EEPROM.read(MAP_DATA + 3), finish = EEPROM.read(MAP_DATA + 4);
  if (n < 19 || n > MAP_MAX || EEPROM.read(MAP_DATA) != 1 || nodes < 2 || nodes > 64 || edges < 1 || edges > 128 || start >= nodes || finish >= nodes || start == finish || n != 9 + 4 * nodes + 2 * edges || mapWord(MAP_DATA + 5) >= 3600 || !mapWord(MAP_DATA + 7)) return false;
  for (uint8_t i = 0; i < edges; i++) {
    uint16_t at = MAP_DATA + 9 + 4 * nodes + 2 * i;
    uint8_t a = EEPROM.read(at), b = EEPROM.read(at + 1);
    if (a >= nodes || b >= nodes || a == b) return false;
  }
  return true;
}
uint16_t savedMapLength() {
  uint16_t n = mapWord(MAP_META + 1);
  return EEPROM.read(MAP_META) == 0xC7 && mapShape(n) && mapSum(n) == mapWord(MAP_META + 3) ? n : 0;
}
void mapInfo() {
  uint16_t n = savedMapLength();
  link -> print(F("MAZE_INFO,"));
  link -> print(n);
  link -> print(',');
  link -> print(n ? mapSum(n) : 0);
  for (uint8_t i = 1; i <= 4; i++) {
    link -> print(',');
    link -> print(n ? EEPROM.read(MAP_DATA + i) : 0);
  }
  link -> print(',');
  link -> print(n ? mapWord(MAP_DATA + 5) : 0);
  link -> print(',');
  link -> print(n ? mapWord(MAP_DATA + 7) : 0);
  link -> print(',');
  link -> println(n ? 1 : 0);
}
int hexValue(char c) {
  return c >= '0' && c <= '9' ? c - '0' : c >= 'a' && c <= 'f' ? c - 'a' + 10 : c >= 'A' && c <= 'F' ? c - 'A' + 10 : -1;
}
void mapChunk(uint16_t offset, uint8_t n) {
  link -> print(F("MAZE_DATA,"));
  link -> print(offset);
  link -> print(',');
  for (uint8_t i = 0; i < n; i++) {
    uint8_t v = EEPROM.read(MAP_DATA + offset + i);
    if (v < 16) link -> print('0');
    link -> print(v, HEX);
  }
  link -> println();
}
void handle(char * buf, Stream & origin) {
  if (!strcmp_P(buf, PSTR("HEARTBEAT"))) {
    if (link == & origin) lastHeartbeat = millis();
    return;
  }
  char * save;
  char * p = strtok_r(buf, ",", & save);
  if (!p || strcmp_P(p, PSTR("C"))) return;
  char * idstr = strtok_r(NULL, ",", & save);
  char * cmd = strtok_r(NULL, ",", & save);
  if (!idstr || !cmd) return;
  unsigned int id = number(idstr, 65535);
  if (link != & origin) {
    if (state == SCAN || state == RUN_PATH || state == MANUAL) {
      origin.print(F("ERR,"));
      origin.print(id);
      origin.println(F(",BUSY_OTHER_TRANSPORT"));
      return;
    }
    link = & origin;
    previousId = 65535;
    hz = link == & Serial ? 10 : 5;
  }
  lastHeartbeat = millis();
  if (id == previousId && previousSuccess && strncmp_P(cmd, PSTR("GET_"), 4)) {
    ack(id, cmd);
    return;
  }
  previousId = id;
  previousSuccess = false;
  char * a = strtok_r(NULL, ",", & save);
  char * barg = strtok_r(NULL, ",", & save);
  char * c = strtok_r(NULL, ",", & save);
  bool moving = state == SCAN || state == RUN_PATH || state == MANUAL;
  bool ok = true;
  if (!strcmp_P(cmd, PSTR("STOP")) || !strcmp_P(cmd, PSTR("RESET"))) stop(!strcmp_P(cmd, PSTR("RESET")) ? IDLE : STOPPED);
  else if (!strcmp_P(cmd, PSTR("PING"))) link -> println(F("PONG"));
  else if (!strcmp_P(cmd, PSTR("GET_STATUS"))) {
    link -> println(F("HELLO,MAZE_WORKSHOP_V3,1"));
    statusPacket();
    paths();
    configPacket();
  } else if (!strcmp_P(cmd, PSTR("GET_SENSORS"))) {
    link -> print(F("SENSOR"));
    for (uint8_t i = 0; i < 8; i++) {
      link -> print(',');
      link -> print(raw[i]);
    }
    link -> println();
  } else if (!strcmp_P(cmd, PSTR("GET_PATH"))) {
    link -> print(F("PATH_RAW,"));
    link -> println(rawPath);
  } else if (!strcmp_P(cmd, PSTR("GET_SHORT_PATH"))) {
    link -> print(F("PATH_SHORT,"));
    link -> println(shortPath);
  } else if (!strcmp_P(cmd, PSTR("GET_CAL"))) {
    link -> print(F("CAL"));
    for (uint8_t i = 0; i < 16; i++) {
      link -> print(',');
      link -> print(i < 8 ? low[i] : high[i - 8]);
    }
    link -> println();
  } else if (!strcmp_P(cmd, PSTR("START_SCAN"))) {
    if (moving || state == PAUSED || mapExpected) ok = false;
    else {
      rawLength = 0;
      rawPath[0] = 0;
      pathIndex = 0;
      phase = 0;
      state = SCAN;
      runStart = millis();
      lastError = 0;
      integral = 0;
    }
  } else if (!strcmp_P(cmd, PSTR("START_RUN"))) {
    if (moving || state == PAUSED || mapExpected || !shortLength) ok = false;
    else {
      state = RUN_PATH;
      pathIndex = 0;
      phase = 0;
      runStart = millis();
      lastError = 0;
      integral = 0;
    }
  } else if (!strcmp_P(cmd, PSTR("PAUSE"))) {
    if (moving) {
      previous = state;
      state = PAUSED;
      Motors(0, 0);
    } else ok = false;
  } else if (!strcmp_P(cmd, PSTR("RESUME"))) {
    if (state == PAUSED && !mapExpected) {
      state = previous;
      phaseStart = millis();
      manualDeadline = millis() + 400;
    } else ok = false;
  } else if (!strcmp_P(cmd, PSTR("DRIVE"))) {
    long l = number(a, 999), r = number(barg, 999);
    if (mapExpected || state == SCAN || state == RUN_PATH || abs(l) > 100 || abs(r) > 100) ok = false;
    else {
      state = MANUAL;
      Motors(l, r);
      manualDeadline = millis() + 400;
    }
  } else if (!strcmp_P(cmd, PSTR("SET_PID"))) {
    if (!a || !barg || !c) ok = false;
    else {
      char * ea, * eb, * ec;
      float x = strtod(a, & ea), y = strtod(barg, & eb), z = strtod(c, & ec);
      if ( * ea || * eb || * ec || ea == a || eb == barg || ec == c || !isfinite(x) || !isfinite(y) || !isfinite(z) || x < 0 || y < 0 || z < 0 || x > 1 || y > 1 || z > 2) ok = false;
      else {
        kp = x;
        ki = y;
        kd = z;
        integral = 0;
      }
    }
  } else if (!strcmp_P(cmd, PSTR("SET_CONTROLLER"))) {
    long v = number(a);
    if (v < 0 || v > 3) ok = false;
    else controller = v;
  } else if (!strcmp_P(cmd, PSTR("SET_SPEED"))) {
    long v = number(a);
    if (v < 0 || v > 100) ok = false;
    else baseSpeed = v;
  } else if (!strcmp_P(cmd, PSTR("SET_THRESHOLD"))) {
    long v = number(a);
    if (v < 0 || v > 1023) ok = false;
    else threshold = v;
  } else if (!strcmp_P(cmd, PSTR("SET_BACKGROUND"))) {
    long v = number(a);
    if (v < 0 || v > 1) ok = false;
    else background = v;
  } else if (!strcmp_P(cmd, PSTR("SET_TELEMETRY"))) {
    long v = number(a);
    if (v != 5 && v != 10 && v != 20) ok = false;
    else if (link != & Serial && v > 5) ok = false;
    else hz = v;
  } else if (!strcmp_P(cmd, PSTR("SET_CAL"))) {
    long index = number(a), lo = number(barg), hi = number(c);
    if (index < 0 || index > 7 || lo < 0 || hi > 1023 || hi <= lo) ok = false;
    else {
      low[index] = lo;
      high[index] = hi;
    }
  } else if (!strcmp_P(cmd, PSTR("CAL_START"))) {
    if (moving || mapExpected) ok = false;
    else {
      state = CALIBRATION;
      for (uint8_t i = 0; i < 8; i++) {
        low[i] = 1023;
        high[i] = 0;
      }
    }
  } else if (!strcmp_P(cmd, PSTR("CAL_END"))) {
    for (uint8_t i = 0; i < 8; i++)
      if (high[i] <= low[i]) ok = false;
    if (ok) state = IDLE;
  } else if (!strcmp_P(cmd, PSTR("CLEAR_PATH"))) {
    if (moving) ok = false;
    else {
      rawLength = shortLength = 0;
      rawPath[0] = shortPath[0] = 0;
    }
  } else if (!strcmp_P(cmd, PSTR("PATH_BEGIN"))) {
    long n = number(a);
    if (moving || n < 1 || n > 100) ok = false;
    else {
      expectedLength = n;
      pendingLength = 0;
      pending[0] = 0;
    }
  } else if (!strcmp_P(cmd, PSTR("PATH_CHUNK"))) {
    long offset = number(a);
    if (moving || offset != pendingLength || !barg || pendingLength + strlen(barg) > expectedLength) ok = false;
    else {
      for (uint8_t i = 0; barg[i]; i++)
        if (!strchr_P(PSTR("LFRB"), barg[i])) ok = false;
      if (ok) {
        strcpy(pending + pendingLength, barg);
        pendingLength += strlen(barg);
      }
    }
  } else if (!strcmp_P(cmd, PSTR("PATH_END"))) {
    if (moving || pendingLength != expectedLength || checksum(pending) != number(a)) ok = false;
    else {
      strcpy(shortPath, pending);
      shortLength = pendingLength;
      state = PATH_READY;
      link -> print(F("PATH_SHORT,"));
      link -> println(shortPath);
      link -> print(F("PATH_STORED,"));
      link -> println(shortLength);
    }
  } else if (!strcmp_P(cmd, PSTR("SAVE_PATH"))) {
    if (moving) ok = false;
    else {
      EEPROM.update(0, 0xA5);
      EEPROM.update(1, shortLength);
      for (uint8_t i = 0; i < shortLength; i++) EEPROM.update(i + 2, shortPath[i]);
      EEPROM.put(102, checksum(shortPath));
    }
  } else if (!strcmp_P(cmd, PSTR("LOAD_PATH"))) {
    if (moving || EEPROM.read(0) != 0xA5) ok = false;
    else {
      uint8_t n = EEPROM.read(1);
      if (n > 100) ok = false;
      else {
        for (uint8_t i = 0; i < n; i++) pending[i] = EEPROM.read(i + 2);
        pending[n] = 0;
        uint16_t crc;
        EEPROM.get(102, crc);
        if (checksum(pending) != crc) ok = false;
        else {
          strcpy(shortPath, pending);
          shortLength = n;
          state = PATH_READY;
          paths();
        }
      }
    }
  } else if (!strcmp_P(cmd, PSTR("GET_MAZE_INFO"))) mapInfo();
  else if (!strcmp_P(cmd, PSTR("GET_MAZE_CHUNK"))) {
    long offset = number(a), n = number(barg);
    uint16_t len = savedMapLength();
    if (offset < 0 || n < 1 || n > 16 || offset + n > len) ok = false;
    else mapChunk(offset, n);
  } else if (!strcmp_P(cmd, PSTR("MAZE_BEGIN"))) {
    long n = number(a);
    if (moving || state == PAUSED || state == CALIBRATION || n < 19 || n > MAP_MAX) ok = false;
    else {
      EEPROM.update(MAP_META, 0);
      mapExpected = n;
      mapReceived = 0;
    }
  } else if (!strcmp_P(cmd, PSTR("MAZE_CHUNK"))) {
    long offset = number(a);
    uint8_t chars = barg ? strlen(barg) : 0;
    if (moving || !mapExpected || offset != mapReceived || !chars || chars > 32 || chars % 2 || mapReceived + chars / 2 > mapExpected) ok = false;
    else {
      for (uint8_t i = 0; i < chars; i++)
        if (hexValue(barg[i]) < 0) ok = false;
      if (ok) {
        for (uint8_t i = 0; i < chars; i += 2) EEPROM.update(MAP_DATA + mapReceived++, hexValue(barg[i]) * 16 + hexValue(barg[i + 1]));
      }
    }
  } else if (!strcmp_P(cmd, PSTR("MAZE_END"))) {
    long sum = number(a);
    if (moving || !mapExpected || mapReceived != mapExpected || sum != mapSum(mapExpected) || !mapShape(mapExpected)) ok = false;
    else {
      EEPROM.put(MAP_META + 1, mapExpected);
      uint16_t crc = sum;
      EEPROM.put(MAP_META + 3, crc);
      EEPROM.update(MAP_META, 0xC7);
      mapExpected = mapReceived = 0;
      mapInfo();
    }
  } else if (!strcmp_P(cmd, PSTR("MAZE_ABORT")) || !strcmp_P(cmd, PSTR("CLEAR_MAZE"))) {
    if (moving || state == PAUSED || state == CALIBRATION) ok = false;
    else {
      EEPROM.update(MAP_META, 0);
      mapExpected = mapReceived = 0;
      mapInfo();
    }
  } else ok = false;
  if (ok) {
    previousSuccess = true;
    ack(id, cmd);
    if (!strncmp_P(cmd, PSTR("SET_"), 4)) configPacket();
  } else err(id, F("INVALID_OR_BUSY"));
}
void poll(Stream & s, char * buf, uint8_t & length, bool & overflow) {
  uint8_t limit = 32;
  while (s.available() && limit--) {
    char c = s.read();
    if (c == '\r') continue;
    if (c == '\n') {
      if (!overflow) {
        buf[length] = 0;
        handle(buf, s);
      }
      length = 0;
      overflow = false;
    } else if (length < 79 && !overflow) buf[length++] = c;
    else {
      overflow = true;
      length = 0;
    }
  }
}
void telemetry() {
  // USB has bandwidth for full frames; HC-05 sends one packet per tick (round robin).
  uint8_t count = link == & Serial ? 4 : 1;
  for (uint8_t packet = 0; packet < count; packet++) {
    switch (telemetryPart++ % 4) {
    case 0:
      link -> print(F("SENSOR"));
      for (uint8_t i = 0; i < 8; i++) {
        link -> print(',');
        link -> print(raw[i]);
      }
      link -> println();
      break;
    case 1:
      link -> print(F("NORM"));
      for (uint8_t i = 0; i < 8; i++) {
        link -> print(',');
        link -> print(norm[i]);
      }
      link -> println();
      break;
    case 2:
      link -> print(F("CTRL,"));
      link -> print(position);
      link -> print(',');
      link -> print(error);
      link -> print(',');
      link -> print(pTerm, 2);
      link -> print(',');
      link -> print(iTerm, 2);
      link -> print(',');
      link -> print(dTerm, 2);
      link -> print(',');
      link -> print(correction, 2);
      link -> print(',');
      link -> print(leftMotor);
      link -> print(',');
      link -> print(rightMotor);
      link -> print(',');
      link -> print(kp, 4);
      link -> print(',');
      link -> print(ki, 4);
      link -> print(',');
      link -> print(kd, 4);
      link -> print(',');
      link -> println(millis() - runStart);
      break;
    case 3:
      statusPacket();
      break;
    }
  }
}
void setup() {
  Serial.begin(115200);
  bluetooth.begin(9600);
  adc.begin(A0, A1, A2, A3);
  pinMode(PWM1, OUTPUT);
  pinMode(INA1, OUTPUT);
  pinMode(INB1, OUTPUT);
  pinMode(PWM2, OUTPUT);
  pinMode(INA2, OUTPUT);
  pinMode(INB2, OUTPUT);
  pinMode(BUTTON, INPUT_PULLUP);
  Motors(0, 0);
  if (sizeof(WORKSHOP_REPLAY) > 1 && sizeof(WORKSHOP_REPLAY) <= MAX_PATH + 1) {
    strcpy(shortPath, WORKSHOP_REPLAY);
    shortLength = sizeof(WORKSHOP_REPLAY) - 1;
    state = PATH_READY;
  }
  Serial.println(F("HELLO,MAZE_WORKSHOP_V3,1"));
  lastHeartbeat = millis();
}
void loop() {
  poll(Serial, serialBuf, serialLen, serialOverflow);
  poll(bluetooth, btBuf, btLen, btOverflow);
  unsigned long now = millis();
  if ((state == SCAN || state == RUN_PATH || state == MANUAL || state == PAUSED) && now - lastHeartbeat > 1500) {
    stop(STOPPED);
    event(F("LINK_TIMEOUT"));
  }
  static bool buttonWasHigh = true;
  bool buttonHigh = digitalRead(BUTTON);
  if (buttonWasHigh && !buttonHigh) {
    stop(STOPPED);
    event(F("BUTTON_STOP"));
  }
  buttonWasHigh = buttonHigh;
  if (now - lastControl >= 10) {
    lastControl = now;
    Read();
    robotTick();
  }
  if (now - lastTelemetry >= 1000 / hz) {
    lastTelemetry = now;
    telemetry();
  }
}
#include <Adafruit_MCP3008.h>
Adafruit_MCP3008 adc;

#define PWM1 5
#define INA1 2
#define INB1 3
#define PWM2 6
#define INA2 4
#define INB2 7

#define MAX_PATH 100

char path[MAX_PATH];
int pathLength = 0;

char shortest_path[MAX_PATH];
int shortestPathLength = 0;

const int NumSensors = 8;
int Max[NumSensors] = { 800, 800, 800, 800, 800, 800, 800, 800 };
int Min[NumSensors] = { 100, 100, 100, 100, 100, 100, 100, 100 };

long SensorValue[NumSensors];
int BackGround = 0, LastValue = 0;
int Error, LastError, LeftMotor, RightMotor, PowerMotor, Position, allWhite = 0;
int BaseSpeed; float Kp, Kd;

void initt() {
  Serial.begin(9600);
  adc.begin(A0, A1, A2, A3);
  pinMode(PWM1, OUTPUT);
  pinMode(INA1, OUTPUT);
  pinMode(INB1, OUTPUT);
  pinMode(PWM2, OUTPUT);
  pinMode(INA2, OUTPUT);
  pinMode(INB2, OUTPUT);
}

void AddPath(char dir) {
  if (pathLength < MAX_PATH) {
    path[pathLength] = dir;
    pathLength++;
  }
}

void CalculateShortestPath() {
  shortestPathLength = 0;
  for (int i = 0; i < pathLength; i++) {
    shortest_path[shortestPathLength++] = path[i];
    if (shortestPathLength >= 3) {
      char a = shortest_path[shortestPathLength - 3];
      char b = shortest_path[shortestPathLength - 2];
      char c = shortest_path[shortestPathLength - 1];
      char newPath = 0;
      
      if (a == 'L' && b == 'B' && c == 'L') newPath = 'F';
      else if (a == 'L' && b == 'B' && c == 'F') newPath = 'R';
      else if (a == 'L' && b == 'B' && c == 'R') newPath = 'B';
      else if (a == 'F' && b == 'B' && c == 'L') newPath = 'R';
      else if (a == 'F' && b == 'B' && c == 'F') newPath = 'B';
      else if (a == 'F' && b == 'B' && c == 'R') newPath = 'L';
      else if (a == 'R' && b == 'B' && c == 'L') newPath = 'B';
      else if (a == 'R' && b == 'B' && c == 'F') newPath = 'L';
      else if (a == 'R' && b == 'B' && c == 'R') newPath = 'F';

      if (newPath != 0) { shortestPathLength -= 3; shortest_path[shortestPathLength++] = newPath; }
    }
  }
}

void setup() {
  initt();

  // View();
  // ViewReadLine();

  while(!digitalRead(8) == 1); delay(500);

  BaseSpeed = 30; Kp = 0.01; Kd = 0.08;
  TrackMaze();

  while(!digitalRead(8) == 1); delay(500);

  BaseSpeed = 32; Kp = 0.01; Kd = 0.1;
  RunShortestPath();
}

void loop() {
  Motors(0, 0);
}

bool w(int pin) { if(adc.readADC(pin) < 450) return true; return false; }
bool b(int pin) { if(adc.readADC(pin) > 450) return true; return false; }

void TrackMaze() {
  while (true) {
    if ((b(0) && b(1)) || (b(6) && b(7))) {
      if (b(0) && b(1) && b(2) && w(5) && w(6) && w(7)) { LL(30); AddPath('L'); }
      else if (b(1) && b(2) && b(5) && b(6)) {
        FF(30);
        if (b(1) && b(6)) {
          FF(60); Motors(0, 0);

          CalculateShortestPath();
          return;
        }
        else { LL(0); AddPath('L'); }
      }
      else if (w(0) && w(1) && w(2) && b(5) && b(6) && b(7)) {
        FF(20);
        if (b(2) || b(3) || b(4) || b(5)) AddPath('F');
        else { RR(0); AddPath('R'); }
      }
    }
    else if (w(2) && w(3) && w(4) && w(5)) { Uturn(); AddPath('B'); }
    Pid(BaseSpeed, Kp, Kd);
  }
}

void RunShortestPath() {
  int pathIdx = 0;
  while (true) {
    if ((b(0) && b(1)) || (b(6) && b(7))) {
      if (pathIdx >= shortestPathLength) { Motors(0, 0); return; }

      char dir = shortest_path[pathIdx];
      pathIdx++;

      if (dir == 'L') LL(30);
      else if (dir == 'R') RR(30);
      else if (dir == 'F') FF(50);
      else if (dir == 'B') Uturn();
    }
    Pid(BaseSpeed, Kp, Kd);
  }
}

void FF(long Time) {
  Move(BaseSpeed, BaseSpeed, Time);
}

void LL(long Time) {
  FF(Time);
  Move(-BaseSpeed, BaseSpeed, 50);
  Read();
  while (SensorValue[0] < 100) {
    Move(-BaseSpeed, BaseSpeed, 0); Read();
  }
  PidTime(BaseSpeed, Kp, Kd, 50);
}

void RR(long Time) {
  FF(Time);
  Move(BaseSpeed, -BaseSpeed, 50);
  Read();
  while (SensorValue[7] < 100) {
    Move(BaseSpeed, -BaseSpeed, 0); Read();
  }
  PidTime(BaseSpeed, Kp, Kd, 50);
}

void Uturn() {
  FF(100);
  Move(BaseSpeed, -BaseSpeed, 50);
  Read();
  while (SensorValue[7] < 100) {
    Move(BaseSpeed, -BaseSpeed, 0); Read();
  }
  PidTime(BaseSpeed, Kp, Kd, 50);
}

void Motors(int PowL, int PowR) {
  PowL = (PowL * 255) / 100;
  PowR = (PowR * 255) / 100;
  if (PowL > 0) {
    digitalWrite(INA1, LOW);
    digitalWrite(INB1, HIGH);
    analogWrite(PWM1, PowL);
  } else if (PowL == 0) {
    digitalWrite(INA1, HIGH);
    digitalWrite(INB1, HIGH);
    analogWrite(PWM1, 255);
  } else {
    digitalWrite(INA1, HIGH);
    digitalWrite(INB1, LOW);
    analogWrite(PWM1, -PowL);
  }

  if (PowR > 0) {
    digitalWrite(INA2, LOW);
    digitalWrite(INB2, HIGH);
    analogWrite(PWM2, PowR);
  } else if (PowR == 0) {
    digitalWrite(INA2, HIGH);
    digitalWrite(INB2, HIGH);
    analogWrite(PWM2, 0);
  } else {
    digitalWrite(INA2, HIGH);
    digitalWrite(INB2, LOW);
    analogWrite(PWM2, -PowR);
  }
}

void Move(int PowL, int PowR, long Time) {
  Motors(PowL, PowR); delay(Time);
}

void ReadPrivate() {
  for (int i = 0; i < NumSensors; i++) {
    SensorValue[i] = adc.readADC(i);
  }
}

void Read() {
  ReadPrivate();
  for (unsigned char i = 0; i < NumSensors; i++) {
  SensorValue[i] = map(SensorValue[i] , Min[i], Max[i] , 0, 1000);
  if (SensorValue[i] > 1000) SensorValue[i] = 1000;
  else if (SensorValue[i] < 0) SensorValue[i] = 0;
  }
}

int ReadLine() {
  int on_line = 0;
  unsigned long avg = 0;
  unsigned int sum = 0;
  unsigned long value = 0;
  on_line = 0;
  Read();
  avg = 0;
  sum = 0;
  for (int i = 0; i < NumSensors; i++) {
    value = SensorValue[i];
    if (BackGround == 1) {
      value = 1000 - value;
      SensorValue[i] = value;
    }
    if (value > 200) on_line = 1;
    if (value > 50) {
      avg += value * (i * 1000);
      sum += value;
    }
  }
  if (on_line == 0) {
    if (LastValue < ((NumSensors - 1) * 1000) / 2) return 0;
    else return (NumSensors - 1) * 1000;
  } 
  else LastValue = avg / sum;
  return LastValue;
}

void Pid(int BaseSpeed, float Kp, float Kd) {
  Position = ReadLine();
  Error = Position - 3500;
  PowerMotor = (Kp * Error) + (Kd * (Error - LastError));
  LastError = Error;
  LeftMotor = BaseSpeed + PowerMotor;
  RightMotor = BaseSpeed - PowerMotor;
  LeftMotor = constrain(LeftMotor, -100, 100);
  RightMotor = constrain(RightMotor, -100, 100);
  Motors(LeftMotor, RightMotor);
}

void PidTime(int BaseSpeed, float Kp, float Kd, long Time) {
  unsigned long Start = millis();
  while (millis() - Start < Time) Pid(BaseSpeed, Kp, Kd);
  Motors(0, 0);
}

void View() {
  while (true) {
    ReadPrivate();
    for (int i = 0; i < NumSensors; i++) {
      Serial.print(SensorValue[i]); Serial.print(", ");
    }
    Serial.println(" ");
  }
}

void ViewReadLine() {
  while (true) {
    ReadLine();
    for (int i = 0; i < NumSensors; i++) {
      Serial.print(SensorValue[i]); Serial.print("\t");
    }
    Serial.println(ReadLine());
  }
}
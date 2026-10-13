// Example: Left pivot motor values unfinished
MotorPair studentMotors(char movement, int speed) {
  if (movement == 'F') return {speed, speed};
  if (movement == 'L') return {0, 0}; // TODO left pivot motor values
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

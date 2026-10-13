// Example: Incomplete statement: missing semicolon
MotorPair studentMotors(char movement, int speed) {
  if (movement == 'F') return {speed, speed};
  if (movement == 'L') return {-speed, speed};
  if (movement == 'R') return {speed, -speed};
  if (movement == 'B') return {speed, -speed};
  return {0, 0};
}
char studentChoose(bool left, bool straight, bool right) {
  if (left) return 'L' // TODO finish the statement with a semicolon
  if (straight) return 'F';
  if (right) return 'R';
  return 'B';
}

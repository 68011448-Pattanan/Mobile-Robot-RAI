// Example: Right-only branch case unfinished
MotorPair studentMotors(char movement, int speed) {
  if (movement == 'F') return {speed, speed};
  if (movement == 'L') return {-speed, speed};
  if (movement == 'R') return {speed, -speed};
  if (movement == 'B') return {speed, -speed};
  return {0, 0};
}
char studentChoose(bool left, bool straight, bool right) {
  if (left) return 'L';
  if (straight) return 'F';
  // TODO choose right when left and straight are unavailable
  return 'B';
}

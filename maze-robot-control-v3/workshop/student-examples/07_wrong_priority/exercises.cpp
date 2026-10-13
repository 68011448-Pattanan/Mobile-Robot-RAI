// Example: Incorrect: straight checked before left
MotorPair studentMotors(char movement, int speed) {
  if (movement == 'F') return {speed, speed};
  if (movement == 'L') return {-speed, speed};
  if (movement == 'R') return {speed, -speed};
  if (movement == 'B') return {speed, -speed};
  return {0, 0};
}
char studentChoose(bool left, bool straight, bool right) {
  if (straight) return 'F'; // BUG: this skips left when both exist
  if (left) return 'L';
  if (right) return 'R';
  return 'B';
}

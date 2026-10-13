// Example: Motor values complete, LSRB unfinished
MotorPair studentMotors(char movement, int speed) {
  if (movement == 'F') return {speed, speed};
  if (movement == 'L') return {-speed, speed};
  if (movement == 'R') return {speed, -speed};
  if (movement == 'B') return {speed, -speed};
  return {0, 0};
}

// Exercise 2: implement Left -> Straight (F) -> Right -> Back priority.
// Return one of 'L', 'F', 'R', 'B'. '?' means the exercise is unfinished.
char studentChoose(bool left, bool straight, bool right) {
  // TODO LSRB: inspect available branches in the correct order.
  return '?';
}

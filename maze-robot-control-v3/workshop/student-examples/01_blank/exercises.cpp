// Example: Both exercises unfinished
// Exercise 1: replace the two motor values for each movement.
// F: forward; L: left pivot; R: right pivot; B: clockwise U-turn.
// Use speed and -speed. The return value is {left wheel, right wheel}.
MotorPair studentMotors(char movement, int speed) {
  if (movement == 'F') return {0, 0}; // TODO motor values
  if (movement == 'L') return {0, 0}; // TODO motor values
  if (movement == 'R') return {0, 0}; // TODO motor values
  if (movement == 'B') return {0, 0}; // TODO motor values
  return {0, 0};
}

// Exercise 2: implement Left -> Straight (F) -> Right -> Back priority.
// Return one of 'L', 'F', 'R', 'B'. '?' means the exercise is unfinished.
char studentChoose(bool left, bool straight, bool right) {
  // TODO LSRB: inspect available branches in the correct order.
  return '?';
}

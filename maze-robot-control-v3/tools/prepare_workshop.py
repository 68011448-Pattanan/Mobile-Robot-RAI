"""Rebuild the blank student sketch from the preserved complete firmware."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
base = (ROOT / 'firmware/maze_hc05/maze_hc05.ino').read_text(encoding='utf-8')
student = '''// Version 3 Day 2 student sketch. Edit ONLY the marked exercise block.
// Positive motor command = wheel forward; negative = reverse; range -100..100.
// Six of eight learning modules are supplied (75% by module coverage).
struct MotorPair { int left; int right; };
MotorPair studentMotors(char movement, int speed);
char studentChoose(bool left, bool straight, bool right);

// BEGIN STUDENT EXERCISES
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
// END STUDENT EXERCISES

// Filled automatically by Export passed Arduino sketch. Motors stay stopped
// on power-up; use the armed dashboard to start a real run.
const char WORKSHOP_REPLAY[] = "";
bool workshopLeft = false, workshopRight = false;
void workshopDrive(char movement, int speed);
'''
# Insert after the includes so Arduino's preprocessing sees the type declaration.
needle = 'Adafruit_MCP3008 adc;'
base = base.replace(needle, student+'\n'+needle)
base = base.replace('State state = IDLE, previous = IDLE;', 'void stop(State s); // Prevent Arduino from generating this prototype before the State enum.\nState state = IDLE, previous = IDLE;')
base = base.replace('void stop(State s) {', '''void workshopDrive(char movement, int speed) {
  MotorPair command = studentMotors(movement, speed);
  Motors(command.left, command.right);
}
void stop(State s) {''')
base = base.replace('Motors(baseSpeed + correction, baseSpeed - correction);', '''MotorPair forward = studentMotors('F', baseSpeed);
  Motors(forward.left + correction, forward.right - correction);''')
base = base.replace('Motors(baseSpeed, baseSpeed);', "workshopDrive('F', baseSpeed);")
base = base.replace("Motors(turn == 'L' ? -baseSpeed : baseSpeed, turn == 'L' ? baseSpeed : -baseSpeed);", 'workshopDrive(turn, baseSpeed);')
base = base.replace('void addDecision(char dir, uint16_t advance) {', '''void addDecision(char dir, uint16_t advance) {
  if (dir != 'L' && dir != 'F' && dir != 'R' && dir != 'B') {
    stop(ERROR);
    event(F("STUDENT_LSRB_INCOMPLETE"));
    return;
  }''')
first = base.index('  if (phase == 1) {', base.index('void robotTick()'))
last = base.index('  if (phase == 2) {', first)
base = base[:first]+'''  if (phase == 1) {
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
'''+base[last:]
first = base.index('    if (b(0) && b(1) && b(2) && w(5)')
last = base.index('  } else if (w(2)', first)
base = base[:first]+'''    workshopLeft = b(0) && b(1);
    workshopRight = b(6) && b(7);
    phase = 1;
    phaseStart = now;
    advanceMs = 30;
    workshopDrive('F', baseSpeed);
    return;
'''+base[last:]
base = base.replace("    addDecision('B', 100);", "    addDecision(state == RUN_PATH ? 'B' : studentChoose(false, false, false), 100);")
base = base.replace('  Motors(0, 0);\n  Serial.println', '''  Motors(0, 0);
  if (sizeof(WORKSHOP_REPLAY) > 1 && sizeof(WORKSHOP_REPLAY) <= MAX_PATH + 1) {
    strcpy(shortPath, WORKSHOP_REPLAY);
    shortLength = sizeof(WORKSHOP_REPLAY) - 1;
    state = PATH_READY;
  }
  Serial.println''')
base = base.replace('HELLO,MAZE_V3,1', 'HELLO,MAZE_WORKSHOP_V3,1')
folder = ROOT / 'firmware/workshop_robot'
folder.mkdir(exist_ok=True)
(folder / 'workshop_robot.ino').write_text(base)
first = base.index('// BEGIN STUDENT EXERCISES') + len('// BEGIN STUDENT EXERCISES')
last = base.index('// END STUDENT EXERCISES')
scaffold = base[:first] + '\n' + base[last:]
(ROOT / 'workshop/scaffold.sha256').write_text(hashlib.sha256(scaffold.encode()).hexdigest()+'\n')
nodes=[{'id':i,'x':x,'y':y} for i,x,y in [('S',80,280),('A',230,280),('D',230,120),('B',400,280),('E',400,430),('F',620,280)]]
points = {n['id']: {'x':n['x'],'y':n['y']} for n in nodes}
pairs=[('S','A'),('A','D'),('A','B'),('B','E'),('B','F')]
maze={'id':'day2-field-v3','name':'Day 2 competition field','width':700,'height':520,'lineWidth':14,'scale':1,'heading':0,
      'start':'S','finish':'F','graph':{'nodes':nodes,'edges':[{'id':str(i),'a':a,'b':b,'points':[points[a],points[b]]} for i,(a,b) in enumerate(pairs)]},
      'sourceType':'example','verified':True,'warnings':[]}
(ROOT / 'workshop/field.json').write_text(json.dumps(maze,indent=2)+'\n')
print('Created the blank student sketch, scaffold manifest and shared field.')

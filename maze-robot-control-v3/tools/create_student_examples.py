"""Generate full Arduino sketches and small exercise excerpts for classroom use."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT / 'firmware/workshop_robot/workshop_robot.ino').read_text(encoding='utf-8')
BEGIN = '// BEGIN STUDENT EXERCISES'
END = '// END STUDENT EXERCISES'
first = BASE.index(BEGIN) + len(BEGIN)
last = BASE.index(END)
blank = BASE[first:last].strip()
answer = (ROOT / 'workshop/instructor/solution.cpp').read_text(encoding='utf-8')
answer = '\n'.join(answer.splitlines()[1:]).strip()
split = answer.index('char studentChoose(')
motors = answer[:split].strip()
lsrb = answer[split:].strip()
blank_split = blank.index('// Exercise 2:')
blank_motors = blank[:blank_split].strip()
blank_lsrb = blank[blank_split:].strip()

cases = [
    ('00_complete', 'Complete motor values and LSRB', answer),
    ('01_blank', 'Both exercises unfinished', blank),
    ('02_motors_only', 'Motor values complete, LSRB unfinished', motors+'\n\n'+blank_lsrb),
    ('03_lsrb_only', 'LSRB complete, motor values unfinished', blank_motors+'\n\n'+lsrb),
    ('04_missing_left_motor', 'Left pivot motor values unfinished', answer.replace("if (movement == 'L') return {-speed, speed};", "if (movement == 'L') return {0, 0}; // TODO left pivot motor values")),
    ('05_missing_back_logic', 'Dead-end fallback unfinished', answer.replace("  return 'B';", "  return '?'; // TODO choose a U-turn when there are no branches")),
    ('06_missing_right_logic', 'Right-only branch case unfinished', answer.replace("  if (right) return 'R';", "  // TODO choose right when left and straight are unavailable")),
    ('07_wrong_priority', 'Incorrect: straight checked before left', answer.replace("  if (left) return 'L';\n  if (straight) return 'F';", "  if (straight) return 'F'; // BUG: this skips left when both exist\n  if (left) return 'L';")),
    ('08_wrong_left_motor', 'Incorrect: left pivot motor signs swapped', answer.replace("if (movement == 'L') return {-speed, speed};", "if (movement == 'L') return {speed, -speed}; // BUG: these signs pivot right")),
    ('09_syntax_error', 'Incomplete statement: missing semicolon', answer.replace("  if (left) return 'L';", "  if (left) return 'L' // TODO finish the statement with a semicolon")),
]

out = ROOT / 'workshop/student-examples'
for name, title, code in cases:
    folder = out / name
    sketch_folder = folder / 'workshop_robot'
    sketch_folder.mkdir(parents=True, exist_ok=True)
    block = '// Example: '+title+'\n'+code+'\n'
    sketch = BASE[:first]+'\n'+block+BASE[last:]
    (sketch_folder/'workshop_robot.ino').write_text(sketch, encoding='utf-8')
    (folder/'exercises.cpp').write_text(block, encoding='utf-8')
print(f'Created {len(cases)} example sketches. The original student starter was not changed.')

# Student code examples — complete, incomplete and incorrect

Each case contains:

- `workshop_robot/workshop_robot.ino`: the entire Arduino sketch, ready to load into version 3 or open in Arduino IDE. Keep this filename inside its `workshop_robot` folder.
- `exercises.cpp`: just the student exercise block, for comparing cases or copying into the app editor. This excerpt is not a standalone Arduino sketch.

The supplied blank starter has not been changed. All examples preserve its scaffold and leave `WORKSHOP_REPLAY` empty; use the app's passed-sketch export to insert a verified replay path.

## Try an example

1. Open http://localhost:3003 and select **Day 2 workshop**.
2. Under **Load edited .ino**, select the example's `workshop_robot.ino`. Alternatively, paste its `exercises.cpp` contents into the student exercise editor.
3. Click **Compile exercises**, then **Run student simulation**. Inspect the branch/motor checks, movement and timeline.
4. Compare your prediction with the result below. Modify the incomplete block and run again.
5. For a real-robot sketch, use the **complete** example, confirm that the physical field matches, pass the simulation, and click **Export passed Arduino sketch + path**. Incomplete/incorrect cases are simulation exercises, not scored physical-run sketches.

Loading a file in the browser does not overwrite the on-disk starter. **Reload saved .ino** restores the saved starter from `firmware/workshop_robot/workshop_robot.ino`. The compiler accepts only changes within the marked student block.

## Cases and verified outcomes

“Finishes” below means both the simulator's learning run and replay finish on the supplied two-dead-end field. “Eligible” additionally requires correct motor values, all eight LSRB cases, and instructor field confirmation. The examples were checked without field confirmation, so verification did not create certificates or record competition results.

| Case | What is complete / missing | Compiles? | Finishes? | Eligible after field confirmation? | What to observe |
| --- | --- | --- | --- | --- | --- |
| [00 — Complete](00_complete/workshop_robot/workshop_robot.ino) | Both exercises complete | Yes | Yes | Yes | Learns `LBLF`, reduces to `FF`, replays successfully. |
| [01 — Blank](01_blank/workshop_robot/workshop_robot.ino) | Motor values are zero; LSRB returns `?` | Yes | No | No | Robot stays at START until the 600-second simulation limit. |
| [02 — Motors only](02_motors_only/workshop_robot/workshop_robot.ino) | Motors complete; LSRB unfinished | Yes | No | No | Robot follows the line, then stops at its first decision because `?` is invalid. |
| [03 — LSRB only](03_lsrb_only/workshop_robot/workshop_robot.ino) | LSRB complete; motors unfinished | Yes | No | No | Branch checks pass, but zero motor commands keep the robot at START. |
| [04 — Missing left motor values](04_missing_left_motor/workshop_robot/workshop_robot.ino) | Everything except the L motor pair | Yes | No | No | Reaches the first junction and chooses L, but cannot pivot; turn timeout. |
| [05 — Missing Back logic](05_missing_back_logic/workshop_robot/workshop_robot.ino) | L/F/R checks complete; dead-end fallback returns `?` | Yes | No | No | Enters the first dead end but cannot choose the U-turn. |
| [06 — Missing Right logic](06_missing_right_logic/workshop_robot/workshop_robot.ino) | L/F/B complete; right-only check omitted | Yes | Yes | No | This field does not require a right-only decision; the full branch checker exposes the missing case. |
| [07 — Wrong priority](07_wrong_priority/workshop_robot/workshop_robot.ino) | All code present, but F checked before L | Yes | Yes | No | Goes straight past the first left branch, learning `FF` instead of `LBLF`; LSRB checks fail. |
| [08 — Wrong left motor signs](08_wrong_left_motor/workshop_robot/workshop_robot.ino) | All code present, but L motor signs reversed | Yes | No | No | Chooses L correctly, then pivots in the wrong direction and times out. |
| [09 — Syntax error](09_syntax_error/workshop_robot/workshop_robot.ino) | Missing semicolon after `return 'L'` | No | Cannot run | No | Compiler identifies the unfinished statement; fix syntax before testing behavior. |

Cases 01–06 demonstrate unfinished code. Cases 07–08 demonstrate complete-looking but incorrect code. Case 09 demonstrates a syntax error. **Compiling, reaching the finish, and implementing LSRB correctly are separate checks.**

## Complete exercise block

Copy these two functions into the marked block. `MotorPair` and its declarations are already supplied outside that block.

```cpp
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
  if (right) return 'R';
  return 'B';
}
```

The motor pair is `{left wheel, right wheel}`. Positive means forward; negative means reverse. B uses the same clockwise pivot signs as R, but the supplied turn scaffold performs a U-turn rather than a right-angle turn. The simulator checks integer speeds 1–100; do not substitute a fixed speed such as 30 for the `speed` parameter.

## All LSRB branch cases

| Left available | Straight available | Right available | Correct decision |
| --- | --- | --- | --- |
| No | No | No | B |
| No | No | Yes | R |
| No | Yes | No | F |
| No | Yes | Yes | F |
| Yes | No | No | L |
| Yes | No | Yes | L |
| Yes | Yes | No | L |
| Yes | Yes | Yes | L |

Verification details are saved in [verification.json](verification.json). These results use the current version 3 simulator and supplied field; they are not physical robot test results. Regenerate/check examples with `python tools/create_student_examples.py` and `python tools/check_student_examples.py` from the version 3 root while its backend is running. Regeneration overwrites these example files, so keep student work elsewhere.

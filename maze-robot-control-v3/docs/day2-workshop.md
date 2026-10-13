# Day 2 workshop — 180 minutes

## Before students arrive

Keep the Day 1 robot, pin layout, eight sensors, MCP3008 and PD line-following exercises. Each group needs its Uno robot, a data-capable USB cable, HC-05, motor driver, charged battery, Arduino IDE and a Windows computer with Docker Desktop/Python. Install Adafruit MCP3008 and BusIO before the session. Prepare the measured field and verify that your robot can physically track it using the instructor solution. Confirm wheel polarity, sensor ordering, line polarity, calibration, speed and turn timing on your actual hardware.

Start version 3 with `docker compose -p maze-robot-v3 up --build -d` and open localhost:3003. Distribute the blank `firmware/workshop_robot/workshop_robot.ino`; do not distribute the instructor answer initially. Keep one instructor-controlled result recorder for an unambiguous finish order. All groups must use the same field definition and initial heading.

## Agenda

| Elapsed minutes | Duration | Topic and outcome |
| --- | ---: | --- |
| 0–15 | 15 | Day 1 review: identify wheel directions, eight sensor signals, error and PD correction. |
| 15–40 | 25 | Bluetooth: explain Arduino UART, HC-05 Classic SPP, outgoing COM port and host bridge; read telemetry and send GET_STATUS/STOP. |
| 40–60 | 20 | LSRB: work through all branch combinations, dead ends and cascading path reduction; distinguish learned routes from arbitrary-maze shortest paths. |
| 60–105 | 45 | Simulation: complete the motor values and LSRB in the `.ino`, compile, observe, debug and reach finish in learning and replay. |
| 105–120 | 15 | Transfer: export the passed sketch with path, install/select the Uno libraries/board and upload using USB. |
| 120–170 | 50 | Physical implementation: validate wheel direction, calibrate sensors, connect Bluetooth and attempt the field. Instructor records successful finishes in order. |
| 170–180 | 10 | Announce the winner and discuss physical differences, incorrect branch priority and motor signs. |
| **Total** | **180** | |

## Exercise 1 — motor values

Load an edited `.ino` through **Load edited .ino**, or edit the marked block in Day 2 workshop. The Dashboard and Path analyzer simulations use this same loaded code. Switching tabs preserves it and the workshop result. **Reload saved .ino** replaces the loaded code with the version stored on disk; refreshing the page also loads that saved version. The blank starter has zero motor values, so it stays stationary until students complete them; the Dashboard explains unfinished exercises after a run starts.

Complete the `{left wheel, right wheel}` return values in `studentMotors()`. Positive values move a wheel forward; negative values reverse it. Use the provided `speed` parameter, which is a percentage 1–100. Forward requires both wheels forward; left/right pivots need opposite wheel directions; the supplied B maneuver uses a clockwise pivot continued to 180 degrees. The supplied motion scaffold determines the turn duration/line reacquisition and supplies PD correction; students do not rewrite the control loop.

Ask each group to explain which wheel moves forward/reverse for each turn before running the real robot. Inspect the simulation's actual motor values and trajectory, not only the green branch checks.

## Exercise 2 — LSRB

Complete `studentChoose(left, straight, right)` using the available-branch booleans. L = left, F = straight/forward, R = right, B = return from a dead end. Check left first, then straight, then right, then back. Use integer expressions and `if`/`else`/`return` in the marked block. The same C++ functions are compiled by the app and called by the Arduino firmware. An unfinished function returns `?`, which cannot pass.

Have students predict the path before observing the robot. The supplied tree should learn `LBLF`, reduce it to `FF`, and successfully replay that reduced route. The assessment checks all eight branch combinations and all motor speeds, then independently runs learning and replay with the shared simulator. Correct behavior in only one branch case is insufficient.

## Field definition

Coordinates below are in millimeters; the origin is the upper-left corner. The field is 700 × 520 mm, scale 1 mm/unit, line width 14 mm, start heading East (0 degrees). Lay straight black line segments on a white surface. Use the app's SVG at actual size for exact geometry and rounded line caps.

| Node | x (mm) | y (mm) | Purpose |
| --- | ---: | ---: | --- |
| S | 80 | 280 | Start, robot facing East |
| A | 230 | 280 | First junction |
| D | 230 | 120 | First dead end |
| B | 400 | 280 | Second junction |
| E | 400 | 430 | Second dead end |
| F | 620 | 280 | Finish |

Connect S–A, A–D, A–B, B–E and B–F. At F add the black **50 × 60 mm** finish rectangle centered at (620,280). Keep START/FINISH labels away from the robot's sensor path. Verify the printer has not scaled the artwork. The simulator detects proximity to the marked finish; the real sketch detects its broad sensor signature. Actual turn timing and sensor thresholds may need instructor tuning before class; changing scaffold code requires rebuilding its manifest with the maintenance tool/appropriate code update, not student editing.

If your existing field differs, replace `workshop/field.json` with its measured maze before class. The example is not an automatic reconstruction of an unseen physical field. The app reads this file for simulation and print output; the instructor confirms the physical match before certificates can be issued.

## Transfer and physical test

The student chooses either export of the passed `.ino` with `WORKSHOP_REPLAY` prefilled, or upload of the passed TXT path to a robot already flashed with the same verified student firmware. Export never starts motors. Connect the bridge to version 3's backend (its default URL is ws://127.0.0.1:8003/bridge). Close Arduino Serial Monitor before starting it.

For the Arduino wiring, use left PWM/INA/INB D5/D2/D3, right D6/D4/D7, MCP3008 CLK/DOUT/DIN/CS A0/A1/A2/A3, HC-05 TXD D9, HC-05 RXD D10 through a 5-to-3.3 V voltage divider, common ground, and local stop button D8 to ground. USB baud is 115200; Bluetooth data baud is 9600. Confirm the HC-05 breakout's supply rating. A divider can use D10 → 1 kΩ → RXD → 2 kΩ → ground.

Lift the wheels for a motor-direction check, then calibrate on the physical white surface and black line. Restore the robot to S facing East before every run. Use deliberate arming, the software STOP and the local D8 stop button. A missing heartbeat stops motion after 1.5 seconds. Simulation does not establish real motor wiring, optical response, traction or finish recognition.

## Competition rules

1. Every group uses the same field layout, starting pose and completion criteria.
2. A group must pass the student simulation before its scored field attempt.
3. The group must demonstrate its own completed motor and LSRB exercises and flash that exact passed sketch.
4. A physical pass means the robot travels from START to FINISH without a push, lift, repositioning or code/motor intervention during the attempt. Either the learned-path replay or real LSRB test may be used, as announced consistently before the first attempt.
5. Retry unsuccessful attempts within the allotted 50-minute field session. Stop and restore the robot to START before retrying.
6. The instructor observes and records each successful finish immediately. The first instructor-confirmed physical finish recorded wins; later passes receive the next place. If finishes cannot be distinguished in time, run a tie-break attempt before recording their order.
7. The scoreboard is a local instructor-operated tool. It has no user authentication and does not replace physical observation. Results persist across restarts; simulation certificates expire after six hours or a backend restart, and changing the field invalidates them.

## Instructor completion rubric

Six supplied learning modules: acquisition, calibration, PD line following, Bluetooth/protocol, path memory/transfer, bounded states and motion phases. Two student modules: motor values and LSRB. This makes the starter 6/8 = **75% complete by assessed module coverage**; its source-line percentage is not 75% because the supporting protocol is verbose. Only the two intended exercise modules contain placeholders.

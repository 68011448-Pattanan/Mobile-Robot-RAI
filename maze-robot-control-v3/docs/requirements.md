# Requirement coverage

Every numbered requirement from both supplied prompts is indexed below. “Implemented” describes the code, not a claim that unavailable physical hardware or Docker was tested. Optional suggestions are handled where practical: PDF raster import, SVG vector preservation, Linux serial container, generator, graph shortest-path comparison and manual controls are included.

| Source | Requirement | Location | Validation / boundary |
| --- | --- | --- | --- |
| Prompt 1 §1 | FIRST: ANALYZE THE EXISTING `maze.ino` | docs/firmware-analysis.md | Implemented; see the verification report for test scope. |
| Prompt 1 §2 | OVERALL APPLICATION GOAL | README.md and application navigation | Implemented; see the verification report for test scope. |
| Prompt 1 §3 | REQUIRED TECH STACK | README.md and application navigation | Implemented; see the verification report for test scope. |
| Prompt 1 §4 | WINDOWS + HC-05 + DOCKER CONSIDERATION | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Files provided and YAML checked; Docker runtime unavailable, so container execution remains unverified. |
| Prompt 1 §5 | SIMULATION MODE | frontend/lib/robot.ts; Dashboard / PID lab / Calibration / Settings; tests/simulation_test.cjs | Implemented; see the verification report for test scope. |
| Prompt 1 §6 | SENSOR SIMULATION | frontend/lib/robot.ts; Dashboard / PID lab / Calibration / Settings; tests/simulation_test.cjs | Implemented; see the verification report for test scope. |
| Prompt 1 §7 | SENSOR CALIBRATION PAGE | frontend/lib/robot.ts; Dashboard / PID lab / Calibration / Settings; tests/simulation_test.cjs | Implemented; see the verification report for test scope. |
| Prompt 1 §8 | LINE POSITION VISUALIZATION | frontend/lib/robot.ts; Dashboard / PID lab / Calibration / Settings; tests/simulation_test.cjs | Implemented; see the verification report for test scope. |
| Prompt 1 §9 | PID / PD TUNING LAB | frontend/lib/robot.ts; Dashboard / PID lab / Calibration / Settings; tests/simulation_test.cjs | Implemented; see the verification report for test scope. |
| Prompt 1 §10 | LSRB / MAZE EXPLORATION SIMULATION | frontend/lib/robot.ts; Dashboard / PID lab / Calibration / Settings; tests/simulation_test.cjs | Implemented; see the verification report for test scope. |
| Prompt 1 §11 | SCAN / LEARNING RUN | frontend/lib/robot.ts; Maze solver / Path analyzer / Dashboard | Implemented; see the verification report for test scope. |
| Prompt 1 §12 | PATH OPTIMIZATION VISUALIZATION | frontend/lib/robot.ts; Maze solver / Path analyzer / Dashboard | Implemented; see the verification report for test scope. |
| Prompt 1 §13 | SHORTEST-PATH / REAL RUN | frontend/lib/robot.ts; Maze solver / Path analyzer / Dashboard | Implemented; see the verification report for test scope. |
| Prompt 1 §14 | SERIAL MONITOR | Serial monitor / Real robot diagnostics; backend packet parser | Implemented; see the verification report for test scope. |
| Prompt 1 §15 | DESIGN A PROPER ROBOT SERIAL PROTOCOL | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Implemented; see the verification report for test scope. |
| Prompt 1 §16 | CREATE A NEW ARDUINO FIRMWARE | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Firmware compiles / protocol tested with mock; actual hardware remains unverified. |
| Prompt 1 §17 | HC-05 BLUETOOTH SUPPORT | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Firmware compiles / protocol tested with mock; actual hardware remains unverified. |
| Prompt 1 §18 | FIRMWARE STATE MACHINE | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Firmware compiles / protocol tested with mock; actual hardware remains unverified. |
| Prompt 1 §19 | REAL-TIME TELEMETRY | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Implemented; see the verification report for test scope. |
| Prompt 1 §20 | REAL ROBOT DASHBOARD | Real robot / Dashboard | Firmware compiles / protocol tested with mock; actual hardware remains unverified. |
| Prompt 1 §21 | SAFETY CONTROLS | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Firmware compiles / protocol tested with mock; actual hardware remains unverified. |
| Prompt 1 §22 | PATH DOWNLOAD FROM ROBOT | backend/app/main.py; Path analyzer; docs/protocol.md | Implemented; see the verification report for test scope. |
| Prompt 1 §23 | PATH UPLOAD TO ROBOT | backend/app/main.py; Path analyzer; docs/protocol.md | Implemented; see the verification report for test scope. |
| Prompt 1 §24 | PATH EDITOR | backend/app/main.py; Path analyzer; docs/protocol.md | Implemented; see the verification report for test scope. |
| Prompt 1 §25 | MANUAL CONTROL | Settings / Real robot manual controls; firmware DRIVE watchdog | Implemented; see the verification report for test scope. |
| Prompt 1 §26 | EDUCATIONAL "HOW IT WORKS" MODE | How it works / Firmware; docs/firmware-analysis.md | Implemented; see the verification report for test scope. |
| Prompt 1 §27 | CODE EXPLORER | How it works / Firmware; docs/firmware-analysis.md | Implemented; see the verification report for test scope. |
| Prompt 1 §28 | DEBUGGING PANEL | Serial monitor / Real robot diagnostics; backend packet parser | Implemented; see the verification report for test scope. |
| Prompt 1 §29 | SIMULATION VS REAL MODE CONSISTENCY | frontend/lib/robot.ts; Dashboard / PID lab / Calibration / Settings; tests/simulation_test.cjs | Implemented; see the verification report for test scope. |
| Prompt 1 §30 | RECORD AND REPLAY | backend/app/main.py; Recordings; CSV/JSON/TXT exports | Implemented; see the verification report for test scope. |
| Prompt 1 §31 | DATA EXPORT | backend/app/main.py; Recordings; CSV/JSON/TXT exports | Implemented; see the verification report for test scope. |
| Prompt 1 §32 | PROJECT STRUCTURE | README.md and application navigation | Implemented; see the verification report for test scope. |
| Prompt 1 §33 | DOCKER | docker-compose.yml; Dockerfiles; README quick start | Files provided and YAML checked; Docker runtime unavailable, so container execution remains unverified. |
| Prompt 1 §34 | STARTUP EXPERIENCE | docker-compose.yml; Dockerfiles; README quick start | Implemented; see the verification report for test scope. |
| Prompt 1 §35 | DOCUMENTATION | README.md and docs/ | Implemented; see the verification report for test scope. |
| Prompt 1 §36 | TESTING | tests/; docs/verification.md | Implemented; see the verification report for test scope. |
| Prompt 1 §37 | IMPORTANT CODE REVIEW OF THE ORIGINAL FIRMWARE | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Firmware compiles / protocol tested with mock; actual hardware remains unverified. |
| Prompt 1 §38 | UI / UX EXPECTATIONS | README.md and application navigation | Implemented; see the verification report for test scope. |
| Prompt 1 §39 | SIMULATION CONTROLS | frontend/lib/robot.ts; Dashboard / PID lab / Calibration / Settings; tests/simulation_test.cjs | Implemented; see the verification report for test scope. |
| Prompt 1 §40 | ROBOT VISUALIZATION | README.md and application navigation | Implemented; see the verification report for test scope. |
| Prompt 1 §41 | ALGORITHM TIMELINE | frontend/lib/robot.ts; Maze solver / Path analyzer / Dashboard | Implemented; see the verification report for test scope. |
| Prompt 1 §42 | CONNECTION ROBUSTNESS | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Implemented; see the verification report for test scope. |
| Prompt 1 §43 | PATH TRANSFER PROTOCOL | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Implemented; see the verification report for test scope. |
| Prompt 1 §44 | COMMAND SAFETY | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Firmware compiles / protocol tested with mock; actual hardware remains unverified. |
| Prompt 1 §45 | DELIVERABLES | README.md and application navigation | Implemented; see the verification report for test scope. |
| Prompt 1 §46 | FINAL VERIFICATION BEFORE DELIVERY | tests/; docs/verification.md | Files provided and YAML checked; Docker runtime unavailable, so container execution remains unverified. |
| Prompt 1 §47 | FINAL RESPONSE | README.md and application navigation | Implemented; see the verification report for test scope. |
| Prompt 2 §1 | ANALYZE THE EXISTING `maze.ino` | docs/firmware-analysis.md | Implemented; see the verification report for test scope. |
| Prompt 2 §2 | OVERALL SYSTEM ARCHITECTURE | README.md and application navigation | Implemented; see the verification report for test scope. |
| Prompt 2 §3 | REQUIRED TECH STACK | README.md and application navigation | Implemented; see the verification report for test scope. |
| Prompt 2 §4 | DOCKER | docker-compose.yml; Dockerfiles; README quick start | Files provided and YAML checked; Docker runtime unavailable, so container execution remains unverified. |
| Prompt 2 §5 | UNIVERSAL MAZE SYSTEM | README.md and application navigation | Best-effort supported formats plus manual correction; no claim of perfect interpretation of every image. |
| Prompt 2 §6 | UNIVERSAL MAZE IMPORTER | backend/app/maze.py; Maze workspace; tests/test_import.py | Best-effort supported formats plus manual correction; no claim of perfect interpretation of every image. |
| Prompt 2 §7 | MAZE IMAGE IMPORT | backend/app/maze.py; Maze workspace; tests/test_import.py | Implemented; see the verification report for test scope. |
| Prompt 2 §8 | PERSPECTIVE CORRECTION | backend/app/maze.py; Maze workspace; tests/test_import.py | Implemented; see the verification report for test scope. |
| Prompt 2 §9 | BLACK-LINE AND WHITE-LINE MAZES | README.md and application navigation | Implemented; see the verification report for test scope. |
| Prompt 2 §10 | THRESHOLD CONTROL | backend/app/maze.py; Maze workspace; tests/test_import.py | Implemented; see the verification report for test scope. |
| Prompt 2 §11 | LINE-MAZE EXTRACTION | backend/app/maze.py; Maze workspace; tests/test_import.py | Implemented; see the verification report for test scope. |
| Prompt 2 §12 | INTERSECTION DETECTION | backend/app/maze.py; Maze workspace; tests/test_import.py | Implemented; see the verification report for test scope. |
| Prompt 2 §13 | GRAPH REPRESENTATION | backend/app/maze.py; Maze workspace; tests/test_import.py | Implemented; see the verification report for test scope. |
| Prompt 2 §14 | MANUAL MAZE CORRECTION | Maze workspace and Settings; backend/app/maze.py | Implemented; see the verification report for test scope. |
| Prompt 2 §15 | START AND FINISH SELECTION | Maze workspace and Settings; backend/app/maze.py | Implemented; see the verification report for test scope. |
| Prompt 2 §16 | SCALE CALIBRATION | Maze workspace and Settings; backend/app/maze.py | Implemented; see the verification report for test scope. |
| Prompt 2 §17 | REAL ROBOT COMPATIBILITY CHECKER | Maze workspace and Settings; backend/app/maze.py | Firmware compiles / protocol tested with mock; actual hardware remains unverified. |
| Prompt 2 §18 | MAZE IMPORT PREVIEW | backend/app/maze.py; Maze workspace; tests/test_import.py | Implemented; see the verification report for test scope. |
| Prompt 2 §19 | IMPORT CONFIDENCE | backend/app/maze.py; Maze workspace; tests/test_import.py | Implemented; see the verification report for test scope. |
| Prompt 2 §20 | DISCONNECTED-LINE DETECTION | backend/app/maze.py; Maze workspace; tests/test_import.py | Implemented; see the verification report for test scope. |
| Prompt 2 §21 | WALL MAZE SUPPORT | backend/app/maze.py; Maze workspace; tests/test_import.py | Implemented; see the verification report for test scope. |
| Prompt 2 §22 | GRID MAZE IMPORT | backend/app/maze.py; Maze workspace; tests/test_import.py | Implemented; see the verification report for test scope. |
| Prompt 2 §23 | JSON MAZE IMPORT | backend/app/maze.py; Maze workspace; tests/test_import.py | Implemented; see the verification report for test scope. |
| Prompt 2 §24 | SVG IMPORT | backend/app/maze.py; Maze workspace; tests/test_import.py | Implemented; see the verification report for test scope. |
| Prompt 2 §25 | PDF IMPORT | backend/app/maze.py; Maze workspace; tests/test_import.py | Implemented; see the verification report for test scope. |
| Prompt 2 §26 | MAZE DRAWING EDITOR | Maze workspace and Settings; backend/app/maze.py | Implemented; see the verification report for test scope. |
| Prompt 2 §27 | MAZE LIBRARY | Maze workspace and Settings; backend/app/maze.py | Implemented; see the verification report for test scope. |
| Prompt 2 §28 | GENERATED MAZES | Maze workspace and Settings; backend/app/maze.py | Implemented; see the verification report for test scope. |
| Prompt 2 §29 | SIMULATION MODE | frontend/lib/robot.ts; Dashboard / PID lab / Calibration / Settings; tests/simulation_test.cjs | Implemented; see the verification report for test scope. |
| Prompt 2 §30 | REALISTIC SENSOR SIMULATION | frontend/lib/robot.ts; Dashboard / PID lab / Calibration / Settings; tests/simulation_test.cjs | Sensor + wheel model implemented; branch probe and physical effects are approximations documented in README. |
| Prompt 2 §31 | SENSOR CALIBRATION | frontend/lib/robot.ts; Dashboard / PID lab / Calibration / Settings; tests/simulation_test.cjs | Implemented; see the verification report for test scope. |
| Prompt 2 §32 | LINE POSITION | frontend/lib/robot.ts; Dashboard / PID lab / Calibration / Settings; tests/simulation_test.cjs | Implemented; see the verification report for test scope. |
| Prompt 2 §33 | PID / PD LAB | frontend/lib/robot.ts; Dashboard / PID lab / Calibration / Settings; tests/simulation_test.cjs | Implemented; see the verification report for test scope. |
| Prompt 2 §34 | LSRB LEARNING MODE | frontend/lib/robot.ts; Maze solver / Path analyzer / Dashboard | Implemented; see the verification report for test scope. |
| Prompt 2 §35 | RAW PATH | backend/app/main.py; Path analyzer; docs/protocol.md | Implemented; see the verification report for test scope. |
| Prompt 2 §36 | PATH OPTIMIZATION | frontend/lib/robot.ts; Maze solver / Path analyzer / Dashboard | Implemented; see the verification report for test scope. |
| Prompt 2 §37 | COMPARE LSRB WITH TRUE SHORTEST PATH | frontend/lib/robot.ts; Maze solver / Path analyzer / Dashboard | Implemented; see the verification report for test scope. |
| Prompt 2 §38 | OPTIMIZED RUN | frontend/lib/robot.ts; Maze solver / Path analyzer / Dashboard | Implemented; see the verification report for test scope. |
| Prompt 2 §39 | SERIAL MONITOR | Serial monitor / Real robot diagnostics; backend packet parser | Implemented; see the verification report for test scope. |
| Prompt 2 §40 | SERIAL PROTOCOL | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Implemented; see the verification report for test scope. |
| Prompt 2 §41 | NEW HC-05 FIRMWARE | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Firmware compiles / protocol tested with mock; actual hardware remains unverified. |
| Prompt 2 §42 | HC-05 | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Firmware compiles / protocol tested with mock; actual hardware remains unverified. |
| Prompt 2 §43 | WINDOWS SERIAL BRIDGE | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Implemented; see the verification report for test scope. |
| Prompt 2 §44 | FIRMWARE STATE MACHINE | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Firmware compiles / protocol tested with mock; actual hardware remains unverified. |
| Prompt 2 §45 | REAL-TIME TELEMETRY | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Implemented; see the verification report for test scope. |
| Prompt 2 §46 | REAL ROBOT DASHBOARD | Real robot / Dashboard | Firmware compiles / protocol tested with mock; actual hardware remains unverified. |
| Prompt 2 §47 | REAL ROBOT POSITION ON IMPORTED MAZE | Dashboard estimated-junction display (no edge percentage without encoders) | Firmware compiles / protocol tested with mock; actual hardware remains unverified. |
| Prompt 2 §48 | PATH DOWNLOAD | backend/app/main.py; Path analyzer; docs/protocol.md | Implemented; see the verification report for test scope. |
| Prompt 2 §49 | PATH UPLOAD | backend/app/main.py; Path analyzer; docs/protocol.md | Implemented; see the verification report for test scope. |
| Prompt 2 §50 | ROBUST PATH TRANSFER | firmware/maze_hc05; serial-bridge; docs/protocol.md; docs/firmware-analysis.md | Implemented; see the verification report for test scope. |
| Prompt 2 §51 | PATH EDITOR | backend/app/main.py; Path analyzer; docs/protocol.md | Implemented; see the verification report for test scope. |
| Prompt 2 §52 | MANUAL CONTROL | Settings / Real robot manual controls; firmware DRIVE watchdog | Implemented; see the verification report for test scope. |
| Prompt 2 §53 | EMERGENCY STOP | README.md and application navigation | Implemented; see the verification report for test scope. |
| Prompt 2 §54 | HOW IT WORKS | How it works / Firmware; docs/firmware-analysis.md | Implemented; see the verification report for test scope. |
| Prompt 2 §55 | CODE EXPLORER | How it works / Firmware; docs/firmware-analysis.md | Implemented; see the verification report for test scope. |
| Prompt 2 §56 | RECORD AND REPLAY | backend/app/main.py; Recordings; CSV/JSON/TXT exports | Implemented; see the verification report for test scope. |
| Prompt 2 §57 | EXPORT DATA | backend/app/main.py; Recordings; CSV/JSON/TXT exports | Implemented; see the verification report for test scope. |
| Prompt 2 §58 | SHARED ROBOT STATE MODEL | frontend/lib/robot.ts RobotState; backend/app/core.py | Implemented; see the verification report for test scope. |
| Prompt 2 §59 | PROJECT STRUCTURE | README.md and application navigation | Implemented; see the verification report for test scope. |
| Prompt 2 §60 | UI | README.md and application navigation | Implemented; see the verification report for test scope. |
| Prompt 2 §61 | MAZE IMPORT WORKFLOW | backend/app/maze.py; Maze workspace; tests/test_import.py | Implemented; see the verification report for test scope. |
| Prompt 2 §62 | SIMULATION WORKFLOW | frontend/lib/robot.ts; Dashboard / PID lab / Calibration / Settings; tests/simulation_test.cjs | Implemented; see the verification report for test scope. |
| Prompt 2 §63 | PHYSICAL ROBOT WORKFLOW | README.md and application navigation | Firmware compiles / protocol tested with mock; actual hardware remains unverified. |
| Prompt 2 §64 | TESTING | tests/; docs/verification.md | Implemented; see the verification report for test scope. |
| Prompt 2 §65 | IMPORTANT LIMITATION | README.md and application navigation | Best-effort supported formats plus manual correction; no claim of perfect interpretation of every image. |
| Prompt 2 §66 | ACCEPTANCE TEST: EXTERNAL MAZE | tests/; docs/verification.md | Implemented; see the verification report for test scope. |
| Prompt 2 §67 | ACCEPTANCE TEST: PHOTO OF A REAL MAZE | tests/; docs/verification.md | Perspective correction implemented and synthetic photo warp tested; a real camera photo was not available. |
| Prompt 2 §68 | ACCEPTANCE TEST: PHYSICAL ROBOT | tests/; docs/verification.md | Firmware compiles / protocol tested with mock; actual hardware remains unverified. |
| Prompt 2 §69 | DOCUMENTATION | README.md and docs/ | Implemented; see the verification report for test scope. |
| Prompt 2 §70 | FINAL DELIVERABLE | README.md and application navigation | Implemented; see the verification report for test scope. |
| Prompt 2 §71 | FINAL VERIFICATION | tests/; docs/verification.md | Files provided and YAML checked; Docker runtime unavailable, so container execution remains unverified. |

## Explicit interpretation boundaries

- Any maze: supports all listed minimum formats and manual correction; the simulator cannot guarantee completion of every geometry and LSRB cannot solve every looped maze.
- Original behavior: physical signatures/pin assignments are retained; responsiveness, controller tick, stop behavior and safety changes are explicitly documented. Simulator branch probing is a separate approximation.
- Shortest path: dead-end reduction is labeled a reduced learned route; Dijkstra provides an independent true graph-distance comparison.
- Physical position: junction-based estimate only; exact distance/edge progress is unavailable without additional sensors.
- Bluetooth rate: 9600 baud cannot safely carry full20Hz snapshots; five round-robin packets per second are used, and higher rates are available through USB.
- Mechanical compatibility: dimensional warnings rather than a certification.
- Artifacts: complete sources, original/new firmware, host bridge, Docker configuration, examples, tests and documentation are included; no essential implementation is marked TODO.

## Additional user request: robot maze upload

Added EEPROM maze transfer alongside existing path transfer, USB and Bluetooth support, reviewed topology/capacity validation, checksum and exact byte readback, saved-map inspection/clear controls, motion staging guard, and mock/integration coverage. See README and protocol.md for storage limits and driving semantics.

## Additional user request: live discovery without a predefined map

Added partial route reconstruction from robot cumulative turn reports, inferred backtracking, unknown-distance schematic visualization, live WebSocket snapshots and browser reconnect recovery, failure/gap warnings, JSON export, a labeled offline discovery demo, and verified non-destructive EEPROM map readback. No physical localization, complete arbitrary-maze reconstruction, or automatic loop closure is claimed.

# Version 3 verification — 2026-10-13

## Passed checks

- Dashboard bug checks: the dashboard and path replay compile the current student sketch loaded/edited in Day 2 workshop. Switching tabs preserves that sketch and the workshop result; hidden workshop animation pauses. Blank motor exercises display a persistent explanation for stationary movement. Browser QA with the complete example verifies movement, learning finish, optimized replay finish, pause, step, resume, reset, tab preservation and stopping workshop animation from the global Emergency Stop control.
- Additional browser regressions verify that starting learning exits a recording replay and that Emergency Stop cancels a pending compile before it can start motion. Every navigation tab renders without a browser exception. Temporary simulation recordings used for QA were removed; no physical finish was recorded.
- Simulator regression checks cover repeated pause/resume, idle pause and clearing probe/turn progress when resetting a run. Loading the same `.ino` file again is supported; a file missing the exercise markers produces immediate feedback. The production frontend build and TypeScript check pass after these fixes.
- Frontend TypeScript checks and production Next.js build pass. Docker Compose builds and starts both services; backend is healthy at 127.0.0.1:8003 and frontend serves localhost:3003. The health check requests workshop setup, including the mounted source and maze assets.
- **74 Python backend tests pass** in the built Docker image. This includes the 67 inherited tests and workshop tests with multiple assertions for scaffold protection, supported C++ syntax, compiler errors, motor ranges, all eight LSRB cases, all speeds 1–100, student output influence on movement, incomplete code, incorrect turn signs and incorrect branch order. Upload regressions cover Windows CRLF, CR-only newlines and a leading UTF-8 BOM; real scaffold edits remain rejected. Certificate/export tests also use an uploaded CRLF sketch with a BOM.
- All ten student examples were verified through the running API using raw decoded file bytes, preserving browser upload line endings. The complete example passes; incomplete and incorrect examples retain their expected failures or assessment results.
- Browser file-picker regression: uploading `00_complete/workshop_robot/workshop_robot.ino` with Windows CRLF and clicking Compile exercises displays PASS for LSRB and all four motor checks.
- Shared-code tests: correct C++ learns `LBLF`, reduces to `FF` and completes replay. Swapping branch priority changes the learned path; wrong left-turn motor signs fail the simulation; the blank starter fails. A path reaching finish with an incorrect priority does not receive a certificate.
- Certificate tests cover field confirmation, successful learning/replay, export containing the exact completed student source plus `WORKSHOP_REPLAY="FF"`, invalid/expired certificates and field changes. Path upload is blocked while the robot is moving and delegates to the existing verified-transfer implementation after stopping.
- Competition tests reject unconfirmed physical finishes and duplicate group names, persist the first group's winning position and keep later finish ordering. These run in an isolated temporary directory and leave the real workshop scoreboard empty.
- The inherited deterministic TypeScript simulation test passes: sensor position, learning/reduction/replay, pause/resume, stop and graph consistency.
- Independent backend plus mock serial-bridge integration passes: connection, telemetry, PID/speed, path checksum/readback, maze checksum/readback, discovery updates, path files, replay, pause/resume, STOP, recordings/export, invalid input and reconnect. This exercises software transport, not the Arduino MCU.
- Browser QA at localhost:3003: blank starter compiles and displays “Needs work”; the instructor solution passes all branch/motor checks, learns and replays, enables export, and downloads a complete `.ino` with `FF`. Editing the exercise block afterward disables export until another pass. Reload restores the untouched blank on-disk student sketch. Desktop simulation and mobile layout screenshots were inspected. No physical scoreboard entry was recorded.
- The Arduino IDE's bundled Arduino CLI compiled for **Arduino Uno**, AVR core **1.8.7**, Adafruit MCP3008 **1.3.3**, and BusIO **1.17.4**:

| Sketch | Flash | Global SRAM | SRAM remaining |
| --- | ---: | ---: | ---: |
| Blank student starter | 21,360 bytes / 66% | 1,100 bytes / 53% | 948 bytes |
| Completed motor and LSRB exercises | 21,532 bytes / 66% | 1,102 bytes / 53% | 946 bytes |
| Exported sketch with FF replay path | 21,564 bytes / 66% | 1,104 bytes / 53% | 944 bytes |

The actual file downloaded by the browser also compiled with the exported-sketch figures above. No sketch was flashed to hardware during these checks. The supplied student sketch still contains only the intended motor and LSRB placeholders and an empty replay path.

## Implementation boundaries

- The app compiles the marked exercise functions as native C++, checks their outputs for every supported branch/speed input, and feeds those outputs to the shared sensor/wheel simulator. It does not emulate all Arduino instructions or arbitrary libraries. Full sketch compilation is separately checked with Arduino CLI.
- The simulator and SVG use one field definition. The unseen existing physical workshop field must be measured or built to match it; the match confirmation is an instructor attestation, not an automated measurement.
- The starter's 75% completion is six of eight assessed learning modules, not a source-line percentage.
- Physical motors, sensor response, turn timing, finish marker, HC-05 radio and the real field run remain unverified without hardware. Native compilation, browser success and mock transport are not substitutes for those tests.
- The scoreboard relies on local instructor observation and has no user authentication. Simulation certificates are held in backend memory for at most six hours and reset on backend restart; physical finish results persist on disk.
- The complete reference firmware and reference graph solver are retained for instructor tools. Students use the Day 2 workflow and blank workshop sketch.

The original sibling `maze-robot-control` directory was not edited. Historical verification.md and firmware-build-summary.txt describe the previous edition; the results above apply to version 3.

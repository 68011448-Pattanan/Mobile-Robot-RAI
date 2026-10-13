# Verification report — 2026-10-04

## Verified

- Original source retained; byte-for-byte comparison against supplied `maze.ino`.
- `npm run build`: production Next.js build and TypeScript checks pass.
- Python backend tests: 67 pass (path rules, cascading reductions, invalid paths, malformed telemetry, importer formats, topology, perspective/rotation/contrast/polarity/gaps, API, checksum/offset rejection, duplicate mutation and ACK retry/timeout).
- `tests/simulation_test.cjs`: weighted line position, sensor readings, physical learning, graph consistency, reduced replay, pause/resume, and motor stop pass.
- Newly generated PNG, not a hard-coded maze: extraction creates an editable graph; selected endpoints/scale feed the sensor model; learning produces LBLF→FF; optimized replay reaches finish.
- Live independent backend + mock serial-bridge process: connect, telemetry, PID/speed commands, 100-character path upload plus compact maze upload, checksum and exact byte readback, maze clear, scan events, automatic raw TXT save/download, run/pause/resume/STOP, recording/CSV export, invalid path rejection, disconnect and reconnect pass.
- Uno firmware compilation with Arduino AVR core1.8.6, Adafruit MCP3008 1.3.3, BusIO1.17.4. Fits 32KBflash / 2KBSRAM. Final memory figures are included in `firmware-build-summary.txt`.
- Browser interaction: dashboard loads, sensor-based learning completes with path LBLF, reduced FF, optimized replay completes; PID controls and path analyzer inspected. A Recharts development-mode array-freeze error discovered during QA was fixed by producing fresh sensor arrays on each sample.
- Compose YAML parses and referenced build contexts/Dockerfiles exist.

## Maze upload update

- Reviewed map packing retains interior geometry points, physical millimeter coordinates, heading, line width, connectivity and start/finish.
- Tests cover invalid/unreviewed metadata, node capacity, disconnected topology, coordinate bounds, malformed maze packets, chunk offsets, duplicate transfer IDs, checksum rejection, exact readback and deliberate readback corruption with abort cleanup, and paused-robot rejection.
- Independent live bridge test uploads the external PNG-derived maze model, reads every stored byte back and clears it.
- Firmware MAZE_V3 compiles for Uno: 21594 bytes flash (66%); 1100 bytes global SRAM (53%), 948 bytes remaining. Streaming EEPROM chunks adds only four global SRAM bytes over the earlier sketch.
- Production frontend build passes; updated UI type checks pass. The new button was verified through build/source inspection; no physical EEPROM, Bluetooth or USB transfer was available.

## Live unknown-maze discovery update

- Inferred route topology is built from cumulative robot turn reports without importing or uploading a maze.
- Tests cover incremental nodes, known-edge backtracking, duplicate reports/ACKs, prefix recovery, divergence/reset, pause/stop/error, finish without turns, no coordinate-based loop closure, live broadcast snapshots, telemetry-gap warnings, and replay-finish isolation.
- Compact saved-map decoding round-trips geometry including negative coordinates; invalid stored payloads and reading during motion are rejected. Reads issue only GET commands.
- Live independent mock integration proves a partial discovery snapshot and a WebSocket discovery update arrive while SCAN is still active, before completion; backtracked corridor counts and final finish are checked.
- Offline animated demo fixtures match the backend inference. Browser QA opened Live discovery and started the labeled synthetic demo. The final animated frame and screenshot were unavailable because the browser blocked a subsequent inspection; full live browser-to-backend testing remains unverified. Backend live WebSocket and frontend production build checks passed independently.
- Firmware is byte-for-byte unchanged from MAZE_V3 in the prior ZIP. Existing USB and Bluetooth path/status reports supply this feature; the prior Uno compile figures remain valid.

## Not verified in this environment

- **Docker binary/runtime is unavailable**: `docker compose config` and `docker compose up --build` could not execute. Backend and frontend were built/run directly instead. The provided Compose configuration is structurally validated, but container startup is not claimed as tested.
- **No physical Uno, motors, ADC sensors, HC-05 or Windows COM port was available**. Firmware compilation and mock protocol tests do not establish physical behavior. Confirm wiring, motor direction, sensor ordering/polarity/calibration, finish marker and turn timing on the real robot.
- Browser preview is isolated from the localhost backend. Browser QA covered the frontend/simulator; importer, real-mode commands and storage were exercised using API tests and the live mock integration instead of the browser.
- No unbounded arbitrary-maze completion guarantee. Loops, weak image extraction, unusual angles, insufficient turn clearance or incompatible line width can prevent sensor simulation or physical LSRB completion.

## Reproduce the external-maze acceptance flow

1. Upload `mazes/external_test.png` (or your own maze) in Maze workspace.
2. Choose black-line interpretation; extract.
3. Inspect binary, skeleton and graph; manually correct any topology errors.
4. Set left endpoint as start, right endpoint as finish, heading0, scale1mm/pixel. Mark topology reviewed.
5. Start learning. The included test should produce `LBLF`, then reduce to `FF`.
6. Download FF asTXT; reload it; run optimized replay.
7. Run the mock bridge and repeat upload/readback/run/stop in Real mode.
8. Only after checking actual hardware, repeat on the physical robot.

## Test limitations

The deterministic mock validates software transport; it does not execute the actual Arduino C++ code. A photographed maze test uses a synthetic perspective warp with manually supplied corners, rather than a real camera photograph. Add real field photographs and measured robot parameters when validating your workshop setup.

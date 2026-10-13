# Maze Robot Digital Twin & Control Center

A local Next.js/TypeScript dashboard, FastAPI backend, Arduino Uno firmware, and host serial bridge. **Both wired USB and HC-05 Bluetooth are supported.** Simulation runs without a robot.

## Quick start (Windows)

Install Docker Desktop with Compose. Unzip this folder, open a terminal in it, and run:

```powershell
docker compose up --build
```

Open **http://localhost:3000**. Backend health: http://localhost:8000/health; interactive API reference: http://localhost:8000/docs.

For simulation: click **Start learning run**, inspect the sensor values and timeline, then **Run optimized path**. The learning example reduces `LBLF` to `FF`.

### Wired USB Arduino

1. Arduino IDE: install **Adafruit MCP3008**, including **Adafruit BusIO** when asked.
2. Open `firmware/maze_hc05/maze_hc05.ino`. Select **Arduino Uno** and the correct COM port. Upload.
3. Close Arduino Serial Monitor/Plotter; only one process can own a COM port.
4. Connect a data-capable USB cable. Windows Device Manager → Ports shows the COM port.
5. On the **Windows host**, outside Docker:

```powershell
python -m pip install -r serial-bridge/requirements.txt
python serial-bridge/serial_bridge.py --list
python serial-bridge/serial_bridge.py --port COM5 --transport USB --baud 115200
```

6. Choose **Real robot** in the app. Check transport, port, and telemetry. Arm motion deliberately, then start a learning run.

### HC-05 Bluetooth

Wire the module as described below. Pair it through Windows Bluetooth settings; its PIN depends on its configuration (common factory values are 1234 or 0000). In Bluetooth COM-port settings choose the **outgoing SPP serial port**, not the incoming one.

```powershell
python serial-bridge/serial_bridge.py --port COM6 --transport Bluetooth --baud 9600
```

The same dashboard and protocol are used. A USB connection is not needed for Bluetooth control after flashing. `serial-bridge/start_windows.bat` installs bridge requirements and asks for the port and transport. The bridge automatically selects 115200 for USB or 9600 for Bluetooth unless `--baud` overrides it.

**Do not try to map a Windows COM port directly into Docker Desktop.** The bridge forwards that port over a local WebSocket.

### No hardware: mock connection

```powershell
python serial-bridge/serial_bridge.py --mock
```

This deterministic fake robot exercises telemetry, commands, acknowledgements, path and maze transfer, recordings and reconnect behavior. Its sensor values and maze events are fixtures; they are not measurements from a real robot.

## Upload paths and mazes to the robot

Reflash the included `firmware/maze_hc05/maze_hc05.ino` (reports **MAZE_V3**), then rebuild the app with `docker compose up --build`. The updated firmware is required for maze transfers; older firmware returns an error.

1. Connect the host bridge using USB or paired HC-05 Bluetooth and choose **Real robot**.
2. Stop motion. In **Maze workspace**, import or draw the maze, set physical scale, start, finish and heading, inspect the graph, and check **Topology reviewed**.
3. Click **Upload maze to robot**. The app validates the compact map, sends numbered chunks, checks its checksum, and compares every stored byte by readback. The success message reports nodes, segments and storage used.
4. In **Path analyzer**, load or edit the L/F/R/B path, then click **Upload & verify on robot**. Arm motion and choose **Run on robot** when ready. **SAVE PATH** persists the replay instructions separately.
5. **Real robot → GET MAZE INFO** inspects saved map metadata. **CLEAR MAZE** deletes only the stored maze.

The compact maze persists in Uno EEPROM across power cycles. It stores coordinates at 1 mm precision, all polyline samples as nodes, connectivity, start/finish, heading and line width. Capacity is **64 nodes including curve samples and 128 segments**. Oversized maps are rejected; simplify the graph explicitly. Images and JSON remain in the app.

The current firmware stores and returns the map; its driving algorithm follows physical line sensors and the separately uploaded path. Map storage alone does not provide localization or generate driving instructions. Maze uploads never start motors. A new upload invalidates the previous saved map before writing; interrupted or failed uploads leave no valid maze, while the saved path stays intact. If interrupted, stop and use **CLEAR MAZE** or retry the upload to clear staging.

## Live discovery of an unknown maze

You do **not** need to import, draw or upload a maze first. Open **Live discovery** (selects Real robot), connect the USB or HC-05 host bridge, place the robot at the entrance facing into the first corridor, arm motion, and click **Start real learning**.

The backend consumes the cumulative `PATH_RAW` reports and scan/finish/error status from the robot. The webapp updates as reports arrive, showing visited route nodes, explored corridors, reported dead ends, inferred return traversals, the last reported junction and an intended next corridor. This display also appears on the real dashboard. A new acknowledged learning run starts a fresh discovery session. Reconnecting browser clients receive the current snapshot; cumulative raw paths recover intermediate turn reports. If the backend itself restarts, retained robot raw-path readback can rebuild an inferred history, but timestamps, a finish observation and other transient events are not recoverable unless still reported.

**Export discovered map** downloads a `DiscoveredMaze` JSON observation snapshot with explicit schematic units and unknown distances. It is distinct from a physical, scaled MazeModel and cannot be uploaded as a measured robot map. Recordings also retain discovery broadcasts. **Preview learning demo** animates clearly labeled synthetic reports when no robot is connected; it never sends motion commands and automatically exits when a bridge connects.

The marker identifies the latest **reported** junction, not continuous x/y position. The inference assumes a tree maze, a robot aligned at its starting entrance, successful 90° turns and no missed junctions. It never joins nodes just because their schematic screen positions coincide. Arbitrary loop closure, unvisited branches, corridor shapes, exact distances and heading drift remain unknown with the current telemetry. This is a partial route topology inferred from commanded turns; a sensor or turn failure can invalidate it. Status gaps and reported failures add uncertainty warnings.

The included MAZE_V3 firmware already streams the needed path and status packets; this feature requires updating/rebuilding the app and backend, **not another firmware change** from the previous package. To inspect a previously uploaded EEPROM maze, stop or pause and choose **Read stored maze from robot**. The app checks checksum, metadata and geometry before opening it in Maze workspace. EEPROM readback is separate from live learning, which does not depend on a saved map.

## Architecture

- Frontend: Next.js, React, TypeScript, Tailwind, a shadcn-style Radix button primitive, Recharts, SVG editor/rendering.
- Backend: FastAPI, Pydantic, WebSockets, OpenCV, NumPy, scikit-image, SVG parsing, Shapely, PyMuPDF.
- Host bridge: PySerial; one bridge/serial port at a time; auto-reconnects.
- Firmware: hardware UART for USB; SoftwareSerial D9/D10 for HC-05; fixed 10 ms control tick and bounded motion phases.
- `frontend/lib/robot.ts`: common `RobotState`, sensor simulation, differential-drive integrator, path optimizer, independent graph LSRB tracer.
- `backend/app/maze.py`: maze extraction and graph analysis; `core.py`: packet/path validation; `main.py`: API and robot routing.

Docker exposes the app and backend on loopback only. This is a local robotics tool, not an authenticated Internet service. Do not expose its command endpoints publicly.

## Wiring

| Signal | Uno pin / connection |
| --- | --- |
| Left motor PWM / INA / INB | D5 / D2 / D3 |
| Right motor PWM / INA / INB | D6 / D4 / D7 |
| MCP3008 CLK / DOUT / DIN / CS | A0 / A1 / A2 / A3 (software SPI) |
| HC-05 TXD | D9 (Uno software RX) |
| HC-05 RXD | D10 through a 5 V-to-3.3 V divider |
| HC-05 ground | Common GND |
| HC-05 supply | Supply rated for your breakout; do not assume a bare module accepts 5 V |
| Stop button | D8 to GND, `INPUT_PULLUP` |
| USB control | Uno USB port; 115200 baud |

Suggested RX divider: D10 → **1 kΩ** → HC-05 RXD, and RXD → **2 kΩ** → GND. Verify the breakout's electrical ratings. The MCP3008 and motor pin layout matches the supplied `maze.ino`. The motor driver model and actual sensor orientation were not supplied: verify direction and driver truth table with the wheels lifted before a floor run.

The start button has intentionally become a **stop button**. Motion begins from the explicitly armed dashboard. The original firmware is preserved byte-for-byte in `firmware/original/maze.ino`.

## Import a maze

Open **Maze workspace** and choose/drop PNG, JPG/JPEG, WEBP, BMP, SVG, PDF, JSON, CSV or TXT (maximum 16 MB).

1. Choose line polarity: auto, black line, white line. Choose **Line maze** or **Wall maze**.
2. Adjust threshold/adaptive threshold, contrast, blur, minimum component size, and morphology opening. After initial extraction, changes update the preview with a debounce.
3. PDF: select a 1-based page. The selected page is rasterized at 2× resolution.
4. Inspect original, corrected, binary, centerline and graph views.
5. Photo: in Original view select four corners in TL, TR, BR, BL order; click **Correct perspective & extract**. Use crop `x,y,width,height` in the corrected image coordinate system; rotation/flip are also available.
6. Use the graph editor to fix gaps and junctions. Nothing automatically connects uncertain endpoints. Opening morphology removes small features; it can alter topology, so review again after processing.
7. Select **Set start** and **Set finish**, then click nodes. Choose heading: East 0°, South 90°, West 180°, North −90°.
8. Set physical scale in mm/pixel or use **Scale** to click two points and enter their known distance.
9. Inspect compatibility analysis. Check **Topology reviewed**, then start simulation.

**Wall maze imports produce a Converted Path** through corridor centers; the physical line robot cannot drive an unmodified wall maze unless that centerline is physically laid down.

SVG: supported path/line/polyline/polygon geometry is retained, including sampled curves and split intersections. Enter SVG element IDs to exclude borders/decorations. Transformed SVGs fall back to raster processing. PDFs currently use raster extraction. Start/finish recognition is a suggested endpoint choice, not semantic label recognition; always verify it.

Confidence is a topology/noise heuristic, **not a calibrated probability**. A noisy or excessively complex extraction reports an error; reduce noise/crop or draw the maze. Best-effort import does not guarantee that every photograph is interpreted correctly.

## Draw, edit and store mazes

Tools: Line (two clicks), Curve (start/control/end), 90° turn, T junction, Cross, Connect, Node, Dead end, Split, Move, Erase, Set start, Set finish, and Scale. Grid snapping is configurable. To intersect lines, split them at the intersection and connect their common node. A dead end is a node with one connected edge.

Rotate or flip the graph, change line width, export JSON, or edit the full JSON for precise topology corrections. The current maze persists in browser local storage; **Save maze** writes the backend maze library. Included examples and generated seeded tree mazes use the same model. `mazes/` is a Docker bind mount.

CSV/TXT grid: default `1=wall`, `0=open`, `S=start`, `F=finish`; open/wall values can be configured. Grid input uses cell-center lines, rather than a complete rasterized corridor-clearance model. JSON details: `docs/maze-format.md`.

## Simulator and PID lab

Eight footprints sample distances to maze line geometry. Readings become 10-bit ADC values, calibrated to 0–1000. Weighted position follows the original thresholds (>50 contributes; any >200 detects a line); no-line behavior remembers which side the line was last seen on.

The robot integrates separate wheel speeds, wheel track and first-order motor lag. Kp/Ki/Kd, P/PI/PD/PID mode, speed, sensor noise, spacing, offset, calibration and threshold are adjustable. Telemetry charts show position, error, P/I/D, correction and motor outputs. Pause/reset/step and 0.25×–4× speed are available.

Per-tick controller: `P=Kp*error`, `I=Ki*sum(error)`, `D=Kd*(error-lastError)` at a nominal 10 ms tick. This is **not a continuous-time gain convention**. Original code used variable-rate PD, so its numerical gains are starting points, not guaranteed equivalent physical tuning.

Junction triggering uses the sensor array. For simulation branch probing, geometry is sampled around the robot pose, rather than steering toward graph nodes. This probe is an educational abstraction of physically checking branches, **not a complete replica of the original timed sensor-signature behavior**. The graph tracer is explicitly separate from this physical model. Finish is detected from proximity to the marked finish in simulation; physical firmware uses the original broad-line signature / replay exhaustion.

No slip, friction variation, battery sag, gearbox backlash or calibrated sensor optical response is modeled. Geometry and motor parameters are illustrative and must be measured on your robot.

## LSRB and path reduction

Left → Straight (`F`) → Right → Back priority. Raw path uses `L/F/R/B`; maximum 100 decisions. Dead-end triples compose turn angles modulo 360; every rule and animated reduction is shown in Path analyzer. V2 repeats cascading suffix reductions.

This is a **reduced learned route**, not a universal shortest-path algorithm. A tree maze is the suitable case. Loops can cause a left-hand-rule cycle; graph tracing detects repeated states and provides a Dijkstra distance comparison. The physical robot has no absolute position/encoder-based loop detector.

## Paths: receive, save, upload, replay

Robot path packets are automatically saved as timestamped raw/shortest TXT files in `paths/`. Download from Path analyzer, or export the displayed path. TXT accepts 1–100 uppercase `L/F/R/B` symbols, whitespace, and optional `#` comment lines.

The path editor supports insert/delete/reorder/clear/optimize/download/load. **Upload & verify on robot** sends BEGIN, offset-indexed 24-character chunks, and an additive 16-bit checksum. Each command has an ID/ACK; retries use the same ID; the firmware suppresses duplicate mutation. After commit the backend requests an exact readback. See `docs/protocol.md`.

Move the physical robot back to its start heading before **Run optimized path**. The simulator resets its pose automatically. EEPROM Save/Load path commands are available; ordinary uploads are stored in RAM.

## Real robot, manual drive and safety

Connection cards show transport, COM port, baud, ACK latency, packet count, malformed packets, missing status sequence packets, latest command and ACK. Arduino telemetry uses the same UI state model as simulation.

**EMERGENCY STOP requests STOP immediately**, bypassing the backend upload lock. It is a software stop; transmission/SoftwareSerial latency and disconnection can prevent immediate delivery. The D8 button supplies a local stop. Communication timeout stops active motion after 1.5 s without heartbeat. The backend supplies heartbeat only while a browser dashboard is connected. All tabs closed → heartbeat ceases. PAUSED is also guarded.

Manual mode uses hold-to-drive buttons or W/A/S/D; release/blur stops. Space requests emergency stop. Manual commands require renewal within 400 ms; browser/backend heartbeats alone cannot maintain manual movement.

No encoders: real position is snapped to estimated graph junctions using reported instruction progress. **No exact edge progress percentage is fabricated.** Wrong or missed junctions invalidate this estimate.

At 9600 baud, HC-05 transmits 5 packets/s round robin (each sensor/controller/status group about 1.25 Hz). USB 115200 supports full frames at 5, 10 or 20 Hz. Higher Bluetooth rates are rejected. SoftwareSerial transmission pauses normal control briefly; test physical tracking performance at low speed.

## Recordings and exports

Record physical telemetry/logs through the backend, or simulation frames/pose through the frontend. Stop & save, choose a run, replay state frames with a scrubber, and export JSON/CSV. The backend stores recordings in `recordings/`. This is telemetry/pose playback, not re-execution of physical motor commands. Keep the matching maze loaded; recording replay does not automatically restore a different maze layout.

## Native Linux serial alternative

The bridge also runs directly on Linux/macOS using `/dev/ttyACM0`, `/dev/ttyUSB0`, or paired RFCOMM device paths. Grant your user appropriate serial-device permissions. Optionally run the bridge inside Docker on Linux:

```bash
ROBOT_DEVICE=/dev/ttyACM0 docker compose -f docker-compose.yml -f docker-compose.linux.yml up --build
# Bluetooth device already paired/bound by the host:
ROBOT_DEVICE=/dev/rfcomm0 ROBOT_BAUD=9600 ROBOT_TRANSPORT=Bluetooth docker compose -f docker-compose.yml -f docker-compose.linux.yml up --build
```

Do not run a host bridge at the same time as the container bridge.

## Local development and tests

Python 3.12 and Node.js 22+:

```bash
python -m pip install -r backend/requirements.txt
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# Second terminal, project root:
cd frontend
npm ci
npm run dev
```

From project root:

```bash
python -m pytest tests -q
python tests/live_bridge_test.py
# Compile the pure TypeScript simulation and run deterministic checks:
frontend/node_modules/.bin/tsc frontend/lib/robot.ts --outDir tests/.compiled --module commonjs --target es2022 --skipLibCheck
node tests/simulation_test.cjs
# Windows: frontend\node_modules\.bin\tsc.cmd instead
npm run build --prefix frontend
arduino-cli compile --fqbn arduino:avr:uno firmware/maze_hc05
```

Validation results and environment limits: `docs/verification.md`. Full source review: `docs/firmware-analysis.md`. Requirement coverage: `docs/requirements.md`.

## Troubleshooting

- **COM port busy:** close Arduino Serial Monitor, other bridge processes and any serial tools.
- **USB COM missing:** use a data cable and the driver appropriate to your Uno/clone.
- **Bluetooth no telemetry:** select outgoing SPP port, verify TX/RX crossing, common ground and data-mode baud. A BLE browser connection is not appropriate for HC-05 Classic SPP.
- **Connected bridge but no robot:** flash V2, verify baud and use GET STATUS. The original sketch does not implement this protocol.
- **ACK timeout:** check COM port/link/power; motion commands are not blindly retried. Stop locally before reconnecting.
- **Robot spins or turns backwards:** check wheel assignment and direction pins, sensor left-to-right ordering, sensor polarity/calibration, then lower speed.
- **Turn timeout:** check line width/sensors and mechanical speed; turns are bounded at 2.5 s. Firmware remains responsive.
- **Import wrong/noisy:** crop labels/borders, adjust polarity/threshold, inspect binary and centerline, then correct the graph. Do not approve a graph you have not checked.
- **Looping maze:** LSRB does not guarantee completion; use graph analysis to understand the topology.
- **Path exceeds 100:** upload is rejected and learning enters ERROR on overflow; do not enlarge buffers casually on Uno.
- **Data disappeared:** keep the bind-mounted mazes/paths/recordings folders and the same project directory.
- **Docker ports occupied:** stop the process already listening on 3000/8000, or update Compose ports and `NEXT_PUBLIC_API_URL` consistently before rebuilding.

Hardware operation and Docker container startup could not be exercised in the authoring environment. Follow the first-run motor/sensor checks before physical use; this package does not claim those unperformed checks passed.

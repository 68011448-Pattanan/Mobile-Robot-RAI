# Maze Robot Control — Version 3 Day 2 Workshop

A separate edition of the existing robot control project for the requested 180-minute Day 2 workshop. Open the **Day 2 workshop** page to complete Arduino motor values and LSRB logic, observe the simulation, export a successful path into the Arduino sketch, and compete on the same physical field.

## Start on Windows

From this version 3 directory, with Docker Desktop running:

```powershell
docker compose -p maze-robot-v3 up --build -d
```

Open **http://localhost:3003**. The backend is at **http://127.0.0.1:8003**. These ports are separate from the previous edition. Docker includes the C++ compiler and Node.js simulation runtime. The checked-in `workshop/runtime/robot.js` is generated from `frontend/lib/robot.ts`.

```powershell
# Stop only this edition:
docker compose -p maze-robot-v3 down
```

## Student workflow

1. Review Day 1 wheel direction, sensors, calibration and PD line following. Follow the agenda in `docs/day2-workshop.md` or expand the agenda in the app.
2. Read the Bluetooth lesson. Pair the HC-05 in Windows and identify its **outgoing** serial COM port. Keep Arduino Serial Monitor closed while the bridge owns the port.
3. Open `firmware/workshop_robot/workshop_robot.ino` in Arduino IDE. Complete **only** the marked student exercise block: the left/right motor values for F/L/R/B and the LSRB decision function. The web editor can also edit this block and download the complete `.ino`.
4. If you edit on disk, save in Arduino IDE and click **Reload saved .ino** in the app. The firmware directory is mounted into Docker, so rebuilding the image is unnecessary for exercise edits. If you edit in the web editor, **Download current sketch** saves your work; the browser does not silently overwrite the disk file.
5. Compile the exercises, inspect your branch and motor checks, and run the student simulation. Use animation pause, step, speed and the scrubber to observe movement, sensor readings, motor commands and the junction timeline. Incorrect logic and incorrect motor signs affect behavior.
6. Have the instructor confirm that the physical field matches the supplied layout and dimensions. Successful learning **and** reduced-path replay, all branch/motor checks, and field confirmation are required for a pass certificate. A field-confirmation change or student code edit clears the current browser pass.
7. Click **Export passed Arduino sketch + path**. Put the downloaded file in a `workshop_robot` folder and open that file in Arduino IDE. Select Arduino Uno, install **Adafruit MCP3008** and **Adafruit BusIO**, compile and upload via USB. The exported sketch contains the exact passed exercise source and its reduced path. Power-up leaves the motors stopped.
8. Run the serial bridge on the Windows host, outside Docker:

```powershell
python -m pip install -r serial-bridge/requirements.txt
python serial-bridge/serial_bridge.py --list
python serial-bridge/serial_bridge.py --port COM6 --transport Bluetooth --baud 9600
# USB alternative:
python serial-bridge/serial_bridge.py --port COM5 --transport USB --baud 115200
```

9. Place the robot at START facing East. Check motor direction with the wheels lifted; calibrate the eight sensors using the Calibration tab. After instructor checks, arm physical motion and run the passed path, or test student LSRB learning on the real field. STOP and the local D8 stop button remain available. If the sketch is already flashed, a passed path can also be transferred over Bluetooth or USB with exact readback verification.
10. The instructor records the group name and confirms the observed physical finish. The first recorded physical finish wins. Results persist in `workshop/data/workshop-results.json`; simulation completion does not win the competition.

## What changing `.ino` does

The app extracts the marked exercises from the actual student sketch, compiles them as C++, and executes them for all eight L/S/R branch combinations and motor speeds 1–100. Their outputs drive the simulator's junction decisions and wheel commands. The Arduino calls those **same functions** from its supplied firmware scaffold. No second student TypeScript algorithm is required.

This is a shared-function simulation adapter. It does not emulate the entire Uno, SoftwareSerial timing, arbitrary Arduino libraries, `setup()`/`loop()` edits, or the complete sketch instruction by instruction. The accepted exercise subset is integer expressions, supplied variable/function names and `if`/`else`/`return`. Compiler diagnostics point to `.ino` line numbers. Changes outside the exercise block are rejected; the exported path is the one allowed scaffold substitution.

The physical sketch must still be flashed after changing the exercise code. Bluetooth path upload transfers driving instructions, not new firmware. The dashboard/PID simulator also compiles the saved exercise file on starting a learning or replay run; use **Day 2 workshop** for certificates and competition. Graph analysis is a reference tool, separate from student certification.

## Shared simulator / real field

`workshop/field.json` is the single workshop maze definition. Its supplied field is **700 × 520 mm**, with **14 mm lines**, an East-facing start, two dead ends, and a broad finish rectangle. Download the field SVG from the app and print/lay it at **100% actual size**. Do not select “fit to page”; this field exceeds A4. Use a large-format printer or lay black tape at the coordinates in `docs/day2-workshop.md`. Measure the result before confirming it matches the simulator.

The app generates the printable SVG from that exact maze model. If the real workshop field already exists and differs, the instructor must update `workshop/field.json` to its measured graph, dimensions, heading and line width before the exercise. The geometry must be a connected line tree with suitable right-angle junctions. Restart the page after changing the file; old certificates are rejected automatically when the field hash changes. The initially supplied field is an example, not a claim that an unseen existing field matches it.

Movement uses the existing sensor and differential-drive model. Branch sensing and finish detection are abstractions; wheel slip, battery sag, mechanical direction and sensor response still require physical verification. Simulation success is preparation for the field test, not proof that the physical robot will pass.

## Starter completion and instructor materials

Six of eight assessed learning modules are provided: sensor acquisition, calibration, PD control, Bluetooth/protocol, path storage/transfer, and bounded motion/state handling. Students complete motor values and LSRB. This is **75% completion by workshop module coverage**, not a percentage of source lines (protocol boilerplate makes line counts misleading).

- Lesson plan, field coordinates and competition rules: `docs/day2-workshop.md`.
- Complete and incomplete student example sketches: `workshop/student-examples/README.md`.
- Requirement mapping: `docs/day2-requirements.md`.
- Verification of this edition: `docs/verification-v3.md`.
- Instructor exercise answer: `workshop/instructor/solution.cpp`. Keep it out of the student handout.
- Existing advanced control documentation: `docs/reference-readme.md`. Its historical ports and verification reports describe the previous edition.

## Development and verification

The original `maze-robot-control` sibling folder is preserved. Version 3 reuses its importer, bridge, protocol, recordings and advanced control features. The complete reference firmware is retained separately from the blank student sketch.

```powershell
cd frontend
npm ci
npm run build:workshop
npm run typecheck
cd ..
docker compose -p maze-robot-v3 build
```

If the TypeScript simulator changes, regenerate `workshop/runtime/robot.js` with `npm run build:workshop` before building/running the backend. Native development needs Python dependencies, Node.js and `g++` on PATH; Docker is the supported Windows route for exercise compilation.

Backend tests, including native shared-code, failure cases, certificates and winner ordering, can run inside the built image:

```powershell
docker run --rm -v "${PWD}:/workspace" -w /workspace -e WORKSHOP_FIRMWARE=/workspace/firmware/workshop_robot/workshop_robot.ino -e WORKSHOP_ASSETS=/workspace/workshop -e DATA_DIR=/tmp/maze-v3-test maze-robot-v3-backend python -m pytest tests -q -p no:cacheprovider
```

`tools/prepare_workshop.py` rebuilds a **blank** starter and field from the reference firmware. It is a maintenance tool, not a student startup step; running it resets student edits. The web editor and compiler never modify the original edition or the on-disk student sketch.

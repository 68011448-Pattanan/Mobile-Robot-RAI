# Day 2 requirement mapping — version 3

| Requested behavior | Version 3 implementation | Verification boundary |
| --- | --- | --- |
| Continue Day 1, total 180 minutes | App agenda and day2-workshop.md; 15+25+20+45+15+50+10 = 180 | Instructor delivers the timed session. |
| Teach Arduino–computer Bluetooth | HC-05 lesson, wiring, outgoing SPP COM port, host bridge, commands and telemetry | Mock transport can be tested; real radio requires hardware. |
| Teach LSRB | Student function, eight branch cases, robot timeline, path reduction, real learning | Tree-maze assumptions; no arbitrary loop guarantee. |
| Simulation and real practical parts | Dedicated Day 2 workflow with compiler, animation, certificates, export and field controls | Simulation models physical behavior approximately. |
| Students complete simulator LSRB | Actual student `.ino` function compiled as C++; its outputs select simulated branches | Only the marked exercise subset is supported; full Uno emulation is not provided. |
| Observe robot behavior | Animated pose and route, frame step/pause/scrub, motor values, sensor ADC and events | A deterministic run is computed first, then animated. |
| Identical simulator and physical maze | One field.json drives simulation and printable SVG; dimensions/coordinates; instructor match confirmation | An unseen existing real field cannot be certified automatically. |
| Pass simulated path to real code | Passed sketch export fills WORKSHOP_REPLAY; passed TXT and Bluetooth/USB transfer with readback | Sketch must be flashed for code changes; uploading a path does not flash firmware. |
| 70–80% complete real starter | Six of eight learning modules supplied = 75%; only motor values and LSRB are exercises | Percentage is explicitly by learning module coverage, not source lines. |
| Test on real field after coding | Passed-path replay, real student LSRB learning, calibration, arm and stop controls | Actual motor/sensor/radio behavior needs the instructor's physical test. |
| First group to pass wins | Persisted instructor-confirmed scoreboard ordered by successful finish record | Local instructor tool; simulation alone cannot win. |
| Changing `.ino` changes simulation | C++ compiler evaluates the saved/uploaded exercise block; shared simulator uses its outputs | Reload saved file or load an edited file, then compile/run again. |

The existing edition remains in the sibling maze-robot-control folder. Historical documentation copied from that edition is retained for reference; verification-v3.md records the checks on this edition.

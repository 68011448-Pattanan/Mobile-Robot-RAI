# Original source analysis and V2 changes

The supplied `maze.ino` is preserved unchanged under `firmware/original/`. Source inspection, rather than the prompt's illustrative names, determines this review.

## Hardware

Arduino Uno assumption. `Adafruit_MCP3008 adc`; `adc.begin(A0,A1,A2,A3)` uses software SPI, in CLK/MISO/MOSI/CS order. Channels 0–7 supply eight sensors. Original serial baud 9600. Motors: PWM1 D5, INA1 D2, INB1 D3; PWM2 D6, INA2 D4, INB2 D7. D8 is read as an input but is never explicitly configured in the original. Sensor defaults: Min=100, Max=800, raw black threshold 450. Arrays each hold 100 path symbols; original arrays are counted, not null-terminated strings.

## Data pipeline

`ReadPrivate()` samples ADC channels. `Read()` maps each raw measurement into 0–1000 and clamps. `ReadLine()` optionally inverts for BackGround=1; values >50 enter the weighted average; any value >200 marks a line. Position range is 0–7000 and target is 3500. If no line is present, the return is 0 or 7000 according to `LastValue`.

`Pid(BaseSpeed,Kp,Kd)` computes `Kp*Error + Kd*(Error-LastError)`. There is **no integral term**. Left=BaseSpeed+correction; Right=BaseSpeed−correction; each clamps to ±100 before percentage-to-PWM conversion. Original learning gains: BaseSpeed=30, Kp=.01, Kd=.08. Replay uses speed32 and Kd=.1. Original sample time depends on loop execution; V2 fixes nominal control ticks at10ms. Hardware SoftwareSerial output can extend that time, especially during command replies.

## Actual exploration policy

`TrackMaze()` first checks whether either outer pair detects black. It then handles:

1. Sensors0/1/2 black,5/6/7 white: left turn, record L.
2. Sensors1/2/5/6 black: move forward30ms. If1/6 remain black, move another60ms, stop, calculate reduced path and finish. Otherwise turn left and record L.
3. Sensors0/1/2 white,5/6/7 black: forward20ms. If any center2–5 remains black, record F; otherwise right turn and record R.
4. Otherwise, center2–5 all white: U-turn, record B.

Other outer-pair signatures can fall through without a decision. This is a sensor-pattern policy resembling left-first exploration; it is not a general arbitrary-maze graph solver. The physical V2 retains these signatures/probes. The simulator uses general geometry-based branch probes and is labeled an approximation.

## Turns and replay

`FF(Time)` calls `Move(BaseSpeed,BaseSpeed,Time)`. `LL(Time)` first advances for Time ms, pivots left50ms, then pivots until normalized sensor0≥100 and runs PD50ms. `RR` uses sensor7. `Uturn` advances100ms and pivots right using sensor7. **LL(30) means forward30ms before a sensor-based left pivot**, not turn30degrees.

`RunShortestPath()` consumes instructions at outer-pair junctions, with L/R30ms advance, F50ms, and Uturn for B. Original stops when a further junction is seen after path exhaustion. Original dead ends during replay are not independently handled.

## Optimization correctness

L=−90°, F=0°, R=+90°, B=180°. All nine supplied dead-end rules are mathematically correct modulo360. Original makes one suffix reduction per incoming symbol; a cascade can therefore remain reducible until a later symbol arrives. V2/JS/Python repeat suffix reduction immediately. This changes intermediate memory contents while preserving turn equivalence.

A reduced left-hand route is shortest under suitable tree-maze assumptions. These transformations alone do not find shortest routes in graphs with loops, nor establish metric optimality.

## Significant modifications

| Original behavior | Problem | V2 modification | Reason / effect |
| --- | --- | --- | --- |
| Scans and replay run in setup() inside while(true) | Cannot continuously receive commands | Explicit states and loop-based tick | Serial remains serviced between motion phases |
| D8 input not configured; ambiguous `!digitalRead(8)==1` | Floating input / unclear button polarity | INPUT_PULLUP; button to ground stops | Motion starts from dashboard, pressing button stops |
| Blocking delay and unbounded sensor turn waits | Lost communication or endless pivot | millis() phases; 2.5s turn timeout | Timeout enters ERROR and stops motors |
| Left stop uses PWM255; right stop uses PWM0 | Driver-dependent asymmetric stop | Both channels PWM0 and both direction inputsLOW | Symmetric de-energized stop; confirm actual driver truth table |
| No command protocol | Random debug output cannot control/verify transfers | Versioned newline protocol; command IDs, ACK/ERR | Host validates packets and verifies exact path readback |
| Silent raw-path overflow | Learned route becomes truncated | ERROR on overflow; uploads rejected >100 | No silent truncation |
| Zero calibration span possible | Divide-by-zero mapping | Calibration checks and denominator guard | Reject invalid written calibration |
| Variable-rate PD only | Gains difficult to compare; no I term | Nominal10ms P/PI/PD/PID; anti-windup | Educational modes and consistent per-tick gain convention |
| One suffix reduction per symbol | Cascades may remain | Repeated suffix reductions | Fully reduced path under supported rules |
| UART only used for debug | No wired control / HC-05 link | USB Serial115200; SoftwareSerial D9RX/D10TX9600 | Same protocol on either transport, with active-transport ownership |
| No heartbeat/manual watchdog | Motion could continue after disconnection | 1.5s heartbeat timeout;400ms manual renewal | Stops active/paused modes after lost supervision |
| Replay relies only on outer-pair junction | Dead-end B replay can fail | Validate/consume B at dead ends; exhaustion stops | Avoid silently making an unexpected turn |
| Replay automatically changes speed/Kd to32/.1 | Overwrites interactive tuning | V2 retains explicitly configured gains for both runs | Replay defaults can be set with SET_SPEED/SET_PID before START_RUN |
| No persistence | Power cycle loses replay path | Explicit EEPROM SAVE_PATH/LOAD_PATH with checksum | Avoid wearing EEPROM on every telemetry update |

Bluetooth telemetry is round robin at5 packets/s. USB emits complete four-packet frames at5/10/20Hz. No battery voltage is invented: the source has no battery measurement pin or circuit.

## Hardware limits

Sensor ordering, actual Min/Max, motor driver truth table, motor speed, wheel track, button wiring and finish-marker geometry must be confirmed on the physical robot. V2 compiled for Uno; compilation does not prove physical tracking or electrical correctness. SoftwareSerial sends block briefly; STOP is responsive between packets, not a hard real-time safety system. The existing U-turn sensing convention is retained with a time bound; unusually shaped junctions can still require physical tuning.

Official references consulted:
- https://github.com/adafruit/Adafruit_MCP3008
- https://github.com/arduino/docs-content/blob/main/content/learn/07.built-in-libraries/04.software-serial/software-serial.md

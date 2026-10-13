# Serial protocol v1

ASCII newline-terminated packets. USB115200, HC-05 data mode9600. Firmware command line length maximum79characters (excluding LF). It rejects overflow until the next newline. Only one active transport owns moving control; a second transport cannot take control while moving. The bridge sends all lines without modification.

## Host → robot

`C,<id>,<COMMAND>[,<args...>]` — ID integer0–59999, matched in ACK/ERR. Backend serializes commands and retries idempotent commands up to3attempts with2s ACKtimeout using the sameID. Motion commands START_SCAN/START_RUN/RESUME/DRIVE are not blindly retried. Firmware caches the most recent successfully mutatingID; duplicate commands are acknowledged without repeated mutation. GET commands can be repeated to re-read state. Backend reconnect handshakes with GET_STATUS.

`HEARTBEAT` — no ACK. Backend sends every0.5s while a browser client is present. Firmware stops active/paused states after1.5s without valid active-transport heartbeat/command. Manual movement additionally needs DRIVE renewal every400ms.

| Command | Arguments / behavior |
| --- | --- |
| PING | PONG and ACK |
| GET_STATUS | HELLO, STATUS, both paths, CONFIG |
| GET_SENSORS | Eight raw ADC readings |
| GET_PATH / GET_SHORT_PATH | Raw / committed replay path |
| GET_CAL | Eight Min values, then eight Max values |
| START_SCAN | Clear raw path; enter SCAN from a nonmoving state |
| START_RUN | Require committed nonempty path; reset path index |
| STOP / RESET | Motors zero; STOPPED / IDLE |
| PAUSE / RESUME | Preserve active mode; stop / resume phase |
| DRIVE | Signed left,right percentages, each−100..100; excluded during automatic movement |
| SET_PID | kp,ki,kd; ranges0..1,0..1,0..2; finite numeric values |
| SET_CONTROLLER | 0=P,1=PI,2=PD,3=PID |
| SET_SPEED | Integer0..100 |
| SET_THRESHOLD | Integer rawADC0..1023 |
| SET_BACKGROUND | 0=highADCline,1=lowADCline |
| SET_TELEMETRY | USB5/10/20; Bluetooth5only |
| SET_CAL | index,min,max; index0..7;0≤min<max≤1023 |
| CAL_START / CAL_END | Sweep sensors manually over light/dark; collect extrema; validate spans |
| CLEAR_PATH | Clear raw/replay memory while stopped |
| PATH_BEGIN | Expected length1..100; clear staging buffer |
| PATH_CHUNK | Offset, L/F/R/B string; backend uses24symbols/chunk; exact offset checked |
| PATH_END | Decimal16-bit additive checksum; length/alphabet verified before commit |
| SAVE_PATH / LOAD_PATH | EEPROM replay path save/load with marker,length,checksum |

## Robot → host

| Packet | Fields |
| --- | --- |
| HELLO | firmwareName,protocolVersion |
| ACK | commandID,commandName |
| ERR | commandID,reason; firmware currently INVALID_OR_BUSY / BUSY_OTHER_TRANSPORT |
| SENSOR | raw0..raw7,0..1023 |
| NORM | normalized0..normalized7,0..1000 |
| CTRL | position,error,P,I,D,correction,leftMotor,rightMotor,kp,ki,kd,runtimeMilliseconds |
| STATUS | mode,pathIndex,statusSequence (16-bit wrapping; legacy2-field packet also accepted) |
| CONFIG | controllerIndex,baseSpeed,threshold,background,telemetryHz |
| CAL | min0..min7,max0..max7 |
| EVENT | eventName[,direction] — JUNCTION,FINISH,TURN_TIMEOUT,PATH_OVERFLOW,PATH_MISMATCH,LINK_TIMEOUT,MANUAL_TIMEOUT,BUTTON_STOP |
| PATH_RAW / PATH_SHORT | zero to100 L/F/R/B symbols |
| PATH_STORED | committed length |
| PONG | no fields |

Positions0..7000; target3500. PWM telemetry is a signed percentage, not0..255. Controller terms use per-control-tick gains. STATUS sequence estimates missing **status packets** only; it cannot count every dropped byte/sensor packet. A reset/large backward sequence jump is not classified as thousands of lost packets.

## Transfer example

```
C,41,PATH_BEGIN,4
ACK,41,PATH_BEGIN
C,42,PATH_CHUNK,0,LFRB
ACK,42,PATH_CHUNK
C,43,PATH_END,294
PATH_SHORT,LFRB
PATH_STORED,4
ACK,43,PATH_END
C,44,GET_SHORT_PATH
PATH_SHORT,LFRB
ACK,44,GET_SHORT_PATH
```

Checksum for `LFRB`:76+70+82+66=294 modulo65536. This is an additive integrity check, **not CRC or cryptographic authentication**. Exact post-commit readback provides additional transfer verification. Incomplete staged paths do not overwrite the prior committed path; motion cannot start using staging memory. New BEGIN resets staging. Concurrent backend uploads are serialized. Emergency STOP bypasses that serialization and is immediately forwarded.

Packet groups can arrive before ACK. The backend waits byID, stores telemetry independently, then requires a new PATH_SHORT readback packet matching the requested path. It does not accept an ACK alone as transfer success. Only explicit SAVE_PATH writes EEPROM.


## Compact maze storage (MAZE_V3 firmware)

All commands use the existing `C,<id>,<command>,<args>` envelope and ACK/ERR retry rules on USB115200 or HC-05 9600. Stop motion before starting; calibration and paused motion also reject uploads.

| Command | Arguments / behavior |
| --- | --- |
| MAZE_BEGIN | Payload length 19–888; invalidates previous map, starts EEPROM staging |
| MAZE_CHUNK | Offset, hex data representing 1–16 bytes; offset must equal received length |
| MAZE_END | Unsigned additive byte checksum modulo65536; validates format and commits marker last |
| MAZE_ABORT | Invalidates map and clears transfer staging |
| GET_MAZE_INFO | Emits MAZE_INFO,length,checksum,nodes,segments,start,finish,heading,lineWidth,version |
| GET_MAZE_CHUNK | Offset,count1–16; emits MAZE_DATA,offset,hex |
| CLEAR_MAZE | Deletes map only, clears staging |

`MAZE_INFO` returns nine zero fields when no valid map exists. Heading is tenths of a degree, normalized to0–3599; East=0 with screen coordinates (positive y downward). Line width is millimeters. Node indices are zero-based. The app verifies metadata followed by all bytes, rather than trusting ACK alone. Motion start/manual commands are rejected while a maze transfer is staged. Emergency STOP continues to bypass host transfer locks.

EEPROM path storage uses0–103; maze metadata uses128–132 and payload136–1023. Marker0xC7 at128 is written last; uint16 little-endian length at129, checksum at131. Starting or aborting upload clears marker. This single-bank scheme deliberately makes an interrupted new upload invalidate the old map. Bytes104–127 and133–135 are unused.

Payload version1: nine-byte header `<BBBBBhH`: version1, node count2–64, segment count1–128, start index, finish index, signed int16 heading in tenths of degrees, unsigned int16 line width. Follow with node records `<hh>` (x,y signed millimeters), then segment records `<BB>` (endpoint indices). Total length9+4*nodes+2*segments. The backend checks connected topology, finite scale/geometry, endpoint consistency, bounds and zero-length segments. Interior polyline points are retained as degree-two nodes, with millimeter quantization; no automatic geometry simplification. Firmware separately checks lengths, checksum, counts, indices, heading and line width before committing.

`POST /maze/upload` accepts the reviewed MazeModel and returns `{verified,bytes,capacity,nodes,segments,checksum}`. Invalid models return400; offline robot, busy firmware, failed transfers or differing readback return409. Failed transfers attempt MAZE_ABORT. Firmware map storage has no autonomous graph-navigation or localization behavior; replay uses the separately uploaded L/F/R/B path.


## Live unknown-maze discovery (host reconstruction)

No new firmware commands or predefined map are required. Existing `PATH_RAW,<cumulative LFRB decisions>`, `STATUS`, ACK of START_SCAN and `EVENT,FINISH` drive a host `DiscoveryMap`. Turn reports are commanded decisions, not encoder-confirmed pose observations. An incoming corridor is inferred when the next report arrives. B reports mark a dead-end hypothesis and return along the known incoming port. Other known ports can also be reused on later returns. Distinct hypothetical nodes are never merged by screen coordinates. Every inferred corridor has `length:null`.

`GET /discovery` returns `{map,connected}`. A map contains session/revision, phase, robotMode, rawPath, schematic nodes/edges, corridor traversal counts, currentNode (last reported junction), heading (relative quarter-turns), pending departure, observation history and warnings. `positionMeasured` and `distanceMeasured` are false; units are schematic. Node IDs and coordinates are display hypotheses rather than physical identifiers/measurements. Successful 90-degree turns, aligned entrance and tree topology are explicit assumptions.

WebSocket `/ws` sends `{type:"discovery",map:...}` at connection and whenever the learning topology or phase changes. Mode-only telemetry does not add fake travelled distance. Duplicate cumulative paths do not add nodes; growth recovers missed intermediate PATH_RAW packets; changed/truncated prefixes start fresh inference. Repeated START_SCAN ACK IDs do not reset an ongoing session. STOP/ERROR retain the latest partial map; explicit FINISH adds the final corridor and finish node once. STATUS PATH_READY alone does not prove learning finished. Manual/replay finish reports do not extend the previous learned graph. Map broadcasts are included in existing session recordings.

`GET /maze/robot` reads a stored compact EEPROM map after stop or pause: metadata, chunks, checksum, final unchanged metadata, binary format and connected geometry are validated. Only GET commands are issued; a failed read never deletes EEPROM content. This endpoint is not polled during learning; live discovery uses small existing streamed reports instead. Metadata/chunk packet arrival counters are separate so an unrelated maze-info response cannot satisfy a pending data read.

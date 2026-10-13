// Run after compiling frontend/lib/robot.ts into tests/.compiled/robot.js.
const assert=require('node:assert/strict');
const {Simulator,makeMaze,graphTrace,optimize}=require('./.compiled/robot.js');
const m=makeMaze();const s=new Simulator(m);assert.equal(s.state.position,3500);assert.ok(s.state.sensors[3]>500);s.start('SCAN');for(let i=0;i<60000&&s.state.mode==='SCAN';i++)s.tick(.01);assert.equal(s.state.mode,'PATH_READY');assert.equal(s.state.rawPath,'LBLF');assert.equal(s.state.optimizedPath,'FF');
const trace=graphTrace(m);assert.ok(trace.complete);assert.equal(trace.raw,s.state.rawPath);
s.start('RUN_PATH');for(let i=0;i<60000&&s.state.mode==='RUN_PATH';i++)s.tick(.01);assert.equal(s.state.mode,'PATH_READY');assert.equal(s.state.pathIndex,2);
s.start('SCAN');s.tick(.01);s.pause();const before={...s.pose};s.tick(.01);assert.deepEqual(s.pose,before);s.resume();s.tick(.01);assert.notDeepEqual(s.pose,before);s.stop();assert.equal(s.state.leftMotor,0);assert.equal(s.state.rightMotor,0);
assert.equal(optimize('LBLBL').path,'R');console.log('PASS sensor position, LSRB decisions, physical scan, reduction, optimized replay, pause/resume, stop, graph consistency');

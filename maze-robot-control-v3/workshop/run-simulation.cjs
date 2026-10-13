// Uses exactly the same Simulator class as the browser dashboard.
const {Simulator}=require('./runtime/robot.js');
let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk=>input+=chunk);
process.stdin.on('end',()=>{
  try {
    const {profile,maze}=JSON.parse(input);
    const sim=new Simulator(maze);
    sim.workshopProfile=profile;
    const frames=[];
    function capture(stage) {
      frames.push({stage,pose:{...sim.pose},state:JSON.parse(JSON.stringify(sim.state))});
    }
    function run(mode,stage) {
      sim.start(mode); capture(stage);
      let ticks=0;
      while(sim.state.mode===mode&&ticks<60001) {
        sim.tick(.01);
        if(++ticks%25===0) capture(stage);
      }
      capture(stage);
      return sim.state.mode==='PATH_READY';
    }
    const learned=run('SCAN','Learning');
    const raw=sim.state.rawPath,path=sim.state.optimizedPath;
    const events=[...sim.events];
    const replayed=learned&&path.length>0?run('RUN_PATH','Replay'):false;
    process.stdout.write(JSON.stringify({passed:learned&&replayed,raw,path,frames,
      events:[...events,...(replayed?sim.events:[])],
      reason:learned&&replayed?'Learning and reduced-path replay reached the finish.':sim.events.at(-1)?.text||'Robot did not finish.'}));
  } catch(error) {process.stderr.write(error.stack);process.exitCode=1;}
});

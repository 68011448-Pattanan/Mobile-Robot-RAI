'use client';
export type DiscoveredMaze={
 type:'DiscoveredMaze';session:string;revision:number;updated:number|null;phase:string;robotMode:string;
 rawPath:string;complete:boolean;units:'schematic';positionMeasured:false;distanceMeasured:false;
 nodes:{id:string;x:number;y:number;kind:string;visits:number}[];
 edges:{id:string;a:string;b:string;traversals:number;length:null;certainty:string}[];
 currentNode:string;heading:number;pending:{source:string;target:string|null;heading:number}|null;
 observations:{index:number;node:string;turn:string;heading:number;time:number}[];warnings:string[];
};
const vectors=[[1,0],[0,1],[-1,0],[0,-1]];
export function LiveDiscoveryMap({map,connected}:{map:DiscoveredMaze|null;connected:boolean}){
 const nodes=map?.nodes||[],edges=map?.edges||[];
 const current=nodes.find(n=>n.id===map?.currentNode);
 const minX=Math.min(0,...nodes.map(n=>n.x))-100,minY=Math.min(0,...nodes.map(n=>n.y))-100;
 const width=Math.max(480,Math.max(0,...nodes.map(n=>n.x))-minX+160),height=Math.max(300,Math.max(0,...nodes.map(n=>n.y))-minY+140);
 const heading=map?.pending?.heading??map?.heading??0,[dx,dy]=vectors[heading];
 const pendingTarget=nodes.find(n=>n.id===map?.pending?.target);
 const active=!!map?.pending&&['LEARNING','PAUSED','AWAITING_FINISH'].includes(map.phase);
 return <><svg className="maze discovery-map" viewBox={`${minX} ${minY} ${width} ${height}`} role="img" aria-label="Live schematic of robot-discovered junctions, unknown distances, and inferred backtracking">
 <defs><pattern id="discovery-grid" width="35" height="35" patternUnits="userSpaceOnUse"><path d="M35 0H0V35" fill="none" stroke="#182e43" strokeWidth=".6"/></pattern></defs>
 <rect x={minX} y={minY} width={width} height={height} fill="url(#discovery-grid)"/>
 {edges.map(e=>{const a=nodes.find(n=>n.id===e.a)!,b=nodes.find(n=>n.id===e.b)!;return <g key={e.id}><line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={e.traversals>1?'#ffb777':'#59dcb5'} strokeWidth="6" strokeLinecap="round"/><text x={(a.x+b.x)/2+9} y={(a.y+b.y)/2-10} fill="#9daec6" fontSize="11">{e.traversals>1?`${e.traversals} passes · `:''}distance ?</text></g>})}
 {active&&current&&<><line x1={current.x} y1={current.y} x2={pendingTarget?.x??current.x+dx*70} y2={pendingTarget?.y??current.y+dy*70} stroke="#a6c2f0" strokeWidth="3" strokeDasharray="6 6"/><text x={current.x+12} y={current.y+50} fill="#b8d0ef" fontSize="11">Next corridor · position unknown</text></>}
 {nodes.map(n=><g key={n.id}><circle cx={n.x} cy={n.y} r="10" fill={n.kind==='start'?'#58ebbd':n.kind==='finish'?'#ffb46e':n.kind==='dead-end report'?'#f17d8b':'#427cbb'} stroke="#0a1a2a" strokeWidth="3"/><text x={n.x+15} y={n.y-15} fill="#d1e2f5" fontSize="13">{n.id} · {n.kind}</text></g>)}
 {current&&map&&map.phase!=='WAITING'&&<g transform={`translate(${current.x} ${current.y})`}><circle r="19" fill="none" stroke={connected?'#bcecff':'#8596a8'} strokeWidth="2" strokeDasharray="3 4"/><path d="M-8 -7L9 0L-8 7Z" fill="#d8f3ff" transform={`rotate(${heading*90})`}/><text x="-35" y="-35" fill="#cee7ff" fontSize="11">Latest reported junction</text></g>}
 {(!map||map.phase==='WAITING')&&<text x={minX+width/2} y={minY+height/2} textAnchor="middle" fill="#90adc9" fontSize="16">Start learning — no predefined maze needed</text>}
 </svg><div className="map-bottom"><span>{nodes.length} route nodes · {edges.length} explored corridors</span><span>{map?.phase||'WAITING'} · {connected?'connected':'last snapshot / offline'}</span><span>Distances unknown</span></div></>;
}

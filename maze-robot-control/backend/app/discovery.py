"""Partial route topology from reported decisions, with no assumed physical distances.

Known corridors are reused when backtracking through a known port. Coordinate
coincidences NEVER merge nodes: without localization loop closure is ambiguous.
"""
import copy, time, uuid

TURN={'F':0,'R':1,'B':2,'L':3}
VECTORS=((1,0),(0,1),(-1,0),(0,-1))

class DiscoveryMap:
    def __init__(self):
        self.reset(False)

    def reset(self,learning=True):
        self.session='discovery-'+uuid.uuid4().hex[:12]
        self.raw=''; self.heading=0; self.current='N0'
        self.nodes=[dict(id='N0',x=0,y=0,kind='start',visits=0)]
        self.edges=[]; self.ports={}; self.observations=[]
        self.pending=dict(source='N0',target=None,heading=0) if learning else None
        self.phase='LEARNING' if learning else 'WAITING'; self.mode='IDLE'
        self.complete=False; self.revision=0; self.updated=None
        self.warnings=['Partial explored topology only. Corridor lengths and physical position are unknown.',
                       'Layout assumes successful 90° turns and a tree maze. Loops and missed junctions cannot be resolved automatically.']

    def _touch(self):
        self.revision+=1; self.updated=time.time()

    def _arrive(self,finish=False):
        if not self.pending: return
        source=self.pending['source']; heading=self.pending['heading']; target=self.pending['target']
        if target is None:
            origin=next(n for n in self.nodes if n['id']==source); dx,dy=VECTORS[heading]
            x,y=origin['x']+dx*140,origin['y']+dy*140
            # Keep distinct hypotheses readable without inventing loop closure.
            while any(abs(n['x']-x)<50 and abs(n['y']-y)<50 for n in self.nodes):
                x+=32 if dy else 0; y+=32 if dx else 0
            target='N'+str(len(self.nodes))
            self.nodes.append(dict(id=target,x=x,y=y,kind='finish' if finish else 'junction',visits=0))
            edge=dict(id='E'+str(len(self.edges)),a=source,b=target,traversals=0,length=None,certainty='inferred')
            self.edges.append(edge)
            self.ports[(source,heading)]=(target,edge['id'])
            self.ports[(target,(heading+2)%4)]=(source,edge['id'])
        edge_id=self.ports[(source,heading)][1]
        next(e for e in self.edges if e['id']==edge_id)['traversals']+=1
        node=next(n for n in self.nodes if n['id']==target); node['visits']+=1
        if finish: node['kind']='finish'
        self.current=target; self.heading=heading; self.pending=None

    def path(self,path):
        if path==self.raw: return False
        if not path:
            if self.raw:
                previous_mode=self.mode; self.reset(previous_mode=='SCAN'); self.mode=previous_mode; self._touch(); return True
            return False
        if not path.startswith(self.raw) or self.phase=='WAITING' or self.complete:
            previous_mode=self.mode; self.reset(previous_mode=='SCAN'); self.mode=previous_mode
            self.phase='LEARNING' if self.mode=='SCAN' else 'HISTORY'
        if self.pending is None and not self.raw:
            self.pending=dict(source=self.current,target=None,heading=0)
        for decision in path[len(self.raw):]:
            self._arrive()
            node=next(n for n in self.nodes if n['id']==self.current)
            if decision=='B': node['kind']='dead-end report'
            self.heading=(self.heading+TURN[decision])%4
            known=self.ports.get((self.current,self.heading))
            self.pending=dict(source=self.current,target=known[0] if known else None,heading=self.heading)
            self.raw+=decision
            self.observations.append(dict(index=len(self.raw),node=self.current,turn=decision,heading=self.heading,time=time.time()))
        self._touch(); return True

    def finish(self):
        if self.complete or self.phase=='WAITING': return False
        self._arrive(True); self.complete=True; self.phase='COMPLETE'; self._touch(); return True

    def status(self,mode):
        if self.mode==mode: return False
        previous=self.mode; self.mode=mode
        if mode=='SCAN':
            if self.phase=='WAITING': self.pending=dict(source=self.current,target=None,heading=0)
            if not self.complete:self.phase='LEARNING'
        elif mode=='PAUSED' and previous=='SCAN': self.phase='PAUSED'
        elif mode in ('STOPPED','ERROR') and not self.complete and self.phase!='WAITING': self.phase=mode
        elif mode=='PATH_READY' and self.phase=='LEARNING':
            # Wait for the explicit FINISH packet; PATH_READY alone is ambiguous.
            self.phase='AWAITING_FINISH'
        self._touch(); return True

    def gap(self,message):
        if message not in self.warnings:self.warnings.append(message);self._touch();return True
        return False

    def snapshot(self):
        return copy.deepcopy(dict(type='DiscoveredMaze',session=self.session,revision=self.revision,updated=self.updated,
            phase=self.phase,robotMode=self.mode,rawPath=self.raw,complete=self.complete,units='schematic',
            nodes=self.nodes,edges=self.edges,currentNode=self.current,heading=self.heading,pending=self.pending,
            observations=self.observations,warnings=self.warnings,positionMeasured=False,distanceMeasured=False))

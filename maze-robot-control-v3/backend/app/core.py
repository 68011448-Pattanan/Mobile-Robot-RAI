"""Shared path and telemetry contract. Percent motor commands, 0..7000 line position."""
import math
ANGLES = {'L': -90, 'F': 0, 'R': 90, 'B': 180}

def validate_path(text):
    path = ''.join(line.strip() for line in text.splitlines() if not line.lstrip().startswith('#')).replace(' ', '')
    if not path or len(path) > 100 or any(c not in ANGLES for c in path):
        raise ValueError('Path must contain 1–100 L/F/R/B instructions.')
    return path

def optimize(path):
    out=[]; steps=[]
    for c in path:
        out.append(c)
        while len(out)>=3 and out[-2]=='B' and out[-3] in 'LFR' and out[-1] in 'LFR':
            before=''.join(out); triple=''.join(out[-3:]); angle=sum(ANGLES[x] for x in triple)%360
            replacement={0:'F',90:'R',180:'B',270:'L'}[angle]
            out[-3:]=[replacement]
            steps.append({'before':before,'rule':triple,'replacement':replacement,'after':''.join(out),'angle':angle})
    return ''.join(out),steps

def checksum(path): return sum(ord(c) for c in path) % 65536

def empty_state():
    return dict(mode='IDLE',sensors=[100]*8,normalized=[0]*8,position=3500,error=0,kp=.01,ki=0,kd=.08,p=0,i=0,d=0,correction=0,leftMotor=0,rightMotor=0,rawPath='',optimizedPath='',pathIndex=0,lastIntersection='',runtime=0,threshold=450,minimum=[100]*8,maximum=[800]*8,telemetryHz=5,controller='PD',background=0)

def parse_packet(line, state):
    parts=line.strip().split(','); kind=parts[0]; vals=parts[1:]
    s=dict(state)
    def numbers(n):
        if len(vals)!=n: raise ValueError(f'{kind}: expected {n} fields')
        v=[float(x) for x in vals]
        if not all(math.isfinite(x) for x in v): raise ValueError('Nonfinite telemetry')
        return v
    if kind=='SENSOR':
        v=numbers(8)
        if any(x<0 or x>1023 for x in v): raise ValueError('ADC out of range')
        s['sensors']=v
    elif kind=='NORM':
        v=numbers(8)
        if any(x<0 or x>1000 for x in v): raise ValueError('Normalized out of range')
        s['normalized']=v
    elif kind=='CTRL':
        v=numbers(12)
        for key,x in zip(['position','error','p','i','d','correction','leftMotor','rightMotor','kp','ki','kd','runtime'],v): s[key]=x
    elif kind=='STATUS':
        if len(vals) not in (2,3) or vals[0] not in ['IDLE','CALIBRATION','MANUAL','SCAN','PATH_READY','RUN_PATH','PAUSED','STOPPED','ERROR']: raise ValueError('Invalid status')
        s['mode']=vals[0]; s['pathIndex']=int(vals[1])
        if len(vals)==3: s['sequence']=int(vals[2])
    elif kind in ('PATH_RAW','PATH_SHORT'):
        p=vals[0] if len(vals)==1 else None
        if p is None or len(p)>100 or any(c not in ANGLES for c in p): raise ValueError('Invalid path packet')
        s['rawPath' if kind=='PATH_RAW' else 'optimizedPath']=p
    elif kind=='CAL':
        v=numbers(16); s['minimum']=v[:8]; s['maximum']=v[8:]
    elif kind=='CONFIG':
        v=numbers(5); mode=int(v[0])
        if mode not in range(4): raise ValueError('Invalid controller mode')
        s['controller']=['P','PI','PD','PID'][mode]; s['baseSpeed']=v[1]; s['threshold']=v[2]; s['background']=v[3]; s['telemetryHz']=v[4]
    elif kind=='MAZE_INFO':
        if len(vals)!=9: raise ValueError('Invalid maze info')
        v=[int(x) for x in vals]
        if any(x<0 for x in v) or v[0]>888 or v[2]>64 or v[3]>128: raise ValueError('Invalid maze limits')
        s['robotMaze']=dict(zip(['bytes','checksum','nodes','segments','start','finish','heading','lineWidth','version'],v))
    elif kind=='MAZE_DATA':
        if len(vals)!=2 or not 0<=int(vals[0])<888 or not 2<=len(vals[1])<=32 or len(vals[1])%2: raise ValueError('Invalid maze data')
        bytes.fromhex(vals[1]); s['mazeData']={'offset':int(vals[0]),'hex':vals[1].lower()}
    elif kind=='EVENT': s['lastIntersection']=','.join(vals)
    elif kind not in ('ACK','ERR','PONG','HELLO','PATH_STORED','CONFIG'): raise ValueError('Unknown packet')
    return s

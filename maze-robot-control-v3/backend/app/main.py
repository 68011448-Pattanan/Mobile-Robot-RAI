import asyncio, json, time, os, csv, io, re
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, FileResponse
from pydantic import BaseModel
from .core import empty_state, parse_packet, validate_path, optimize, checksum
from .maze import import_maze, model, analysis
from .robot_maze import encode_maze, decode_maze
from .discovery import DiscoveryMap
from .workshop import create_router

ROOT=Path(os.getenv('DATA_DIR',str(Path(__file__).resolve().parents[2])))
for d in ('mazes','paths','recordings'): (ROOT/d).mkdir(parents=True,exist_ok=True)
discovery=DiscoveryMap(); last_scan_ack=None; maze_replies={"robotMaze":0,"mazeData":0}
state=empty_state(); bridge=None; clients=set(); connected=False; info={}; packet_count=0; errors=0; last_packet=0; last_ack=''; latency=None
waiters={}; logs=[]; recording=None; recording_id=None; next_id=1; command_lock=asyncio.Lock(); last_command=''; path_sequence=0; upload_lock=asyncio.Lock(); dropped_status=0; previous_sequence=None; maze_sequence=0

def safe_id(v):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',v): raise HTTPException(400,'Invalid file identifier')
    return v

async def broadcast(data):
    if recording is not None: recording.append({'timestamp':time.time(),'data':data})
    stale=[]
    for ws in tuple(clients):
        try: await ws.send_json(data)
        except Exception: stale.append(ws)
    for ws in stale: clients.discard(ws)

async def log(direction,line):
    row={'timestamp':time.time(),'direction':direction,'line':line}; logs.append(row)
    if len(logs)>5000: del logs[:1000]
    await broadcast({'type':'log','entry':row})

async def status():
    await broadcast({'type':'connection','connected':connected,'bridge':bridge is not None,'info':info,'packets':packet_count,'errors':errors,'lastPacket':last_packet,'latency':latency,'lastAck':last_ack,'lastCommand':last_command,'droppedStatus':dropped_status})

async def receive(line):
    global state,packet_count,errors,last_packet,last_ack,connected,path_sequence,dropped_status,previous_sequence,maze_sequence,last_scan_ack
    await log('RX',line); last_packet=time.time()
    try:
        state=parse_packet(line,state); packet_count+=1
    except (ValueError,TypeError,IndexError): errors+=1; await status(); return
    p=line.split(','); map_changed=False
    if p[0]=='ACK' and len(p)>=3:
        last_ack=line
        if p[2]=='START_SCAN' and p[1]!=last_scan_ack:
            last_scan_ack=p[1]; discovery.reset(); discovery.status('SCAN'); map_changed=True
        elif p[2]=='START_RUN':
            map_changed=discovery.status('RUN_PATH') or map_changed
        future=waiters.get(p[1])
        if future and not future.done(): future.set_result(p[2:])
    elif p[0]=='ERR' and len(p)>=3:
        future=waiters.get(p[1])
        if future and not future.done(): future.set_exception(ValueError(','.join(p[2:])))
    if p[0] in ('HELLO','STATUS','SENSOR','NORM','CTRL'): connected=True
    if p[0]=='HELLO': previous_sequence=None
    if p[0]=='STATUS' and len(p)==4:
        sequence=int(p[3]); delta=(sequence-previous_sequence)%65536 if previous_sequence is not None else 1
        if 1<delta<32768: dropped_status+=delta-1
        previous_sequence=sequence
    if p[0]=='PATH_SHORT': path_sequence+=1
    if p[0] in ('MAZE_DATA','MAZE_INFO'):
        maze_sequence+=1; maze_replies['mazeData' if p[0]=='MAZE_DATA' else 'robotMaze']+=1
    if p[0]=='STATUS': map_changed=discovery.status(state['mode']) or map_changed
    if p[0]=='PATH_RAW': map_changed=discovery.path(p[1]) or map_changed
    if p[0]=='EVENT' and len(p)>=2:
        if p[1]=='FINISH' and discovery.mode in ('SCAN','PATH_READY') and discovery.phase in ('LEARNING','AWAITING_FINISH','HISTORY'):
            map_changed=discovery.finish() or map_changed
        if p[1] in ('TURN_TIMEOUT','LINK_TIMEOUT','PATH_OVERFLOW'):
            map_changed=discovery.gap('Robot reported '+p[1]+': latest intended turn or inferred connection may be wrong.') or map_changed
    if p[0]=='STATUS' and len(p)==4 and 1<delta<32768:
        map_changed=discovery.gap('Telemetry gap detected; inferred topology may be incomplete.') or map_changed
    if map_changed: await broadcast({'type':'discovery','map':discovery.snapshot()})
    if p[0] in ('PATH_RAW','PATH_SHORT'):
        kind='raw' if p[0]=='PATH_RAW' else 'shortest'
        session=info.get('session','robot')
        (ROOT/'paths'/f'{session}_{kind}.txt').write_text(p[1]+'\n')
    await broadcast({'type':'state','state':state}); await status()

async def command(name,args='',retry=True):
    global next_id,last_command,latency
    if not bridge or not connected: raise ValueError('Robot not connected. Start the USB/Bluetooth host bridge.')
    if not re.fullmatch('[A-Z_]+',name) or '\n' in args or '\r' in args or len(args)>140: raise ValueError('Invalid command')
    async with command_lock:
        ident=str(next_id); next_id=(next_id+1)%60000; line=f'C,{ident},{name}'+(','+args if args else '')
        if len(line)>79: raise ValueError('Command exceeds the firmware 79-character limit')
        future=asyncio.get_running_loop().create_future(); waiters[ident]=future; start=time.monotonic(); last_command=line
        try:
            for attempt in range(3 if retry else 1):
                await log('TX',line); await bridge.send_json({'type':'tx','line':line})
                try:
                    result=await asyncio.wait_for(asyncio.shield(future),2)
                    latency=round((time.monotonic()-start)*1000,1); return result
                except asyncio.TimeoutError:
                    if attempt==(2 if retry else 0): raise ValueError(f'{name}: ACK timeout; robot may have reset or disconnected.')
        finally: waiters.pop(ident,None)

async def watchdog():
    global connected
    while True:
        await asyncio.sleep(.5)
        if connected and time.time()-last_packet>4: connected=False; await status()
        if bridge and clients and connected:
            try: await bridge.send_json({'type':'tx','line':'HEARTBEAT'})
            except Exception: pass

@asynccontextmanager
async def lifespan(app):
    task=asyncio.create_task(watchdog()); yield; task.cancel()
app=FastAPI(title='Maze Robot Control API',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:3003','http://127.0.0.1:3003','http://localhost:3000','http://127.0.0.1:3000'],allow_methods=['*'],allow_headers=['*'])
@app.get('/health')
async def health(): return {'ok':True}
@app.websocket('/ws')
async def ui_ws(ws:WebSocket):
    await ws.accept(); clients.add(ws)
    await ws.send_json({'type':'state','state':state}); await ws.send_json({'type':'discovery','map':discovery.snapshot()}); await status()
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect: clients.discard(ws)
@app.websocket('/bridge')
async def bridge_ws(ws:WebSocket):
    global bridge,connected,info,state,last_packet,last_scan_ack
    await ws.accept()
    if bridge: await ws.close(code=1008,reason='One bridge at a time'); return
    bridge=ws; state=empty_state(); last_scan_ack=None
    try:
        while True:
            data=await ws.receive_json()
            if data.get('type')=='hello':
                info={**data,'session':time.strftime('maze_%Y-%m-%d_%H-%M-%S')}; last_packet=time.time(); await status()
                await ws.send_json({'type':'tx','line':'C,0,GET_STATUS'})
            elif data.get('type')=='rx':
                line=str(data.get('line',''))
                if len(line)<=512: await receive(line)
            elif data.get('type')=='error': await log('ERROR',str(data.get('message')))
    except (WebSocketDisconnect,RuntimeError): pass
    finally:
        bridge=None; connected=False
        for f in list(waiters.values()):
            if not f.done(): f.set_exception(ValueError('Bridge disconnected'))
        await status()

class Cmd(BaseModel):
    name:str
    args:str=''
@app.post('/command')
async def cmd(c:Cmd):
    try:
        if c.name=='DISCONNECT':
            await command('STOP'); await bridge.close(); return {'ack':True}
        return {'ack':await command(c.name,c.args,retry=c.name not in ('START_SCAN','START_RUN','DRIVE','RESUME'))}
    except ValueError as e: raise HTTPException(409,str(e))
class PathBody(BaseModel): text:str
@app.post('/path/optimize')
async def path_opt(b:PathBody):
    try: p=validate_path(b.text); short,steps=optimize(p); return dict(raw=p,optimized=short,steps=steps,checksum=checksum(short))
    except ValueError as e: raise HTTPException(400,str(e))
@app.post('/path/upload')
async def upload(b:PathBody):
    async with upload_lock:
        return await upload_path(b)

async def upload_path(b:PathBody):
    try:
        p=validate_path(b.text)
        await command('PATH_BEGIN',str(len(p)))
        for offset in range(0,len(p),24): await command('PATH_CHUNK',f'{offset},{p[offset:offset+24]}')
        await command('PATH_END',str(checksum(p)))
        sequence_before=path_sequence
        await command('GET_SHORT_PATH')
        # ACK is insufficient: verify exact readback.
        for _ in range(20):
            if path_sequence>sequence_before and state['optimizedPath']==p: return {'verified':True,'path':p}
            await asyncio.sleep(.1)
        raise ValueError('Uploaded path readback did not match')
    except ValueError as e: raise HTTPException(409,str(e))
@app.get('/paths')
async def paths(): return [p.name for p in sorted((ROOT/'paths').glob('*.txt'),reverse=True)]
@app.get('/paths/{filename}')
async def download_path(filename:str):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+\.txt',filename): raise HTTPException(400,'Invalid path filename')
    p=ROOT/'paths'/filename
    if not p.exists(): raise HTTPException(404,'Path not found')
    return FileResponse(p,filename=filename)
async def maze_reply(name,args,key):
    before=maze_replies[key]
    await command(name,args)
    for _ in range(20):
        if maze_replies[key]>before and key in state: return state[key]
        await asyncio.sleep(.1)
    raise ValueError('Maze readback timed out')

@app.get('/discovery')
async def discovered_map():
    return {'map':discovery.snapshot(),'connected':connected}

@app.get('/maze/robot')
async def read_robot_maze():
    async with upload_lock:
        try:
            if state['mode'] in ('SCAN','RUN_PATH','MANUAL','CALIBRATION'):
                raise ValueError('Stop or pause motion before reading a stored EEPROM map; live discovery remains available while moving.')
            before=await maze_reply('GET_MAZE_INFO','','robotMaze')
            if not before['bytes']: raise ValueError('No saved maze on robot. Use live discovery to view an unknown maze during learning.')
            payload=bytearray()
            for offset in range(0,before['bytes'],16):
                count=min(16,before['bytes']-offset)
                data=await maze_reply('GET_MAZE_CHUNK',f'{offset},{count}','mazeData')
                chunk=bytes.fromhex(data['hex'])
                if data['offset']!=offset or len(chunk)!=count: raise ValueError('Maze readback offset or size mismatch')
                payload.extend(chunk)
            after=await maze_reply('GET_MAZE_INFO','','robotMaze')
            if before!=after or sum(payload)%65536!=before['checksum']: raise ValueError('Stored maze changed or failed checksum during readback')
            maze=decode_maze(bytes(payload))
            if before['nodes']!=len(maze['graph']['nodes']) or before['segments']!=len(maze['graph']['edges']) or before['version']!=1:
                raise ValueError('Stored maze metadata differs from geometry')
            return {'verified':True,'maze':maze,'storage':before}
        except ValueError as e: raise HTTPException(409,str(e))

@app.post('/maze/upload')
async def upload_maze(m:dict):
    try: payload,details=encode_maze(m)
    except ValueError as e: raise HTTPException(400,str(e))
    async with upload_lock:
        started=False
        try:
            if state['mode'] not in ('IDLE','STOPPED','PATH_READY','ERROR'): raise ValueError('Stop the robot before uploading a maze.')
            await command('MAZE_BEGIN',str(len(payload))); started=True
            for offset in range(0,len(payload),16):
                await command('MAZE_CHUNK',f'{offset},{payload[offset:offset+16].hex()}')
            await command('MAZE_END',str(details['checksum']))
            info=await maze_reply('GET_MAZE_INFO','','robotMaze')
            if info['bytes']!=len(payload) or info['checksum']!=details['checksum'] or info['version']!=1: raise ValueError('Maze metadata readback did not match')
            for offset in range(0,len(payload),16):
                count=min(16,len(payload)-offset)
                chunk=await maze_reply('GET_MAZE_CHUNK',f'{offset},{count}','mazeData')
                if chunk['offset']!=offset or bytes.fromhex(chunk['hex'])!=payload[offset:offset+count]: raise ValueError('Maze byte readback did not match')
            return dict(verified=True,**details)
        except ValueError as e:
            if started:
                try: await command('MAZE_ABORT')
                except ValueError: pass
            raise HTTPException(409,str(e))

@app.post('/maze/import')
async def maze_import(file:UploadFile=File(...),options:str=Form('{}')):
    data=await file.read(16*1024*1024+1)
    if len(data)>16*1024*1024: raise HTTPException(413,'Maximum file size: 16 MB')
    try: return await asyncio.to_thread(import_maze,data,file.filename,json.loads(options))
    except Exception as e: raise HTTPException(400,str(e))
@app.post('/maze/analysis')
async def maze_analysis(m:dict):
    try: return analysis(m)
    except Exception as e: raise HTTPException(400,str(e))
@app.post('/mazes')
async def save_maze(m:dict):
    ident=safe_id(m['id']); (ROOT/'mazes'/f'{ident}.json').write_text(json.dumps(m)); return {'saved':ident}
@app.get('/mazes')
async def mazes():
    result=[]
    for p in (ROOT/'mazes').glob('*.json'):
        try: result.append(json.loads(p.read_text()))
        except Exception: pass
    return result
@app.get('/source/{version}')
async def source(version:str):
    paths={'original':'original/maze.ino','v2':'maze_hc05/maze_hc05.ino','v3':'workshop_robot/workshop_robot.ino'}
    if version not in paths: raise HTTPException(404)
    return PlainTextResponse((Path(os.getenv('FIRMWARE_DIR',str(Path(__file__).resolve().parents[2]/'firmware')))/paths[version]).read_text())
@app.post('/record/start')
async def rec_start():
    global recording,recording_id
    if recording is not None: raise HTTPException(409,'Already recording')
    recording=[]; recording_id=time.strftime('run_%Y%m%d_%H%M%S'); return {'id':recording_id}
@app.post('/record/stop')
async def rec_stop():
    global recording
    if recording is None: raise HTTPException(409,'Not recording')
    (ROOT/'recordings'/f'{recording_id}.json').write_text(json.dumps(recording)); recording=None; return {'id':recording_id}
@app.post('/recordings')
async def rec_save(data:dict):
    ident=time.strftime('sim_%Y%m%d_%H%M%S'); (ROOT/'recordings'/f'{ident}.json').write_text(json.dumps(data.get('frames',[]))); return {'id':ident}
@app.get('/recordings')
async def recordings(): return [p.stem for p in sorted((ROOT/'recordings').glob('*.json'),reverse=True)]
@app.get('/recordings/{ident}')
async def rec_get(ident:str,format:str='json'):
    p=ROOT/'recordings'/f'{safe_id(ident)}.json'
    if not p.exists(): raise HTTPException(404)
    frames=json.loads(p.read_text())
    if format=='csv':
        output=io.StringIO(); keys=['timestamp','mode']+[f'sensor_{i}' for i in range(8)]+['position','error','kp','ki','kd','correction','leftMotor','rightMotor','pathIndex','lastIntersection','command']; writer=csv.DictWriter(output,keys); writer.writeheader()
        for f in frames:
            data=f['data']; s=data.get('state',{}); row={k:s.get(k,'') for k in keys}; row['timestamp']=f['timestamp']
            for i,v in enumerate(s.get('sensors',[])): row[f'sensor_{i}']=v
            if data.get('type')=='log': row['command']=data['entry']['line']
            writer.writerow(row)
        return PlainTextResponse(output.getvalue(),media_type='text/csv')
    return frames
@app.post('/emergency')
async def emergency():
    # Bypass the normal command lock and upload retries: STOP must not wait behind a transfer.
    global next_id
    if not bridge: raise HTTPException(409,'Bridge not connected')
    ident=str(next_id); next_id=(next_id+1)%60000
    line=f'C,{ident},STOP'; await log('TX',line)
    await bridge.send_json({'type':'tx','line':line})
    return {'requested':True,'id':ident}

app.include_router(create_router(upload, PathBody, lambda: state))

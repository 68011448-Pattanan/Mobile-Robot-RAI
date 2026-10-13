"""End-to-end test with an independent backend + serial bridge process, no hardware."""
import os,sys,time,subprocess,pathlib,json
import httpx
from websockets.sync.client import connect
ROOT=pathlib.Path(__file__).resolve().parents[1]
server=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--port','8011'],cwd=ROOT/'backend',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
bridge=None;ui=None
try:
 with httpx.Client(trust_env=False,timeout=15) as c:
  for _ in range(100):
   try:
    if c.get('http://127.0.0.1:8011/health').status_code==200:break
   except httpx.ConnectError:time.sleep(.05)
  ui=connect('ws://127.0.0.1:8011/ws',proxy=None)
  bridge=subprocess.Popen([sys.executable,str(ROOT/'serial-bridge/serial_bridge.py'),'--mock','--url','ws://127.0.0.1:8011/bridge'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  time.sleep(.5)
  def command(name,args=''):
   r=c.post('http://127.0.0.1:8011/command',json={'name':name,'args':args});assert r.status_code==200,(name,r.text);return r.json()
  for name in ('PING','GET_STATUS','GET_SENSORS'):command(name)
  path='LFRB'*25
  r=c.post('http://127.0.0.1:8011/path/upload',json={'text':path});assert r.status_code==200,r.text;assert r.json()['verified']
  maze=json.loads((ROOT/'mazes/external-test.json').read_text());maze['verified']=True
  r=c.post('http://127.0.0.1:8011/maze/upload',json=maze);assert r.status_code==200,r.text;assert r.json()['verified']
  stored=c.get('http://127.0.0.1:8011/maze/robot');assert stored.status_code==200,stored.text
  assert stored.json()['verified'] and len(stored.json()['maze']['graph']['nodes'])>1
  command('GET_MAZE_INFO');command('CLEAR_MAZE')
  command('SET_PID','0.02,0,0.1');command('SET_SPEED','30')
  c.post('http://127.0.0.1:8011/record/start',json={}).raise_for_status()
  command('START_SCAN');time.sleep(1.3)
  live=c.get('http://127.0.0.1:8011/discovery').json()['map']
  assert live['phase']=='LEARNING' and live['rawPath']=='L' and len(live['nodes'])==2 and not live['complete'],live
  assert c.get('http://127.0.0.1:8011/maze/robot').status_code==409
  websocket_live=False
  for _ in range(1000):
   message=json.loads(ui.recv(timeout=3))
   if message['type']=='discovery' and message['map']['rawPath']=='L':websocket_live=True;break
  assert websocket_live,'No mid-run discovery update over WebSocket'
  time.sleep(5.2);command('GET_PATH');command('GET_SHORT_PATH')
  final=c.get('http://127.0.0.1:8011/discovery').json()['map']
  assert final['complete'] and final['phase']=='COMPLETE' and final['rawPath']=='LFBLL',final
  assert not final['distanceMeasured'] and not final['positionMeasured']
  assert any(e['traversals']==2 for e in final['edges'])
  files=c.get('http://127.0.0.1:8011/paths').json();assert any('raw' in p for p in files)
  filename=next(p for p in files if 'raw' in p); assert c.get('http://127.0.0.1:8011/paths/'+filename).text.strip()=='LFBLL'
  command('START_RUN');command('PAUSE');command('RESUME');command('STOP')
  rec=c.post('http://127.0.0.1:8011/record/stop',json={}).json(); assert len(c.get('http://127.0.0.1:8011/recordings/'+rec['id']).json())>10
  assert 'sensor_0' in c.get('http://127.0.0.1:8011/recordings/'+rec['id']+'?format=csv').text
  r=c.post('http://127.0.0.1:8011/path/upload',json={'text':'XX'});assert r.status_code==409
  c.post('http://127.0.0.1:8011/emergency',json={}).raise_for_status()
  command('DISCONNECT');time.sleep(2.6);command('GET_STATUS')
  print('PASS: connect, telemetry, PID/speed, 100-character path checksum/readback, maze checksum/exact byte readback/clear/decode, unknown-maze topology and mid-run WebSocket updates, learning events, TXT save/download, replay, pause/resume, STOP, record/CSV export, invalid path, disconnect/reconnect')
finally:
 if ui:ui.close()
 if bridge:bridge.terminate();bridge.wait(timeout=5)
 server.terminate();server.wait(timeout=5)

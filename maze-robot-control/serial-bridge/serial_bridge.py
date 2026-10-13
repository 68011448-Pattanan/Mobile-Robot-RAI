"""Windows host bridge: identical transport for USB COM and paired HC-05 SPP COM."""
import argparse, asyncio, json, time
import serial
from serial.tools import list_ports
import websockets

class MockRobot:
    def __init__(self):
        self.maze=b''; self.map_pending=bytearray(); self.map_length=0; self.path=''; self.pending=''; self.mode='IDLE'; self.raw=''; self.index=0; self.last=time.monotonic(); self.ids={}; self.running_since=None
    def handle(self,line):
        if line=='HEARTBEAT': return []
        p=line.split(','); ident=p[1]; cmd=p[2]; args=p[3:]
        if ident in self.ids: return self.ids[ident]
        result=[]
        if cmd=='PATH_BEGIN': self.pending=''; self.length=int(args[0])
        elif cmd=='PATH_CHUNK':
            if int(args[0])!=len(self.pending): return [f'ERR,{ident},OFFSET']
            self.pending+=args[1]
        elif cmd=='PATH_END':
            if len(self.pending)!=self.length or sum(map(ord,self.pending))%65536!=int(args[0]) or any(c not in 'LFRB' for c in self.pending): return [f'ERR,{ident},CHECKSUM']
            self.path=self.pending; result+=[f'PATH_STORED,{len(self.path)}',f'PATH_SHORT,{self.path}']
        elif cmd=='MAZE_BEGIN':
            n=int(args[0])
            if self.mode not in ('IDLE','STOPPED','PATH_READY','ERROR') or not 19<=n<=888: return [f'ERR,{ident},INVALID_OR_BUSY']
            self.maze=b''; self.map_length=n; self.map_pending=bytearray()
        elif cmd=='MAZE_CHUNK':
            data=bytes.fromhex(args[1])
            if int(args[0])!=len(self.map_pending) or not 1<=len(data)<=16 or len(self.map_pending)+len(data)>self.map_length: return [f'ERR,{ident},OFFSET']
            self.map_pending.extend(data)
        elif cmd=='MAZE_END':
            if len(self.map_pending)!=self.map_length or sum(self.map_pending)%65536!=int(args[0]): return [f'ERR,{ident},CHECKSUM']
            self.maze=bytes(self.map_pending); self.map_length=0
        elif cmd in ('MAZE_ABORT','CLEAR_MAZE'): self.maze=b''; self.map_length=0
        elif cmd=='GET_MAZE_INFO':
            m=self.maze
            result+=['MAZE_INFO,'+(f'{len(m)},{sum(m)%65536},{m[1]},{m[2]},{m[3]},{m[4]},{int.from_bytes(m[5:7],"little")},{int.from_bytes(m[7:9],"little")},{m[0]}' if m else '0,0,0,0,0,0,0,0,0')]
        elif cmd=='GET_MAZE_CHUNK':
            offset,n=map(int,args)
            if offset<0 or not 1<=n<=16 or offset+n>len(self.maze): return [f'ERR,{ident},RANGE']
            result+=[f'MAZE_DATA,{offset},{self.maze[offset:offset+n].hex()}']
        elif cmd=='GET_SHORT_PATH': result+=[f'PATH_SHORT,{self.path}']
        elif cmd=='GET_PATH': result+=[f'PATH_RAW,{self.raw}']
        elif cmd=='START_SCAN': self.mode='SCAN'; self.raw=''; self.running_since=time.monotonic()
        elif cmd=='START_RUN': self.mode='RUN_PATH'; self.index=0; self.running_since=time.monotonic()
        elif cmd in ('STOP','RESET'): self.mode='STOPPED'; self.running_since=None
        elif cmd=='PAUSE': self.previous=self.mode; self.mode='PAUSED'
        elif cmd=='RESUME': self.mode=getattr(self,'previous','IDLE')
        elif cmd=='DRIVE': self.mode='MANUAL'
        elif cmd=='CLEAR_PATH': self.raw=self.path=''
        elif cmd=='GET_CAL': result+=['CAL,'+','.join(['100']*8+['800']*8)]
        result=[f'ACK,{ident},{cmd}']+result+[f'STATUS,{self.mode},{self.index}']
        self.ids[ident]=result
        if len(self.ids)>16: self.ids.pop(next(iter(self.ids)))
        return result
    def telemetry(self):
        result=[]
        if self.running_since and self.mode=='SCAN':
            elapsed=time.monotonic()-self.running_since; n=min(5,int(elapsed))
            raw='LFBLL'[:n]
            if raw!=self.raw: self.raw=raw; result+=[f'EVENT,JUNCTION,{raw[-1]}',f'PATH_RAW,{raw}']
            if elapsed>6: self.mode='PATH_READY'; self.path='LRL'; self.running_since=None; result+=['EVENT,FINISH',f'PATH_SHORT,{self.path}']
        elif self.running_since and self.mode=='RUN_PATH':
            self.index=min(len(self.path),int(time.monotonic()-self.running_since))
            if self.index==len(self.path): self.mode='PATH_READY'; self.running_since=None
        result+=['SENSOR,100,110,240,790,800,250,110,100','NORM,0,14,200,985,1000,214,14,0',f'CTRL,3500,0,0,0,0,0,{30 if self.mode in ("SCAN","RUN_PATH") else 0},{30 if self.mode in ("SCAN","RUN_PATH") else 0},0.01,0,0.08,{int((time.monotonic()-self.last)*1000)}',f'STATUS,{self.mode},{self.index}']
        return result

async def connect(args):
    while True:
        ser=None
        try:
            if not args.mock:
                ser=serial.serial_for_url(args.port,baudrate=args.baud,timeout=.05,write_timeout=.5); await asyncio.sleep(2)
                ser.reset_input_buffer()
            async with websockets.connect(args.url,max_size=65536,proxy=None) as ws:
                await ws.send(json.dumps({'type':'hello','port':args.port or 'MOCK','baud':args.baud,'transport':args.transport if not args.mock else 'MOCK'}))
                if args.mock: await ws.send(json.dumps({'type':'rx','line':'HELLO,MOCK,1'}))
                print('Connected:',args.url,args.port or 'MOCK')
                mock=MockRobot()
                async def reader():
                    buffer=bytearray()
                    while True:
                        if args.mock:
                            for line in mock.telemetry(): await ws.send(json.dumps({'type':'rx','line':line}))
                            await asyncio.sleep(.2)
                        else:
                            data=await asyncio.to_thread(ser.read,128)
                            for byte in data:
                                if byte==10:
                                    await ws.send(json.dumps({'type':'rx','line':buffer.decode('ascii',errors='replace').strip()})); buffer.clear()
                                elif len(buffer)<512: buffer.append(byte)
                                else: buffer.clear()
                async def writer():
                    async for raw in ws:
                        msg=json.loads(raw)
                        if msg.get('type')!='tx': continue
                        line=msg['line']
                        if args.mock:
                            for reply in mock.handle(line): await ws.send(json.dumps({'type':'rx','line':reply}))
                        else: await asyncio.to_thread(ser.write,(line+'\n').encode('ascii'))
                tasks=[asyncio.create_task(reader()),asyncio.create_task(writer())]
                done,pending=await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
                for task in pending: task.cancel()
                await asyncio.gather(*tasks,return_exceptions=True)
        except Exception as e: print('Connection error:',e,'— retrying in 2 seconds')
        finally:
            if ser: ser.close()
        await asyncio.sleep(2)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--port'); parser.add_argument('--baud',type=int); parser.add_argument('--url',default='ws://127.0.0.1:8000/bridge'); parser.add_argument('--transport',choices=['USB','Bluetooth'],default='USB'); parser.add_argument('--mock',action='store_true'); parser.add_argument('--list',action='store_true'); args=parser.parse_args(); args.baud=args.baud or (115200 if args.transport=='USB' else 9600)
    if args.list:
        for p in list_ports.comports(): print(p.device,p.description)
    elif not args.port and not args.mock: parser.error('Use --port COM5, --mock, or --list')
    else:
        try: asyncio.run(connect(args))
        except KeyboardInterrupt: print('Bridge closed. Firmware stops after heartbeat timeout.')

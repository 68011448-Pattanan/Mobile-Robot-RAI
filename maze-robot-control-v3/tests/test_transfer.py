import importlib.util,pathlib,asyncio,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('bridge',ROOT/'serial-bridge/serial_bridge.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
sys.path.insert(0,str(ROOT/'backend'))
from app import main
from app.core import checksum

def test_checksum_and_offsets():
    robot=b.MockRobot();robot.handle('C,1,PATH_BEGIN,4');assert robot.handle('C,2,PATH_CHUNK,1,LFRB')[0]=='ERR,2,OFFSET';robot.handle('C,3,PATH_CHUNK,0,LFRB');assert robot.handle('C,4,PATH_END,0')[0]=='ERR,4,CHECKSUM';reply=robot.handle('C,5,PATH_END,'+str(checksum('LFRB')));assert 'PATH_SHORT,LFRB' in reply

def test_idempotence():
    robot=b.MockRobot();robot.handle('C,1,PATH_BEGIN,3');r=robot.handle('C,2,PATH_CHUNK,0,LFR');assert robot.handle('C,2,PATH_CHUNK,0,LFR')==r;assert robot.pending=='LFR'

def test_ack_retry(monkeypatch):
    original=asyncio.wait_for
    async def fast_wait(future,timeout):return await original(future,.02)
    monkeypatch.setattr(main.asyncio,'wait_for',fast_wait)
    class Fake:
        def __init__(self,drop):self.calls=0;self.drop=drop
        async def send_json(self,data):
            self.calls+=1
            if self.calls>self.drop:
                ident=data['line'].split(',')[1]
                await main.receive('ACK,'+ident+',PING')
    async def run():
        main.connected=True;fake=Fake(1);main.bridge=fake
        result=await main.command('PING');assert result==['PING'];assert fake.calls==2
        fake=Fake(99);main.bridge=fake
        try:await main.command('PING')
        except ValueError as e:assert 'timeout' in str(e)
        else:assert False
        assert fake.calls==3;main.bridge=None;main.connected=False
    asyncio.run(run())

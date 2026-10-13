import asyncio, copy, struct
import pytest
from fastapi import HTTPException
from app import main
from app.robot_maze import encode_maze
from app.core import parse_packet, empty_state
from test_transfer import b

def sample():
    return dict(verified=True,scale=2,lineWidth=6,heading=-90,start='S',finish='F',graph=dict(nodes=[dict(id='S',x=0,y=0),dict(id='F',x=20,y=0)],edges=[dict(a='S',b='F',points=[dict(x=0,y=0),dict(x=10,y=5),dict(x=20,y=0)])]))

def test_geometry_and_units():
    data,info=encode_maze(sample())
    assert struct.unpack('<BBBBBhH',data[:9])==(1,3,2,0,1,2700,12)
    assert struct.unpack('<hhhhhh',data[9:21])==(0,0,40,0,20,10)
    assert data[21:]==bytes([0,2,2,1])
    assert info['bytes']==25 and info['checksum']==sum(data)%65536

@pytest.mark.parametrize('change',[{'verified':False},{'scale':0},{'scale':float('nan')},{'lineWidth':0},{'start':'F'},{'finish':'missing'}])
def test_invalid_metadata(change):
    m=sample();m.update(change)
    with pytest.raises(ValueError):encode_maze(m)

def test_limits_and_disconnected():
    m=sample();m['graph']['edges'][0]['points'][1:1]=[dict(x=i,y=2) for i in range(63)]
    with pytest.raises(ValueError,match='capacity'):encode_maze(m)
    m=sample();m['graph']['nodes'].append(dict(id='X',x=1,y=3))
    with pytest.raises(ValueError,match='connected'):encode_maze(m)
    m=sample();m['graph']['nodes'][1]['x']=50000
    with pytest.raises(ValueError,match='coordinates'):encode_maze(m)

def test_upload_exact_readback_and_failure(monkeypatch):
    class Fake:
        def __init__(self,corrupt=False):self.robot=b.MockRobot();self.corrupt=corrupt
        async def send_json(self,data):
            for reply in self.robot.handle(data['line']):
                if self.corrupt and reply.startswith('MAZE_DATA,0,'):reply=reply[:-2]+'ff'
                await main.receive(reply)
    async def run():
        main.command_lock=asyncio.Lock();main.upload_lock=asyncio.Lock()
        main.bridge=Fake();main.connected=True;main.state=empty_state()
        result=await main.upload_maze(sample())
        assert result['verified'] and main.bridge.robot.maze==encode_maze(sample())[0]
        main.bridge=Fake(True)
        with pytest.raises(HTTPException) as exc:await main.upload_maze(sample())
        assert 'readback' in exc.value.detail and main.bridge.robot.maze==b''
        main.state['mode']='PAUSED'
        with pytest.raises(HTTPException) as exc:await main.upload_maze(sample())
        assert 'Stop' in exc.value.detail
        main.bridge=None;main.connected=False;main.state=empty_state()
    asyncio.run(run())

def test_packet_validation():
    for packet in ['MAZE_INFO,889,0,2,1,0,1,0,12,1','MAZE_DATA,0,xx','MAZE_DATA,-1,aa','MAZE_DATA,0,a']:
        with pytest.raises(ValueError):parse_packet(packet,empty_state())

def test_mock_offsets_checksum_and_duplicates():
    robot=b.MockRobot();data,info=encode_maze(sample())
    robot.handle(f'C,1,MAZE_BEGIN,{len(data)}')
    assert robot.handle('C,2,MAZE_CHUNK,1,ff')[0].startswith('ERR')
    reply=robot.handle('C,3,MAZE_CHUNK,0,'+data[:16].hex())
    assert robot.handle('C,3,MAZE_CHUNK,0,'+data[:16].hex())==reply
    robot.handle('C,4,MAZE_CHUNK,16,'+data[16:].hex())
    assert robot.handle('C,5,MAZE_END,0')[0].startswith('ERR')
    assert robot.handle(f'C,6,MAZE_END,{info["checksum"]}')[0].startswith('ACK')
    assert robot.maze==data

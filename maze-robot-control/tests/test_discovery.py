import asyncio, copy, pathlib, sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'backend'))
import pytest
from app.discovery import DiscoveryMap
from app import main
from app.core import empty_state
from app.robot_maze import encode_maze,decode_maze
from fastapi import HTTPException
from test_robot_maze import sample
from test_transfer import b


def learning():
    d=DiscoveryMap();d.reset();d.status('SCAN');return d


def test_unknown_maze_and_backtrack():
    d=learning();assert len(d.nodes)==1 and d.raw==''
    d.path('L');assert len(d.nodes)==2 and d.current=='N1'
    d.path('LB');assert len(d.nodes)==3 and d.current=='N2'
    d.path('LBL');assert len(d.nodes)==3 and len(d.edges)==2 and d.current=='N1'
    assert d.edges[1]['traversals']==2 and d.nodes[2]['kind']=='dead-end report'
    d.finish();s=d.snapshot()
    assert s['complete'] and s['phase']=='COMPLETE' and len(s['nodes'])==4
    assert s['nodes'][-1]['kind']=='finish' and all(e['length'] is None for e in s['edges'])
    assert not s['positionMeasured'] and not s['distanceMeasured'] and s['units']=='schematic'
    assert not d.finish()


def test_duplicate_history_and_reconnect():
    d=learning();d.path('L');session=d.session
    assert not d.path('L');d.path('LBLF')
    assert d.raw=='LBLF' and len(d.observations)==4 and d.session==session
    # Diverging or shortened path must begin a new inference, not splice old maps.
    d.path('R');assert d.session!=session and len(d.observations)==1
    d.path('');assert d.raw=='' and len(d.nodes)==1
    d=DiscoveryMap();d.path('LBL');assert d.phase=='HISTORY' and d.current=='N1'


def test_loop_is_never_invented_by_coordinate_coincidence():
    d=learning();d.path('LLLL')
    assert len(d.nodes)==5 and len(d.edges)==4 and d.current!='N0'
    assert 'Loops' in d.warnings[1]


def test_pause_stop_and_error():
    d=learning();d.path('L');count=len(d.nodes)
    d.status('PAUSED');assert d.phase=='PAUSED'
    d.status('SCAN');assert d.phase=='LEARNING'
    d.status('STOPPED');assert d.phase=='STOPPED' and len(d.nodes)==count
    d.status('ERROR');d.gap('Turn failed');assert d.phase=='ERROR' and 'Turn failed' in d.warnings


def test_finish_without_a_turn():
    d=learning();d.finish();assert len(d.nodes)==2 and len(d.edges)==1 and d.complete


def test_stored_map_roundtrip_and_reject_corruption():
    data,_=encode_maze(sample());m=decode_maze(data)
    assert encode_maze(m)[0]==data and m['heading']==270 and m['scale']==1
    for bad in (b'',bytes([2])+data[1:],data[:-1],data[:-1]+b'\xff'):
        with pytest.raises(ValueError):decode_maze(bad)
    m=sample();m['graph']['nodes'][0]['x']=-200;m['graph']['edges'][0]['points'][0]['x']=-200
    payload,_=encode_maze(m);assert encode_maze(decode_maze(payload))[0]==payload


def test_live_broadcast_and_packet_recovery(monkeypatch,tmp_path):
    messages=[]
    class Client:
        async def send_json(self,message):messages.append(copy.deepcopy(message))
    async def run():
        main.discovery=DiscoveryMap();main.last_scan_ack=None;main.clients={Client()};main.previous_sequence=None
        main.state=empty_state();main.connected=False
        await main.receive('EVENT')
        await main.receive('ACK,501,START_SCAN');await main.receive('STATUS,SCAN,0,0')
        await main.receive('PATH_RAW,L');await main.receive('PATH_RAW,L')
        assert main.discovery.raw=='L' and len(main.discovery.observations)==1
        # A missed intermediate raw packet is recovered from the cumulative prefix.
        await main.receive('PATH_RAW,LBL');assert main.discovery.current=='N1'
        await main.receive('STATUS,SCAN,0,3')
        assert any('gap' in w for w in main.discovery.warnings)
        updates=[m['map'] for m in messages if m['type']=='discovery']
        assert any(m['rawPath']=='L' and not m['complete'] for m in updates)
        assert any(m['rawPath']=='LBL' for m in updates)
        await main.receive('ACK,501,START_SCAN');assert main.discovery.raw=='LBL'
        await main.receive('STATUS,PATH_READY,0,4');await main.receive('EVENT,FINISH')
        assert main.discovery.complete and main.discovery.phase=='COMPLETE'
        count=len(main.discovery.nodes)
        await main.receive('ACK,502,START_RUN');await main.receive('EVENT,FINISH')
        assert len(main.discovery.nodes)==count
        snapshot=await main.discovered_map();assert snapshot['map']['rawPath']=='LBL'
        main.clients=set();main.discovery=DiscoveryMap();main.state=empty_state();main.connected=False;main.last_scan_ack=None
    (tmp_path/'paths').mkdir();monkeypatch.setattr(main,'ROOT',tmp_path)
    asyncio.run(run())


def test_read_robot_map_is_verified_and_non_destructive(monkeypatch):
    class Fake:
        def __init__(self):self.robot=b.MockRobot();self.commands=[]
        async def send_json(self,data):
            self.commands.append(data['line'].split(',')[2])
            for reply in self.robot.handle(data['line']):await main.receive(reply)
    async def run():
        main.command_lock=asyncio.Lock();main.upload_lock=asyncio.Lock();main.bridge=Fake();main.connected=True;main.state=empty_state()
        with pytest.raises(HTTPException) as exc:await main.read_robot_maze()
        assert 'No saved maze' in exc.value.detail
        data,_=encode_maze(sample());main.bridge.robot.maze=data
        result=await main.read_robot_maze();assert result['verified'] and encode_maze(result['maze'])[0]==data
        assert all(c.startswith('GET_') for c in main.bridge.commands) and main.bridge.robot.maze==data
        main.state['mode']='SCAN'
        with pytest.raises(HTTPException) as exc:await main.read_robot_maze()
        assert 'live discovery' in exc.value.detail
        main.bridge=None;main.connected=False;main.discovery=DiscoveryMap();main.state=empty_state()
    asyncio.run(run())


def test_demo_fixture_matches_inference():
    import json,pathlib
    frames=json.loads((pathlib.Path(__file__).resolve().parents[1]/'frontend/lib/discovery-demo.json').read_text())
    d=learning()
    for raw,frame in zip(('L','LB','LBL','LBLF'),frames[1:-1]):
        d.path(raw);s=d.snapshot()
        assert frame['nodes']==s['nodes'] and frame['edges']==s['edges'] and frame['currentNode']==s['currentNode']
        assert frame['positionMeasured'] is False and frame['distanceMeasured'] is False
    d.finish();assert frames[-1]['nodes']==d.snapshot()['nodes'] and frames[-1]['phase']=='COMPLETE'

import sys, pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'backend'))
import pytest
from app.core import *
@pytest.mark.parametrize('raw,expected',[('LBL','F'),('LBF','R'),('LBR','B'),('FBL','R'),('FBF','B'),('FBR','L'),('RBL','B'),('RBF','L'),('RBR','F')])
def test_rules(raw,expected): assert optimize(raw)[0]==expected
@pytest.mark.parametrize('path',['LXRF','1234','LEFT-RIGHT','L'*101,'','L\x00F'])
def test_invalid(path):
    with pytest.raises(ValueError):validate_path(path)
def test_metadata(): assert validate_path('# Saved route\nL F R B\n')=='LFRB'
def test_cascade(): assert optimize('LBLBL')[0]=='R'
def test_parser():
    s=parse_packet('SENSOR,100,200,300,400,500,600,700,800',empty_state()); assert s['sensors'][7]==800
    s=parse_packet('CTRL,3501,1,0.1,0,0.2,0.3,30,29,0.01,0,0.08,100',s); assert s['position']==3501
@pytest.mark.parametrize('packet',['SENSOR,1,2','SENSOR,nan,0,0,0,0,0,0,0','SENSOR,1024,0,0,0,0,0,0,0','PATH_RAW,LX','STATUS,BAD,1','WHAT,3'])
def test_malformed(packet):
    with pytest.raises((ValueError,TypeError)):parse_packet(packet,empty_state())
def test_config():
    s=parse_packet('CONFIG,3,32,460,1,10',empty_state()); assert s['controller']=='PID';assert s['threshold']==460;assert s['background']==1

def test_status_sequence():
    s=parse_packet('STATUS,SCAN,4,65535',empty_state());assert s['sequence']==65535;assert s['pathIndex']==4

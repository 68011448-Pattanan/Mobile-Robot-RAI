import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'backend'))
from fastapi.testclient import TestClient
from app.main import app

def test_endpoints():
    with TestClient(app) as c:
        assert c.get('/health').json()['ok']
        assert c.post('/path/optimize',json={'text':'LBL'}).json()['optimized']=='F'
        assert c.post('/path/optimize',json={'text':'XX'}).status_code==400
        assert c.post('/command',json={'name':'STOP'}).status_code==409
        assert 'TrackMaze' in c.get('/source/original').text
        r=c.post('/maze/import',files={'file':('new.csv',b'1,1,1,1\n1,S,F,1\n1,1,1,1','text/csv')});assert r.status_code==200
        m=r.json();assert c.post('/maze/analysis',json=m).json()['components']==1

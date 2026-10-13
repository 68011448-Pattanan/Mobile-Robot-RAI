import asyncio
import json
from pathlib import Path
import sys
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app import workshop as w


def blank():
    return w.FIRMWARE.read_text(encoding='utf-8')


def completed():
    source = blank()
    first = source.index(w.BEGIN) + len(w.BEGIN)
    last = source.index(w.END)
    answer = (w.ASSETS / 'instructor/solution.cpp').read_text(encoding='utf-8')
    return source[:first] + '\n' + answer + source[last:]


def test_scaffold_and_subset():
    w.exercise(blank())
    w.exercise(completed())
    with pytest.raises(ValueError, match='scaffold'):
        w.exercise(completed().replace('baseSpeed = 30', 'baseSpeed = 99'))
    with pytest.raises(ValueError, match='workshop subset'):
        w.exercise(completed().replace("if (left) return 'L';", 'system(0);'))
    with pytest.raises(ValueError):
        w.exercise(completed().replace("if (left) return 'L';", '#include <fstream>'))


def test_native_compilation_and_simulation():
    starter = w.compile_sketch(blank())
    assert not starter['checks']['lsrb']
    assert not any(starter['checks']['motors'].values())
    correct = w.compile_sketch(completed())
    assert correct['checks']['lsrb'] and all(correct['checks']['motors'].values())
    maze = json.loads((w.ASSETS / 'field.json').read_text(encoding='utf-8'))
    run = w.simulate(correct, maze)
    assert run['passed']
    assert run['raw'] == 'LBLF' and run['path'] == 'FF'
    assert {f['stage'] for f in run['frames']} == {'Learning', 'Replay'}
    assert any(f['state']['leftMotor'] < 0 for f in run['frames'])
    wrong_order = completed().replace("if (left) return 'L';\n  if (straight) return 'F';", "if (straight) return 'F';\n  if (left) return 'L';")
    wrong = w.compile_sketch(wrong_order)
    assert not wrong['checks']['lsrb']
    assert w.simulate(wrong, maze)['raw'] != run['raw']
    wrong_motor = completed().replace("movement == 'L') return {-speed, speed}", "movement == 'L') return {speed, -speed}")
    incorrect = w.compile_sketch(wrong_motor)
    assert not incorrect['checks']['motors']['L']
    assert not w.simulate(incorrect, maze)['passed']
    assert not w.simulate(starter, maze)['passed']
    with pytest.raises(ValueError):
        w.compile_sketch(completed().replace('return {-speed, speed};', 'return {speed*2, speed};'))
    with pytest.raises(ValueError, match='workshop_robot.ino'):
        w.compile_sketch(completed().replace("return 'L';", "return 'L'"))


@pytest.mark.parametrize('newline,bom', [('\r\n', ''), ('\r\n', '\ufeff'), ('\r', ''), ('\n', '\ufeff')])
def test_uploaded_sketch_encoding(newline, bom):
    source = completed()
    uploaded = bom + source.replace('\n', newline)
    assert w.exercise(uploaded) == w.exercise(source)
    assert w.compile_sketch(uploaded) == w.compile_sketch(source)
    with pytest.raises(ValueError, match='scaffold'):
        w.exercise(uploaded.replace('baseSpeed = 30', 'baseSpeed = 99'))


def test_certificate_export_transfer_and_winner(monkeypatch):
    from pydantic import BaseModel
    class PathBody(BaseModel):
        text: str
    uploads = []
    state = {'mode': 'IDLE'}
    async def upload(body):
        uploads.append(body.text)
        return {'verified': True, 'path': body.text}
    with tempfile.TemporaryDirectory() as directory:
        monkeypatch.setenv('DATA_DIR', directory)
        app = FastAPI()
        app.include_router(w.create_router(upload, PathBody, lambda: state))
        with TestClient(app) as client:
            assert client.post('/workshop/export', json={'certificate': 'invented'}).status_code == 409
            denied = client.post('/workshop/simulate', json={'source': completed(), 'fieldConfirmed': False}).json()
            assert not denied['passed'] and denied['certificate'] is None
            uploaded = '\ufeff' + completed().replace('\n', '\r\n')
            compiled = client.post('/workshop/compile', json={'source': uploaded})
            assert compiled.status_code == 200
            assert compiled.json()['checks']['lsrb']
            approved = client.post('/workshop/simulate', json={'source': uploaded, 'fieldConfirmed': True}).json()
            assert approved['passed']
            token = approved['certificate']
            exported = client.post('/workshop/export', json={'certificate': token}).text
            assert 'const char WORKSHOP_REPLAY[] = "FF";' in exported
            assert '\r' not in exported and not exported.startswith('\ufeff')
            assert w.compile_sketch(exported)['checks']['lsrb']
            state['mode'] = 'SCAN'
            assert client.post('/workshop/upload', json={'certificate': token}).status_code == 409
            state['mode'] = 'STOPPED'
            assert client.post('/workshop/upload', json={'certificate': token}).json()['verified']
            assert uploads == ['FF']
            body = {'certificate': token, 'group': 'Group 1', 'physicalFinishConfirmed': False}
            assert client.post('/workshop/results', json=body).status_code == 400
            body['physicalFinishConfirmed'] = True
            assert client.post('/workshop/results', json=body).json()['winner'] == 'Group 1'
            assert client.post('/workshop/results', json=body).status_code == 409
            body['group'] = 'Group 2'
            rows = client.post('/workshop/results', json=body).json()
            assert rows['winner'] == 'Group 1' and rows['results'][1]['place'] == 2
            assert client.get('/workshop/results').json() == rows
            assert '<svg' in client.get('/workshop/field.svg').text
            cert = w.certificates[token]
            cert['mazeHash'] = 'old field'
            assert client.post('/workshop/export', json={'certificate': token}).status_code == 409
            cert['mazeHash'] = w.digest(json.loads((w.ASSETS/'field.json').read_text(encoding='utf-8')))
            cert['time'] -= 7*3600
            assert client.post('/workshop/export', json={'certificate': token}).status_code == 409

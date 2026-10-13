"""Day 2 workshop: compile the shared Arduino exercises and certify a run."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
FIRMWARE = Path(os.getenv('WORKSHOP_FIRMWARE', str(ROOT / 'firmware/workshop_robot/workshop_robot.ino')))
ASSETS = Path(os.getenv('WORKSHOP_ASSETS', str(ROOT / 'workshop')))
BEGIN = '// BEGIN STUDENT EXERCISES'
END = '// END STUDENT EXERCISES'
REPLAY = re.compile(r'const char WORKSHOP_REPLAY\[\] = "[LFRB]*";')
certificates = {}
cache = {}
compile_lock = asyncio.Lock()
result_lock = asyncio.Lock()


def digest(value):
    if not isinstance(value, str):
        value = json.dumps(value, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(value.encode()).hexdigest()


def normalize_source(source):
    # File uploads retain Windows newlines and may include a UTF-8 BOM.
    # These encoding differences do not change the supplied Arduino scaffold.
    return source.removeprefix('\ufeff').replace('\r\n', '\n').replace('\r', '\n')


def exercise(source):
    source = normalize_source(source)
    if len(source.encode()) > 100_000 or source.count(BEGIN) != 1 or source.count(END) != 1:
        raise ValueError('Keep exactly one student exercise block in the workshop sketch.')
    first = source.index(BEGIN) + len(BEGIN)
    last = source.index(END)
    if last <= first or len(REPLAY.findall(source)) != 1:
        raise ValueError('Invalid workshop sketch structure.')
    scaffold = source[:first] + '\n' + source[last:]
    scaffold = REPLAY.sub('const char WORKSHOP_REPLAY[] = "";', scaffold)
    if digest(scaffold) != (ASSETS / 'scaffold.sha256').read_text(encoding='utf-8').strip():
        raise ValueError('Edit only the marked student exercises. The supplied Arduino scaffold must stay intact.')
    code = source[first:last]
    # This educational subset excludes libraries, macros and host I/O. It still
    # executes actual compiled C++, including incorrect student condition order.
    clean = re.sub(r'/\*.*?\*/|//[^\n]*', '', code, flags=re.S)
    tokens = re.findall(r"'[LFRB?]'|[A-Za-z_][A-Za-z_0-9]*|[0-9]+|==|!=|<=|>=|&&|\|\||[{}();,+*/%?:!<>=&|\-]", clean)
    if re.sub(r'\s+', '', clean) != ''.join(tokens):
        raise ValueError('Use integer motor expressions and if/else/return logic in the exercise block.')
    allowed = {'MotorPair', 'studentMotors', 'studentChoose', 'movement', 'speed', 'left', 'straight', 'right',
               'int', 'char', 'bool', 'if', 'else', 'return', 'true', 'false', 'const'}
    if any(t[0].isalpha() and t not in allowed for t in tokens):
        raise ValueError('The workshop subset supports the supplied names, integer expressions and if/else/return; no extra functions or libraries.')
    return code, source[:first].count('\n') + 1


def compile_sketch(source):
    source = normalize_source(source)
    code, line = exercise(source)
    key = digest(source)
    if key in cache:
        return cache[key]
    compiler = os.getenv('CXX', 'g++')
    if not shutil.which(compiler):
        raise ValueError('C++ compiler unavailable. Start version 3 with Docker Compose, which includes g++.')
    runner = '''
#include <iostream>
struct MotorPair { int left; int right; };
'''+f'#line {line} "workshop_robot.ino"\n'+code+'''
#line 1 "workshop_runner.cpp"
int main() {
  for (int mask=0; mask<8; ++mask)
    std::cout << "C " << mask << " " << studentChoose(mask&4, mask&2, mask&1) << "\\n";
  for (int speed=1; speed<=100; ++speed)
    for (char turn : {'F','L','R','B'}) {
      MotorPair m = studentMotors(turn, speed);
      std::cout << "M " << turn << " " << speed << " " << m.left << " " << m.right << "\\n";
    }
}
'''
    try:
        with tempfile.TemporaryDirectory(prefix='maze-workshop-') as temp:
            cpp = Path(temp) / 'exercise.cpp'
            exe = Path(temp) / ('exercise.exe' if os.name == 'nt' else 'exercise')
            cpp.write_text(runner, encoding='utf-8')
            built = subprocess.run([compiler, '-std=c++17', '-O0', '-Wall', '-Wextra', '-Werror=return-type',
                                    str(cpp), '-o', str(exe)], capture_output=True, text=True, timeout=15)
            if built.returncode:
                raise ValueError(built.stderr[-6000:])
            ran = subprocess.run([str(exe)], capture_output=True, text=True, timeout=2)
            if ran.returncode:
                raise ValueError('The student functions failed while running. Check their return values.')
    except subprocess.TimeoutExpired:
        raise ValueError('The student code exceeded the compile/run time limit.')
    choices = ['?'] * 8
    motors = {turn: [[0, 0] for _ in range(101)] for turn in 'FLRB'}
    rows = ran.stdout.splitlines()
    if len(rows) != 408:
        raise ValueError('Student functions did not produce the expected outputs.')
    for row in rows:
        fields = row.split()
        if fields[0] == 'C':
            choices[int(fields[1])] = fields[2]
        else:
            turn, speed, left, right = fields[1], *map(int, fields[2:])
            if not (-100 <= left <= 100 and -100 <= right <= 100):
                raise ValueError('Motor commands must stay between -100 and 100 for every speed from 1 to 100.')
            motors[turn][speed] = [left, right]
    expected = ['B', 'R', 'F', 'F', 'L', 'L', 'L', 'L']
    directions = {'F': (1, 1), 'L': (-1, 1), 'R': (1, -1), 'B': (1, -1)}
    motor_checks = {t: all(motors[t][s] == [a*s, b*s] for s in range(1, 101))
                    for t, (a, b) in directions.items()}
    result = {'sourceHash': key, 'choices': choices, 'motors': motors,
              'checks': {'lsrb': choices == expected, 'motors': motor_checks},
              'diagnostics': built.stderr.strip()}
    if len(cache) >= 64:
        cache.pop(next(iter(cache)))
    cache[key] = result
    return result


def simulate(profile, maze):
    node = os.getenv('NODE', 'node')
    if not shutil.which(node):
        raise ValueError('Node.js unavailable. Start version 3 with Docker Compose.')
    try:
        ran = subprocess.run([node, str(ASSETS / 'run-simulation.cjs')], input=json.dumps({'profile': profile, 'maze': maze}),
                             capture_output=True, text=True, timeout=20)
    except subprocess.TimeoutExpired:
        raise ValueError('Simulation exceeded its time limit.')
    if ran.returncode:
        raise ValueError('Simulation failed: ' + ran.stderr[-1500:])
    return json.loads(ran.stdout)


def field_svg(maze):
    # Field JSON is instructor-owned, never arbitrary student markup.
    scale = maze['scale']
    lines = []
    for edge in maze['graph']['edges']:
        pts = ' '.join(f"{p['x']},{p['y']}" for p in edge['points'])
        lines.append(f'<polyline points="{pts}" fill="none" stroke="black" stroke-width="{maze["lineWidth"]}" stroke-linecap="round" stroke-linejoin="round"/>')
    nodes = {n['id']: n for n in maze['graph']['nodes']}
    start, finish = nodes[maze['start']], nodes[maze['finish']]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{maze['width']*scale}mm" height="{maze['height']*scale}mm" viewBox="0 0 {maze['width']} {maze['height']}">
<rect width="100%" height="100%" fill="white"/>{''.join(lines)}
<rect x="{finish['x']-25/scale}" y="{finish['y']-30/scale}" width="{50/scale}" height="{60/scale}" fill="black"/>
<text x="{start['x']-25/scale}" y="{start['y']+45/scale}" font-size="{10/scale}">START</text>
<text x="{finish['x']-25/scale}" y="{finish['y']+45/scale}" font-size="{10/scale}">FINISH</text>
</svg>'''


class SketchBody(BaseModel):
    source: str = Field(max_length=100_000)


class RunBody(SketchBody):
    fieldConfirmed: bool = False


class CertificateBody(BaseModel):
    certificate: str


class ResultBody(CertificateBody):
    group: str = Field(min_length=1, max_length=60)
    physicalFinishConfirmed: bool = False


def create_router(upload_path, path_body, state_getter):
    router = APIRouter(prefix='/workshop')

    def maze_now():
        return json.loads((ASSETS / 'field.json').read_text(encoding='utf-8'))

    def certificate_now(token):
        cert = certificates.get(token)
        if not cert or time.time() - cert['time'] > 6*3600:
            raise HTTPException(409, 'Run and pass the workshop simulation again to obtain a current certificate.')
        if cert['mazeHash'] != digest(maze_now()):
            raise HTTPException(409, 'The instructor changed the field. Run the simulation again.')
        return cert

    @router.get('/setup')
    async def setup():
        maze = maze_now()
        return {'source': FIRMWARE.read_text(encoding='utf-8'), 'maze': maze, 'mazeHash': digest(maze),
                'filename': 'workshop_robot.ino', 'durationMinutes': 180}

    @router.get('/field.svg')
    async def field():
        return PlainTextResponse(field_svg(maze_now()), media_type='image/svg+xml')

    @router.post('/compile')
    async def compile_route(body: SketchBody):
        try:
            async with compile_lock:
                return await asyncio.to_thread(compile_sketch, body.source)
        except ValueError as error:
            raise HTTPException(400, str(error))

    @router.post('/simulate')
    async def run(body: RunBody):
        try:
            async with compile_lock:
                profile = await asyncio.to_thread(compile_sketch, body.source)
                maze = maze_now()
                result = await asyncio.to_thread(simulate, profile, maze)
            passed = result['passed'] and profile['checks']['lsrb'] and all(profile['checks']['motors'].values()) and body.fieldConfirmed
            token = uuid.uuid4().hex if passed else None
            if token:
                if len(certificates) >= 100:
                    certificates.pop(next(iter(certificates)))
                certificates[token] = {'source': normalize_source(body.source), 'sourceHash': profile['sourceHash'], 'mazeHash': digest(maze),
                                       'path': result['path'], 'time': time.time()}
            return {**result, 'passed': passed, 'certificate': token, 'profile': profile,
                    'fieldConfirmed': body.fieldConfirmed, 'mazeHash': digest(maze)}
        except ValueError as error:
            raise HTTPException(400, str(error))

    @router.post('/export')
    async def export(body: CertificateBody):
        cert = certificate_now(body.certificate)
        source = REPLAY.sub(f'const char WORKSHOP_REPLAY[] = "{cert["path"]}";', cert['source'])
        return PlainTextResponse(source, headers={'Content-Disposition': 'attachment; filename="workshop_robot.ino"'})

    @router.post('/upload')
    async def upload(body: CertificateBody):
        cert = certificate_now(body.certificate)
        if state_getter()['mode'] not in ('IDLE', 'STOPPED', 'PATH_READY', 'ERROR'):
            raise HTTPException(409, 'Stop the real robot before transferring a workshop path.')
        return await upload_path(path_body(text=cert['path']))

    results_file = Path(os.getenv('DATA_DIR', str(ROOT))) / 'workshop-results.json'

    def results_now():
        rows = json.loads(results_file.read_text(encoding='utf-8')) if results_file.exists() else []
        return {'results': rows, 'winner': rows[0]['group'] if rows else None}

    @router.get('/results')
    async def results():
        return results_now()

    @router.post('/results')
    async def record(body: ResultBody):
        cert = certificate_now(body.certificate)
        if not body.physicalFinishConfirmed:
            raise HTTPException(400, 'The instructor must observe and confirm the physical finish.')
        group = body.group.strip()
        if not group:
            raise HTTPException(400, 'Enter the group name.')
        async with result_lock:
            current = results_now()
            if any(r['group'].casefold() == group.casefold() for r in current['results']):
                raise HTTPException(409, 'This group already has a confirmed finish.')
            current['results'].append({'group': group, 'place': len(current['results'])+1,
                                       'confirmedAt': time.time(), 'sourceHash': cert['sourceHash'],
                                       'mazeHash': cert['mazeHash'], 'path': cert['path']})
            temporary = results_file.with_suffix('.tmp')
            temporary.write_text(json.dumps(current['results'], indent=2))
            temporary.replace(results_file)
            return results_now()

    return router

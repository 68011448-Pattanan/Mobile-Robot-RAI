"""Check examples through the running version 3 compiler and simulator API."""
import argparse
import json
from pathlib import Path
import urllib.error
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:8003')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1] / 'workshop/student-examples'

expected = {
    '00_complete': (True, True, True, True, 'LBLF', 'FF'),
    '01_blank': (True, False, False, False, '', ''),
    '02_motors_only': (True, False, True, False, '', ''),
    '03_lsrb_only': (True, True, False, False, '', ''),
    '04_missing_left_motor': (True, True, False, False, None, None),
    '05_missing_back_logic': (True, False, True, False, None, None),
    '06_missing_right_logic': (True, False, True, True, 'LBLF', 'FF'),
    '07_wrong_priority': (True, False, True, True, 'FF', 'FF'),
    '08_wrong_left_motor': (True, True, False, False, None, None),
    '09_syntax_error': (False, None, None, None, None, None),
}

def post(path, data):
    request = urllib.request.Request(args.url+path, data=json.dumps(data).encode(), headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)

rows = []
for folder in sorted(p for p in root.iterdir() if p.is_dir()):
    # Match browser File.text(): preserve the uploaded file's original newlines.
    source = (folder/'workshop_robot/workshop_robot.ino').read_bytes().decode('utf-8')
    status, profile = post('/workshop/compile', {'source':source})
    row = {'case':folder.name, 'compiled':status==200}
    want = expected[folder.name]
    assert row['compiled'] == want[0], (folder.name, profile)
    if status != 200:
        row['diagnostic'] = profile['detail']
    else:
        status, run = post('/workshop/simulate', {'source':source, 'fieldConfirmed':False})
        assert status == 200, (folder.name, run)
        # No certificates or physical finishes are created by these examples.
        assert run['certificate'] is None and not run['passed']
        learning = [f for f in run['frames'] if f['stage']=='Learning']
        replay = [f for f in run['frames'] if f['stage']=='Replay']
        row.update(lsrbChecks=profile['checks']['lsrb'], motorChecks=profile['checks']['motors'],
                   learningFinished=learning[-1]['state']['mode']=='PATH_READY',
                   replayFinished=bool(replay) and replay[-1]['state']['mode']=='PATH_READY',
                   raw=run['raw'], reduced=run['path'], reason=run['reason'])
        row['eligibleWithFieldConfirmation'] = row['lsrbChecks'] and all(row['motorChecks'].values()) and row['learningFinished'] and row['replayFinished']
        actual = (row['compiled'], row['lsrbChecks'], all(row['motorChecks'].values()), row['learningFinished'] and row['replayFinished'], row['raw'], row['reduced'])
        assert all(w is None or a==w for a,w in zip(actual,want)), (folder.name,actual,want)
    rows.append(row)
    print(folder.name+': '+('compile error (intentional)' if not row['compiled'] else row['reason']), flush=True)

(root/'verification.json').write_text(json.dumps(rows,indent=2)+'\n', encoding='utf-8')
print('PASS: all 10 examples produce their expected compiler and simulation outcomes.')

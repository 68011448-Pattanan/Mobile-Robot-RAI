"""Compile the completed/exported student sketch without flashing hardware."""
import argparse
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--cli', default='arduino-cli')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
source = (root/'firmware/workshop_robot/workshop_robot.ino').read_text(encoding='utf-8')
first = source.index('// BEGIN STUDENT EXERCISES')+len('// BEGIN STUDENT EXERCISES')
last = source.index('// END STUDENT EXERCISES')
answer = (root/'workshop/instructor/solution.cpp').read_text(encoding='utf-8')
source = source[:first]+'\n'+answer+source[last:]
with tempfile.TemporaryDirectory(prefix='maze-v3-uno-') as directory:
    folder=Path(directory)/'workshop_robot'
    folder.mkdir()
    for label, sketch in [('Completed exercise', source), ('Exported FF path', source.replace('WORKSHOP_REPLAY[] = ""', 'WORKSHOP_REPLAY[] = "FF"'))]:
        (folder/'workshop_robot.ino').write_text(sketch)
        print(label, flush=True)
        subprocess.run([args.cli,'compile','--fqbn','arduino:avr:uno','--build-path',str(Path(directory)/'build'),str(folder)],check=True)

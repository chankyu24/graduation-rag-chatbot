"""Run reproducible tests and a real HTTP server smoke test."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

parser=argparse.ArgumentParser()
parser.add_argument('--embedding',action='store_true',help='download/load multilingual model')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
env=os.environ.copy()
env['PYTHONUTF8']='1'
if args.embedding: env['RUN_EMBEDDING_TEST']='1'
subprocess.run([sys.executable,'-m','pytest','-q','--junitxml=test-results.xml'],cwd=root,env=env,check=True)
subprocess.run([sys.executable,str(root/'scripts/smoke_server.py')],cwd=root,env=env,check=True)

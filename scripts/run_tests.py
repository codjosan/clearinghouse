from pathlib import Path
import subprocess,sys,os
r=Path(__file__).resolve().parents[1]
env=os.environ.copy();env['PYTHONPATH']=str(r/'src')
cmd=[sys.executable,'-m','unittest','discover','-s','tests','-v']
raise SystemExit(subprocess.run(cmd,cwd=r,env=env).returncode)

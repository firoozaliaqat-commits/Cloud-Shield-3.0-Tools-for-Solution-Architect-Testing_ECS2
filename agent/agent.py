"""Lightweight outbound-only ECS2 metrics pusher. Reads real host counters via /host/proc."""
import json,os, time, urllib.request, urllib.error
from pathlib import Path

RECEIVER=os.getenv('RECEIVER','').rstrip('/')
TOKEN=os.getenv('TELEMETRY_TOKEN','')
HOSTPROC=Path('/host/proc')

def cpu():
    fields=(HOSTPROC/'stat').read_text().splitlines()[0].split()[1:];vals=list(map(int,fields));return sum(vals), vals[3]+vals[4]
def mem():
    vals={}
    for line in (HOSTPROC/'meminfo').read_text().splitlines():
        key,rest=line.split(':',1)
        if key in ('MemTotal','MemAvailable'):vals[key]=int(rest.strip().split()[0])
    return round(100*(1-vals['MemAvailable']/vals['MemTotal']),2)
def net():
    rx=tx=0
    for line in (HOSTPROC/'net/dev').read_text().splitlines()[2:]:
        iface,details=line.split(':',1)
        if iface.strip()=='lo':continue
        counters=details.split();rx+=int(counters[0]);tx+=int(counters[8])
    return rx,tx

def run():
    try:prev=cpu()
    except Exception:prev=(1,0)
    while True:
        time.sleep(10)
        try:
            cur=cpu();dt=max(1,cur[0]-prev[0]);pct=round(max(0,min(100,100*(1-(cur[1]-prev[1])/dt))),2);prev=cur
            rx,tx=net();status=0
            try:
                with urllib.request.urlopen('http://127.0.0.1:8081/health',timeout=3) as response:status=response.status
            except urllib.error.HTTPError as ex:status=ex.code
            except Exception:pass
            payload={'name':'ecs2','timestamp':time.time(),'cpu_pct':pct,'mem_pct':mem(),'net_rx_bytes':rx,'net_tx_bytes':tx,'store_http':status}
            if not RECEIVER or not TOKEN:
                print('agent: local metrics collected (remote collector not configured)',payload,flush=True);continue
            req=urllib.request.Request(RECEIVER+'/api/telemetry/ingest',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','X-Telemetry-Token':TOKEN},method='POST')
            with urllib.request.urlopen(req,timeout=5) as response:print('agent telemetry pushed',response.status,flush=True)
        except Exception as ex:print('agent push failed',type(ex).__name__,str(ex)[:130],flush=True)
run()

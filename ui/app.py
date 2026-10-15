"""MatchMind overlay UI: FastAPI service serving pipeline highlights, stats,
and a pitch-map visualization of raw events.

Run:  uvicorn ui.app:app --reload   (from repo root) -> http://127.0.0.1:8000
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from orchestration.orchestrator import run  # noqa: E402

app = FastAPI(title="MatchMind", version="0.2")

ROOT = os.path.join(os.path.dirname(__file__), "..")
DEFAULT_FEED = os.path.join(ROOT, "data", "sample_match.jsonl")


@app.get("/api/match")
def match(path: str = Query(default=DEFAULT_FEED),
          persona: str = "casual", team: str = "HOME"):
    return run(path, persona=persona, favorite_team=team)


@app.get("/api/events")
def events(path: str = Query(default=DEFAULT_FEED),
           types: str = Query(default="shot,goal,pass")):
    want = set(t.strip() for t in types.split(",") if t.strip())
    out = []
    with open(path) as f:
        for raw in f:
            ev = json.loads(raw)
            if ev.get("type") in want:
                out.append(ev)
    return {"events": out, "pitch": {"x": 105, "y": 68}}


@app.get("/", response_class=HTMLResponse)
def home():
    return _PAGE


_PAGE = r"""
<!doctype html><html><head><meta charset="utf-8"><title>MatchMind — Pitch Map</title>
<style>
 body{font-family:system-ui;margin:1.5rem;max-width:1000px;color:#1b1b1f}
 h1{margin:0}.sub{color:#666;margin:.2rem 0 1rem}
 .wrap{display:flex;gap:1.5rem;flex-wrap:wrap}
 #pitch{background:#1f7a3d;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.2)}
 .panel{flex:1;min-width:260px}
 .controls{margin:.6rem 0;display:flex;align-items:center;gap:.6rem;flex-wrap:wrap}
 .row{padding:.3rem 0;border-bottom:1px solid #eee;font-size:.9rem}
 #clock{font-variant-numeric:tabular-nums;font-weight:600}
 .legend span{display:inline-block;margin-right:1rem;font-size:.82rem}
 .dot{display:inline-block;width:.7rem;height:.7rem;border-radius:50%;vertical-align:middle;margin-right:.25rem}
 label.chk{font-size:.85rem;display:inline-flex;align-items:center;gap:.25rem}
</style></head><body>
<h1>MatchMind</h1><p class="sub">Pitch map of a synthetic match — shots sized by xG, goals flagged, passes optional.</p>
<div class="controls">
 <button id="play">&#9654; Play</button>
 <input id="scrub" type="range" min="0" max="90" value="90" style="flex:1;min-width:200px">
 <span id="clock">90'</span>
 <label class="chk"><input type="checkbox" id="tShots" checked> Shots/goals</label>
 <label class="chk"><input type="checkbox" id="tPasses"> Passes</label>
</div>
<div class="legend">
 <span><i class="dot" style="background:#ffd166"></i>HOME shot</span>
 <span><i class="dot" style="background:#4cc9f0"></i>AWAY shot</span>
 <span><i class="dot" style="background:#ef476f"></i>goal</span>
 <span>&mdash; pass</span>
</div>
<div class="wrap">
 <svg id="pitch" width="630" height="408" viewBox="0 0 105 68"></svg>
 <div class="panel"><div id="stats"></div><h3>Highlights</h3><div id="feed"></div></div>
</div>
<script>
const SVG="http://www.w3.org/2000/svg";
const pitch=document.getElementById('pitch');
function L(x1,y1,x2,y2){const l=document.createElementNS(SVG,'line');
 l.setAttribute('x1',x1);l.setAttribute('y1',y1);l.setAttribute('x2',x2);l.setAttribute('y2',y2);
 l.setAttribute('stroke','rgba(255,255,255,.7)');l.setAttribute('stroke-width','.3');pitch.appendChild(l);}
function drawPitch(){
 L(0,0,105,0);L(0,68,105,68);L(0,0,0,68);L(105,0,105,68);L(52.5,0,52.5,68);
 const c=document.createElementNS(SVG,'circle');c.setAttribute('cx',52.5);c.setAttribute('cy',34);
 c.setAttribute('r',9.15);c.setAttribute('fill','none');c.setAttribute('stroke','rgba(255,255,255,.7)');
 c.setAttribute('stroke-width','.3');pitch.appendChild(c);
 L(0,13.85,16.5,13.85);L(0,54.15,16.5,54.15);L(16.5,13.85,16.5,54.15);
 L(105,13.85,88.5,13.85);L(105,54.15,88.5,54.15);L(88.5,13.85,88.5,54.15);
}
let EVENTS=[];
const showShots=()=>document.getElementById('tShots').checked;
const showPasses=()=>document.getElementById('tPasses').checked;
function render(maxMin){
 pitch.innerHTML='';drawPitch();
 EVENTS.filter(e=>e.minute<=maxMin).forEach(e=>{
  if(e.type==='pass'){ if(!showPasses()||e.end_x==null)return;
   const l=document.createElementNS(SVG,'line');
   l.setAttribute('x1',e.x);l.setAttribute('y1',e.y);l.setAttribute('x2',e.end_x);l.setAttribute('y2',e.end_y);
   l.setAttribute('stroke',e.complete?'rgba(255,255,255,.35)':'rgba(255,80,80,.45)');
   l.setAttribute('stroke-width','.2');pitch.appendChild(l);}
  else if(e.type==='shot'||e.type==='goal'){ if(!showShots())return;
   const c=document.createElementNS(SVG,'circle');
   c.setAttribute('cx',e.x);c.setAttribute('cy',e.y);
   c.setAttribute('r',Math.max(.6,(e.xg||.05)*6));
   c.setAttribute('fill',e.type==='goal'?'#ef476f':(e.team==='HOME'?'#ffd166':'#4cc9f0'));
   c.setAttribute('opacity','.9');pitch.appendChild(c);
   const t=document.createElementNS(SVG,'title');t.textContent=e.minute+"' "+e.team+" "+e.type+" xG "+(e.xg||'');c.appendChild(t);}
 });
}
Promise.all([
 fetch('/api/events?types=shot,goal,pass').then(r=>r.json()),
 fetch('/api/match').then(r=>r.json())
]).then(([ev,m])=>{
 EVENTS=ev.events;render(90);
 document.getElementById('stats').textContent='Final: '+JSON.stringify(m.final_stats.HOME)+' vs '+JSON.stringify(m.final_stats.AWAY);
 const f=document.getElementById('feed');m.highlights.forEach(h=>{const d=document.createElement('div');d.className='row';d.textContent=h.text;f.appendChild(d);});
});
const scrub=document.getElementById('scrub'),clock=document.getElementById('clock');
scrub.oninput=()=>{clock.textContent=scrub.value+"'";render(+scrub.value);};
document.getElementById('tShots').onchange=()=>render(+scrub.value);
document.getElementById('tPasses').onchange=()=>render(+scrub.value);
let timer=null;
document.getElementById('play').onclick=function(){
 if(timer){clearInterval(timer);timer=null;this.innerHTML='&#9654; Play';return;}
 this.innerHTML='&#10073;&#10073; Pause';let mm=0;scrub.value=0;
 timer=setInterval(()=>{mm+=1;if(mm>90){clearInterval(timer);timer=null;document.getElementById('play').innerHTML='&#9654; Play';return;}
  scrub.value=mm;clock.textContent=mm+"'";render(mm);},120);
};
</script></body></html>
"""

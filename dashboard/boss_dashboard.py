"""Generate BOSS状态看板.html next to a boss_status.json.

Usage: python boss_dashboard.py [path/to/boss_status.json]
(defaults to boss_status.example.json in this folder)
"""
import json
import sys
from pathlib import Path

src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "boss_status.example.json"
HERE = src.parent
data = json.loads(src.read_text(encoding="utf-8"))

TEMPLATE = r"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BOSS投递看板</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1d2330;--mut:#6b7280;--line:#e5e7eb;
--wait:#64748b;--resume:#2563eb;--interview:#16a34a;--ask:#d97706;--reject:#dc2626;--junk:#9ca3af}
@media (prefers-color-scheme:dark){:root{--bg:#111318;--card:#1a1d24;--ink:#e6e8ec;--mut:#9aa1ad;--line:#2b2f38}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.55 -apple-system,"Microsoft YaHei",sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:20px 16px 40px}
h1{font-size:22px;margin:0 0 4px}.sub{color:var(--mut);margin-bottom:18px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:18px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;border-top:3px solid var(--c)}
.kpi b{display:block;font-size:26px}.kpi span{color:var(--mut);font-size:12px}
.bar{display:flex;height:12px;border-radius:6px;overflow:hidden;margin-bottom:22px;background:var(--line)}
.bar i{display:block;background:var(--c)}
h2{font-size:16px;margin:22px 0 10px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--c);border-radius:10px;padding:12px 14px}
.card .h{display:flex;justify-content:space-between;gap:8px;font-weight:600}
.card .m{color:var(--mut);font-size:12px;margin:2px 0 8px}
.q{background:var(--bg);border-radius:6px;padding:6px 9px;margin:4px 0;font-size:13px}
.tag{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;color:#fff;background:var(--c);white-space:nowrap}
.filters{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}
.filters button{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:4px 12px;cursor:pointer}
.filters button.on{background:var(--ink);color:var(--bg)}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);font-size:13px}
th{color:var(--mut);font-weight:500}
.tw{overflow-x:auto}
</style></head><body><div class="wrap">
<h1>BOSS直聘 投递看板</h1>
<div class="sub">更新于 __UPDATED__ · 共 __TOTAL__ 个会话（BOSS 列表中可见部分）</div>
<div class="kpis" id="kpis"></div>
<div class="bar" id="bar"></div>
<h2>HR 回复（最新在前）</h2>
<div class="cards" id="cards"></div>
<h2>全部会话</h2>
<div class="filters" id="filters"></div>
<div class="tw"><table><thead><tr><th>时间</th><th>公司</th><th>HR</th><th>岗位</th><th>状态</th><th>备注</th></tr></thead><tbody id="rows"></tbody></table></div>
</div>
<script>
const D=__DATA__;
const ST={"面试邀约":"--interview","要简历":"--resume","询问意向":"--ask","拒绝":"--reject","无关":"--junk","已投递":"--wait"};
const c=s=>`var(${ST[s]||'--wait'})`;
const esc=s=>(s||'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
const cnt={};D.conversations.forEach(x=>cnt[x.stage]=(cnt[x.stage]||0)+1);
const order=Object.keys(ST);
document.getElementById('kpis').innerHTML=`<div class="kpi" style="--c:var(--ink)"><b>${D.conversations.length}</b><span>会话总数</span></div>`+
 order.filter(k=>cnt[k]).map(k=>`<div class="kpi" style="--c:${c(k)}"><b>${cnt[k]}</b><span>${k==='已投递'?'已投递·待回复':k}</span></div>`).join('');
document.getElementById('bar').innerHTML=order.filter(k=>cnt[k]).map(k=>`<i title="${k} ${cnt[k]}" style="--c:${c(k)};width:${cnt[k]/D.conversations.length*100}%"></i>`).join('');
document.getElementById('cards').innerHTML=D.replies.slice().sort((a,b)=>b.datetime.localeCompare(a.datetime)).map(r=>`
<div class="card" style="--c:${c(r.type)}"><div class="h"><span>${esc(r.company)}</span><span class="tag">${esc(r.type)}</span></div>
<div class="m">${esc(r.position)} · ${esc(r.hr)} · ${esc(r.datetime)}</div>
<div class="q"><b>HR：</b>${esc(r.said)}</div>
${r.my_reply?`<div class="q"><b>我：</b>${esc(r.my_reply)}</div>`:''}
<div class="m" style="margin:6px 0 0">建议：${esc(r.suggestion)}</div></div>`).join('');
let f='全部';
function draw(){document.getElementById('filters').innerHTML=['全部',...order.filter(k=>cnt[k])].map(k=>`<button class="${k===f?'on':''}" data-k="${k}">${k}${k==='全部'?'':' '+cnt[k]}</button>`).join('');
document.getElementById('rows').innerHTML=D.conversations.filter(x=>f==='全部'||x.stage===f).map(x=>`<tr><td>${esc(x.time)}</td><td>${esc(x.company)}</td><td>${esc(x.hr)} <span style="color:var(--mut)">${esc(x.title)}</span></td><td>${esc(x.position||'')}</td><td><span class="tag" style="--c:${c(x.stage)}">${esc(x.stage)}</span></td><td>${esc(x.note||'')}</td></tr>`).join('');}
document.getElementById('filters').onclick=e=>{const k=e.target.dataset.k;if(k){f=k;draw();}};draw();
</script></body></html>"""

html = (TEMPLATE.replace("__UPDATED__", data["updated"])
        .replace("__TOTAL__", str(data.get("total_conversations", len(data["conversations"]))))
        .replace("__DATA__", json.dumps(data, ensure_ascii=False)))
(HERE / "BOSS状态看板.html").write_text(html, encoding="utf-8")
print("ok", len(data["conversations"]), "conversations,", len(data["replies"]), "replies")

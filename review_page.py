"""Self-contained, offline HTML review of the same plan used by apply."""
import difflib
import html
import json
import re


def word_diff(before, after):
    left = re.findall(r"\s+|[^\s]+", before or "")
    right = re.findall(r"\s+|[^\s]+", after or "")
    old, new = [], []
    for action, a, b, c, d in difflib.SequenceMatcher(None, left, right, autojunk=False).get_opcodes():
        x, y = html.escape("".join(left[a:b])), html.escape("".join(right[c:d]))
        old.append(f"<del>{x}</del>" if action in {"delete", "replace"} else x)
        new.append(f"<ins>{y}</ins>" if action in {"insert", "replace"} else y)
    return "".join(old), "".join(new)


def render_page(plan):
    # Paths, source filenames and machine identity do not enter the HTML report.
    entries = []
    for entry in plan["entries"]:
        before, after = word_diff(entry["before"], entry["after"])
        entries.append({**entry, "before_html": before, "after_html": after})
    payload = json.dumps({"entries": entries, "counts": plan["counts"],
                          "blocked": plan["blocked"], "template_changed": plan["template_changed"]},
                         ensure_ascii=True).replace("<", "\\u003c")
    return PAGE.replace("/* REVIEW_DATA */", payload)


PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'none'; connect-src 'none'; base-uri 'none'; form-action 'none'">
<title>Document change review</title>
<style>
:root{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#162c39;background:#f2f5f6;font-synthesis:none}
*{box-sizing:border-box}body{margin:0}main{max-width:1100px;margin:auto;padding:34px 38px 50px}header{display:flex;justify-content:space-between;gap:20px;border-bottom:1px solid #cbd5da;padding-bottom:15px;font-size:13px;font-weight:650;letter-spacing:.03em}header span{font-weight:450;color:#526674}.eyebrow{font-size:12px;text-transform:uppercase;letter-spacing:.12em;color:#526674;font-weight:650}h1{font-size:50px;letter-spacing:-.05em;font-weight:720;line-height:1.1;margin:22px 0 12px}h1 strong{color:#295cba}#summary{font-size:17px;line-height:1.55;color:#445b68;margin:0 0 22px;max-width:740px}.notice{border-left:4px solid #b43537;background:#fff0ee;padding:14px 18px;margin-bottom:20px;line-height:1.5}.template-note{border-left:4px solid #a6640b;background:#fff5dc;padding:12px 18px;margin-bottom:18px}button{font:inherit;cursor:pointer}button:focus-visible,summary:focus-visible{outline:3px solid #6b4bc6;outline-offset:3px}.list-heading{display:flex;align-items:center;justify-content:space-between;gap:14px;margin:20px 0 12px}.list-heading h2{font-size:14px;margin:0}.toggle{border:1px solid #b5c3cb;background:white;padding:8px 12px;border-radius:5px;font-size:12px}.grid{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-bottom:22px}.doc{background:#fff;border:1px solid #c9d4da;border-radius:7px;text-align:left;padding:12px;min-height:74px;color:#193443}.doc b{display:block;font-size:12px;letter-spacing:.02em}.doc span{display:block;font-size:11px;margin-top:7px;color:#4d6675}.doc.changed,.doc.added{border-color:#74a0e8}.doc.conflict{border-color:#bf4d46;background:#fff0ee}.doc[aria-pressed=true]{outline:2px solid #295cba;outline-offset:0;background:#eaf1ff}.doc.conflict[aria-pressed=true]{outline-color:#b43537}.detail{background:white;border:1px solid #ccd6dc;border-radius:9px;overflow:hidden}.detail-head{padding:20px 24px;border-bottom:1px solid #dbe3e8;display:flex;justify-content:space-between;align-items:center;gap:12px}.detail-head h2{margin:0;font-size:19px;letter-spacing:-.025em}.status{font-size:12px;font-weight:650;color:#295cba}.reason{padding:16px 24px;background:#f8fafc;border-bottom:1px solid #dbe3e8;font-size:14px;line-height:1.6}.source-row{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.field{font-family:ui-monospace,monospace;font-size:12px;color:#526674}.value-old{color:#823e36;text-decoration:line-through}.value-new{color:#195532;font-weight:700}.compare{display:grid;grid-template-columns:1fr 1fr;gap:0}.pane{padding:22px 24px;min-width:0}.pane+.pane{border-left:1px solid #dbe3e8}.pane h3{font-size:11px;text-transform:uppercase;letter-spacing:.09em;margin:0 0 18px;color:#516777}.document{white-space:pre-wrap;overflow-wrap:anywhere;font-size:15px;line-height:1.7;min-height:160px}.document del{background:#ffe4df;color:#773126;text-decoration:line-through;border-radius:2px}.document ins{background:#d6f5df;color:#15552b;text-decoration:none;box-shadow:0 2px 0 #48865b;border-radius:2px}footer{margin-top:20px;font-size:12px;line-height:1.65;color:#536b79}footer p{margin:8px 0}code{font-size:12px;background:#e6ecef;padding:3px 5px;border-radius:3px}.empty{font-size:14px;color:#526674}.conflict-message{color:#8b2e2a;font-weight:650}details{margin-top:12px}details summary{cursor:pointer}#apply-help{overflow-wrap:anywhere}
@media(max-width:700px){main{padding:24px 18px}header{font-size:11px}h1{font-size:36px}#summary{font-size:15px}.grid{grid-template-columns:repeat(3,1fr)}.compare{grid-template-columns:1fr}.pane+.pane{border-left:0;border-top:1px solid #dbe3e8}.pane{padding:18px}.document{font-size:15px;min-height:0}.detail-head,.reason{padding:16px}.detail-head h2{font-size:17px}.source-row{gap:8px}}
</style></head><body><main>
<header>SPREADSHEET → DOCUMENTS <span>Local change review</span></header>
<h1 id="headline"></h1><p id="summary"></p>
<div id="warning" class="notice" hidden></div><div id="template" class="template-note" hidden>Template changed. Review the text difference for each affected document.</div>
<section aria-label="Document impact map"><div class="list-heading"><h2 id="map-title"></h2><button class="toggle" id="filter" aria-pressed="false">Show affected only</button></div><div id="map" class="grid"></div></section>
<section class="detail" aria-label="Selected document changes" aria-live="polite"><div class="detail-head"><h2 id="selected"></h2><span class="status" id="status"></span></div><div class="reason" id="reason"></div><div class="compare"><div class="pane"><h3>Baseline text · removed words crossed out</h3><div class="document" id="before"></div></div><div class="pane"><h3>Proposed text · new words underlined</h3><div class="document" id="after"></div></div></div></section>
<footer><p>This report has not changed any documents. Reused files are copied byte for byte into a new revision. The baseline stays intact.</p><details><summary>How to apply this review</summary><p id="apply-help"></p><p>Run from the repository folder, using this report's adjacent plan.json and a fresh output directory. Changed inputs or baseline files invalidate the review. The preview compares generated text, not Word layout or manual edits.</p></details></footer>
</main><script>
const data = /* REVIEW_DATA */;
const $ = id => document.getElementById(id);
const labels = {changed:'Rebuild',unchanged:'Reuse',added:'Create',removed:'Leave in baseline'};
const count = name => data.counts[name] || 0;
const rebuild = count('changed') + count('added');
let selected = (data.entries.find(e=>e.conflict) || data.entries.find(e=>e.action==='changed') || data.entries[0]).id;
let affectedOnly = false;
$('headline').innerHTML = data.blocked ? 'A document changed.<br><strong>Rebuild paused.</strong>' : `Rebuild ${rebuild}. <strong>Keep ${count('unchanged')}.</strong>`;
$('summary').textContent = data.blocked ? 'A generated file no longer matches its saved version. Rebuilding now could discard a change someone made in Word.' : `${count('changed')} changed, ${count('added')} new, ${count('unchanged')} reusable. Select a document to trace the source changes to its text.`;
if(count('removed')) $('summary').textContent += ` ${count('removed')} removed from this batch; their older files stay in the baseline.`;
$('map-title').textContent = `${data.entries.length} documents · impact map`;
$('template').hidden = !data.template_changed;
if(data.blocked){$('warning').hidden=false;$('warning').textContent='Nothing will be rebuilt. Preserve the edited files, reconcile the source or template, and make a new baseline before continuing. This tool does not merge manual Word edits.';}
$('apply-help').textContent = data.blocked ? 'Apply is blocked until the baseline conflict is resolved.' : 'python revisions.py apply path/to/plan.json output/next-revision';
function renderMap(){
  $('map').replaceChildren();
  const visible=data.entries.filter(e=>!affectedOnly || e.action!=='unchanged' || e.conflict);
  if(!visible.some(e=>e.id===selected) && visible.length) selected=visible[0].id;
  for(const e of visible){
    const b=document.createElement('button'); b.className=`doc ${e.conflict?'conflict':e.action}`;b.setAttribute('aria-pressed',String(e.id===selected));
    const name=document.createElement('b');name.textContent=e.id;
    const status=document.createElement('span');status.textContent=e.conflict?'! Conflict':labels[e.action];
    b.append(name,status);b.onclick=()=>{selected=e.id;renderMap();renderDetail();};$('map').append(b);
  }
  if(!visible.length){const p=document.createElement('p');p.className='empty';p.textContent='No affected documents. Every output can be reused.';$('map').append(p);}
}
function renderDetail(){
  const e=data.entries.find(e=>e.id===selected);$('selected').textContent=e.id+'.docx';$('status').textContent=e.conflict?'Rebuild blocked':labels[e.action];$('reason').replaceChildren();
  if(e.conflict){const p=document.createElement('div');p.className='conflict-message';p.textContent=e.conflict+'. The left pane shows the saved generated text, not the edited file.';$('reason').append(p);}
  for(const f of e.fields){
    const row=document.createElement('div');row.className='source-row';
    const field=document.createElement('span');field.className='field';field.textContent=f.field;
    const old=document.createElement('span');old.className='value-old';old.textContent=f.before??'(absent)';
    const arrow=document.createElement('span');arrow.textContent='→';
    const next=document.createElement('span');next.className='value-new';next.textContent=f.after??'(absent)';row.append(field,old,arrow,next);$('reason').append(row);
  }
  const explanation=document.createElement('div');
  explanation.textContent=e.action==='unchanged' ? (e.fields.length?'Source values changed, but the rendered text is identical. No rebuild needed.':'No output text changed. Reuse the existing file.') : e.action==='removed'?'Removed from the new batch. The baseline file will not be deleted.' : data.template_changed?'Template changed; the text comparison below shows its effect.':e.action==='added'?'New record. A document will be created.':'Source values changed. The text comparison below shows their effect.';
  $('reason').append(explanation);$('before').innerHTML=e.before_html||'<span class="empty">No baseline document</span>';$('after').innerHTML=e.after_html||'<span class="empty">Not included in the next revision</span>';
}
$('filter').onclick=()=>{affectedOnly=!affectedOnly;$('filter').textContent=affectedOnly?'Show all documents':'Show affected only';$('filter').setAttribute('aria-pressed',String(affectedOnly));renderMap();renderDetail();};renderMap();renderDetail();
</script></body></html>'''

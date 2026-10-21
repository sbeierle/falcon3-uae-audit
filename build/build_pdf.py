import re, subprocess, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

out = Path(sys.argv[1]).resolve()
src = (out / "report_v2.md").read_text(encoding="utf-8")

AR = re.compile("[\u0621-\u064A\u0671-\u06D3]+(?:[ \u060C.\u00AB\u00BB,]*[\u0621-\u064A\u0671-\u06D3\u0660-\u0669]+)*")
def wrap(seg):
    return AR.sub(lambda m: f'<span dir="rtl" lang="ar">{m.group(0)}</span>', seg)
parts = src.split("`")
for i in range(0, len(parts), 2):          # outside code spans only
    parts[i] = wrap(parts[i])
prepared = out / "_report_prepared.md"
prepared.write_text("`".join(parts), encoding="utf-8")

html = out / "report_v2.html"
subprocess.run([
    "pandoc", str(prepared), "-f", "markdown+smart+pipe_tables+fenced_divs+raw_html+implicit_figures",
    "-t", "html5", "--standalone", "--embed-resources", "--css", str(Path(__file__).with_name("style.css")),
    "--metadata", "pagetitle=Falcon3-7B-Instruct under UAE Statutory Frameworks (v2)", "--metadata", "lang=en",
    "-o", str(html), "--resource-path", str(out)], check=True)

pdf = out / "Falcon3-7B_UAE_Statutory_Audit_v2.pdf"
hdr = '<div style="font-family:Inter,sans-serif;font-size:7.5px;color:#6b7280;width:100%;padding:0 18mm;">Falcon3-7B-Instruct under UAE Statutory Frameworks · v2 · preprint draft</div>'
ftr = '<div style="font-family:Inter,sans-serif;font-size:7.5px;color:#6b7280;width:100%;text-align:center;"><span class="pageNumber"></span> / <span class="totalPages"></span></div>'
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto(html.as_uri()); pg.wait_for_load_state("networkidle")
    pg.pdf(path=str(pdf), format="A4", print_background=True, display_header_footer=True,
           header_template=hdr, footer_template=ftr,
           margin={"top": "18mm", "bottom": "17mm", "left": "18mm", "right": "18mm"})
    b.close()
print("wrote", pdf)

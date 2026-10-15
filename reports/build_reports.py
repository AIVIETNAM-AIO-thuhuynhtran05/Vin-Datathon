"""Dựng báo cáo PDF cho từng phần (EDA, Dashboard, Customer Segmentation, Forecasting).

Mỗi PDF ghép một hoặc nhiều file Markdown nguồn (reports/markdown/ hoặc README của từng folder):
Markdown → HTML (kèm CSS in ấn) → Microsoft Edge / Google Chrome chạy headless in ra PDF.

Phần nào chưa sẵn sàng (status="pending") sẽ bị bỏ qua, trừ khi chạy với --include-drafts
(khi đó PDF có nhãn BẢN NHÁP).

    python reports/build_reports.py                    # dựng các báo cáo đã sẵn sàng
    python reports/build_reports.py --only eda          # chỉ một báo cáo
    python reports/build_reports.py --include-drafts    # dựng cả bản nháp
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
MARKDOWN_DIR = REPORT_DIR / "markdown"

# Thứ tự trong list = thứ tự chương trong PDF.
REPORTS = {
    "eda": {
        "output": "01_EDA_report.pdf",
        "title": "Báo cáo EDA & Chất lượng dữ liệu",
        "subtitle": "Mô tả dữ liệu, kiểm tra missing / trùng lặp / dữ liệu không hợp lệ / ràng buộc nghiệp vụ / outlier",
        "sources": [MARKDOWN_DIR / "00_data_overview.md", MARKDOWN_DIR / "data_quality_and_eda.md"],
        "status": "ready",
    },
    "dashboard": {
        "output": "02_Dashboard_report.pdf",
        "title": "Báo cáo phân tích Dashboard",
        "subtitle": "Insight và khuyến nghị kinh doanh từ dashboard Power BI",
        "sources": [MARKDOWN_DIR / "dashboard_analysis_recommendations.md"],
        "status": "pending",
        "pending_reason": "Dashboard chưa được rà soát lại và chưa áp dụng data cleaning.",
    },
    "segmentation": {
        "output": "03_Customer_Segmentation_report.pdf",
        "title": "Báo cáo Phân nhóm khách hàng",
        "subtitle": "Rule-based + K-Means trên RFM: phương pháp, feature engineering, PCA, chọn k, profile và hành động theo nhóm",
        "sources": [
            ROOT / "customer_segmentation" / "README.md",
            MARKDOWN_DIR / "customer_segmentation_features.md",
            MARKDOWN_DIR / "customer_segmentation_pca.md",
            MARKDOWN_DIR / "customer_segmentation_k_selection.md",
            MARKDOWN_DIR / "customer_segment_profiles.md",
        ],
        "status": "ready",
    },
    "forecasting": {
        "output": "04_Forecasting_report.pdf",
        "title": "Báo cáo Dự báo doanh thu",
        "subtitle": "Dự báo Revenue theo ngày, 01/01/2023 – 01/07/2024",
        "sources": [ROOT / "forecasting" / "README.md"],
        "status": "pending",
        "pending_reason": "Chưa triển khai mô hình dự báo.",
    },
}

BROWSER_CANDIDATES = [
    os.environ.get("REPORT_BROWSER", ""),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome",
    "chromium",
    "chromium-browser",
    "microsoft-edge",
]

CSS = """
@page { size: A4; margin: 16mm 14mm 16mm 14mm; }
:root { --ink:#1f2933; --muted:#616e7c; --accent:#1c5cab; --line:#d9e2ec; --soft:#f3f6f9; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Arial, "Helvetica Neue", sans-serif; color: var(--ink); font-size: 10pt; line-height: 1.5; }
.cover { height: 250mm; display: flex; flex-direction: column; justify-content: center; page-break-after: always; }
.cover .kicker { color: var(--accent); font-weight: 700; letter-spacing: .08em; text-transform: uppercase; font-size: 9pt; }
.cover h1 { font-size: 26pt; line-height: 1.2; margin: 6mm 0 4mm; border: none; color: var(--ink); }
.cover .subtitle { font-size: 12pt; color: var(--muted); max-width: 150mm; }
.cover .meta { margin-top: 14mm; font-size: 9pt; color: var(--muted); border-top: 2px solid var(--accent); padding-top: 4mm; }
.cover .meta li { margin: 1mm 0; }
.draft { display: inline-block; background: #fff4e5; color: #8a4b00; border: 1px solid #f0b357; padding: 2mm 4mm;
         border-radius: 2mm; font-weight: 700; margin-top: 6mm; font-size: 10pt; }
.chapter { page-break-before: always; }
h1 { font-size: 17pt; color: var(--accent); border-bottom: 2px solid var(--accent); padding-bottom: 2mm; margin-top: 0; }
h2 { font-size: 13pt; margin-top: 7mm; border-bottom: 1px solid var(--line); padding-bottom: 1mm; page-break-after: avoid; }
h3 { font-size: 11pt; margin-top: 5mm; page-break-after: avoid; }
p, li { orphans: 3; widows: 3; }
a { color: var(--accent); text-decoration: none; }
code { font-family: Consolas, "Courier New", monospace; font-size: 8.5pt; background: var(--soft); padding: 0 1mm; border-radius: 1mm; }
pre { background: var(--soft); padding: 3mm; border-radius: 2mm; font-size: 6.8pt; line-height: 1.35; white-space: pre; overflow: hidden; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
blockquote { margin: 3mm 0; padding: 2mm 4mm; border-left: 3px solid var(--accent); background: var(--soft); color: var(--ink); }
table { border-collapse: collapse; width: 100%; margin: 3mm 0 4mm; font-size: 8pt; word-break: normal; overflow-wrap: break-word; }
td code, th code { white-space: nowrap; }
thead { display: table-header-group; }
tr { page-break-inside: avoid; }
th { background: #e4ecf5; text-align: left; font-weight: 600; }
th, td { border: 1px solid var(--line); padding: 1.2mm 1.6mm; vertical-align: top; }
tbody tr:nth-child(even) td { background: #fafbfc; }
img { max-width: 100%; display: block; margin: 3mm auto; page-break-inside: avoid; }
hr { border: none; border-top: 1px solid var(--line); margin: 5mm 0; }
"""


def find_browser() -> str:
    for candidate in BROWSER_CANDIDATES:
        if not candidate:
            continue
        resolved = candidate if Path(candidate).is_file() else shutil.which(candidate)
        if resolved:
            return resolved
    raise FileNotFoundError("Không tìm thấy Edge/Chrome. Đặt biến môi trường REPORT_BROWSER trỏ tới trình duyệt.")


def render_markdown(path: Path) -> str:
    """Markdown → HTML; ảnh tương đối được đổi thành đường dẫn tuyệt đối để trình duyệt tìm thấy."""
    text = path.read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists", "attr_list"])

    def absolute(match: re.Match[str]) -> str:
        source = html.unescape(match.group(1))
        if re.match(r"^[a-z]+:", source):
            return match.group(0)
        target = (path.parent / source).resolve()
        if not target.is_file():
            print(f"  ⚠ thiếu ảnh: {target}")
        return f'src="{target.as_uri()}"'

    return re.sub(r'src="([^"]+)"', absolute, body)


def build_html(spec: dict, draft: bool) -> str:
    sources = [source for source in spec["sources"] if source.is_file()]
    missing = [source for source in spec["sources"] if not source.is_file()]
    for source in missing:
        print(f"  ⚠ thiếu nguồn: {source}")
    source_items = "".join(f"<li>{html.escape(str(source.relative_to(ROOT)).replace(os.sep, '/'))}</li>" for source in sources)
    draft_note = (
        f'<div class="draft">BẢN NHÁP — {html.escape(spec.get("pending_reason", "chưa hoàn thiện"))}</div>' if draft else ""
    )
    cover = f"""
    <section class="cover">
      <div class="kicker">Vin Datathon 2026</div>
      <h1>{html.escape(spec["title"])}</h1>
      <div class="subtitle">{html.escape(spec["subtitle"])}</div>
      {draft_note}
      <div class="meta">
        <div>Ngày tạo: {date.today().strftime("%d/%m/%Y")}</div>
        <div>Nguồn nội dung:</div><ul>{source_items}</ul>
      </div>
    </section>"""
    chapters = "".join(f'<section class="chapter">{render_markdown(source)}</section>' for source in sources)
    return f"""<!doctype html><html lang="vi"><head><meta charset="utf-8">
<title>{html.escape(spec["title"])}</title><style>{CSS}</style></head><body>{cover}{chapters}</body></html>"""


def print_pdf(browser: str, html_path: Path, pdf_path: Path) -> None:
    command = [
        browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf-no-header",
        "--run-all-compositor-stages-before-draw", f"--print-to-pdf={pdf_path}", html_path.as_uri(),
    ]
    subprocess.run(command, check=True, capture_output=True, timeout=180)
    if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        raise RuntimeError(f"Trình duyệt không tạo được {pdf_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", choices=REPORTS, nargs="+", help="Chỉ dựng các báo cáo này")
    parser.add_argument("--include-drafts", action="store_true", help="Dựng cả báo cáo chưa sẵn sàng (gắn nhãn BẢN NHÁP)")
    args = parser.parse_args()

    browser = find_browser()
    with tempfile.TemporaryDirectory() as workdir:
        for key in args.only or REPORTS:
            spec = REPORTS[key]
            draft = spec["status"] != "ready"
            if draft and not args.include_drafts:
                print(f"Bỏ qua {spec['output']}: {spec['pending_reason']} (dùng --include-drafts để dựng bản nháp)")
                continue
            print(f"Dựng {spec['output']}{' (bản nháp)' if draft else ''}…")
            html_path = Path(workdir) / f"{key}.html"
            html_path.write_text(build_html(spec, draft), encoding="utf-8")
            pdf_path = REPORT_DIR / spec["output"]
            print_pdf(browser, html_path, pdf_path)
            print(f"  → {pdf_path.relative_to(ROOT)} ({pdf_path.stat().st_size / 1024:,.0f} KB)")


if __name__ == "__main__":
    main()

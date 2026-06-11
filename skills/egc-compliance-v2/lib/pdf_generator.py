"""
Generates the 4-page print-quality PDF via Playwright.

MANDATORY LAYOUT RULES (enforced by experience with Chromium headless print):
1. Use display:table / display:table-cell for ALL multi-column layouts
2. NEVER use flexbox or CSS grid in print-targeted HTML
3. All images (logo, charts) MUST be base64-embedded data URIs
4. Page breaks: page-break-after:always on .page, page-break-inside:avoid on tables
5. @page { size: letter; margin: 36pt; }
6. Font sizes >= 8px (smaller text may be invisible at print resolution)
"""

import base64
import subprocess
import tempfile
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def render(report: dict, charts: dict, ecm_data: dict, output_path: Path, base_dir: Path):
    """Render report dict + charts → PDF at output_path."""
    # Load logo as base64
    logo_path = _find_logo(base_dir)
    logo_b64 = _encode_image(logo_path) if logo_path else None

    # Render Jinja2 template
    env = Environment(loader=FileSystemLoader(str(base_dir / 'templates')))
    template = env.get_template('report_print.html.j2')

    html = template.render(
        report=report,
        charts=charts,
        logo_b64=logo_b64,
        ecm_data=ecm_data,
    )

    # Write HTML to temp file
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as f:
        f.write(html)
        html_path = f.name

    # Run Playwright
    _playwright_to_pdf(html_path, str(output_path))

    Path(html_path).unlink(missing_ok=True)


def _playwright_to_pdf(html_path: str, pdf_path: str):
    script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const browser = await chromium.launch({{ args: ['--no-sandbox', '--disable-setuid-sandbox'] }});
  const page = await browser.newPage();
  await page.setViewportSize({{ width: 816, height: 1056 }});
  await page.goto('file://{html_path}', {{ waitUntil: 'networkidle' }});
  await page.waitForTimeout(1200);
  await page.pdf({{
    path: '{pdf_path}',
    format: 'Letter',
    printBackground: true,
    margin: {{ top: '0.5in', right: '0.5in', bottom: '0.5in', left: '0.5in' }},
  }});
  await browser.close();
  console.log('PDF written to {pdf_path}');
}})();
"""
    result = subprocess.run(['node', '-e', script], capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"Playwright failed: {result.stderr}")


def _find_logo(base_dir: Path):
    """Look for JRose.png or Audette logo in parent directories."""
    for candidate in [
        base_dir.parent / 'JRose.png',
        base_dir.parent.parent / 'JRose.png',
        base_dir / 'assets' / 'logo.png',
    ]:
        if candidate.exists():
            return candidate
    return None


def _encode_image(path: Path) -> str:
    data = path.read_bytes()
    ext = path.suffix.lower().lstrip('.')
    mime = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg'}.get(ext, 'image/png')
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"

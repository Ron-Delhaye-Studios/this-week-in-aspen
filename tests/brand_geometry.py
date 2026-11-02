"""Measure the approved footer mark in loaded Playfair at phone/desktop widths.

Serve the checkout separately. BASE_URL defaults to the local luxury review server;
CHROMIUM_PATH can select Chromium. No production data writes occur.
"""
import json
import os
from pathlib import Path
import urllib.request
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get('BASE_URL', 'http://127.0.0.1:8784/')
OUT = ROOT / 'design/review/luxury'
OUT.mkdir(parents=True, exist_ok=True)
FONT_RESPONSES = {}


def network(context):
    def route(request):
        url = request.request.url
        if 'fonts.googleapis.com' in url or 'fonts.gstatic.com' in url:
            try:
                if url not in FONT_RESPONSES:
                    with urllib.request.urlopen(url, timeout=20) as response:
                        FONT_RESPONSES[url] = response.read(), response.headers.get('Content-Type')
                data, kind = FONT_RESPONSES[url]
                return request.fulfill(body=data, content_type=kind)
            except Exception:
                return request.abort()
        if 'api.open-meteo.com' in url:
            return request.fulfill(json={'current': {'temperature_2m': 45, 'weather_code': 2, 'time': '2026-11-01T18:00'}})
        if url.startswith(BASE):
            return request.continue_()
        return request.abort()
    context.route('**/*', route)


results = []
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        executable_path=os.environ.get('CHROMIUM_PATH', '/usr/bin/chromium'),
        headless=True, args=['--no-sandbox'])
    for width in (320, 390, 430, 1440):
        for theme in ('light', 'dark'):
            context = browser.new_context(viewport={'width': width, 'height': 844}, service_workers='block')
            context.add_init_script('localStorage.setItem("gh-theme", ' + json.dumps(theme) + ')')
            network(context)
            page = context.new_page()
            page.goto(BASE, wait_until='networkidle')
            page.evaluate("document.fonts.load('900 40px \"Playfair Display\"', 'THE GOLDEN HOUR')")
            page.evaluate("document.fonts.load('italic 900 40px \"Playfair Display\"', 'HOUR')")
            page.evaluate('document.fonts.ready')
            page.locator('.gh-footer').scroll_into_view_if_needed()
            result = page.evaluate('''() => {
                const mark = document.querySelector('.gh-footer .gh-foot-word');
                const range = document.createRange(); range.selectNodeContents(mark);
                const rect = range.getBoundingClientRect(), box = mark.getBoundingClientRect();
                const loaded = [...document.fonts].filter(f => f.family.includes('Playfair Display') && f.status === 'loaded');
                return {
                    text: mark.textContent, textWidth: rect.width, availableWidth: box.width,
                    textLeft: rect.left, textRight: rect.right, boxLeft: box.left, boxRight: box.right,
                    fontFamily: getComputedStyle(mark).fontFamily,
                    fontSize: getComputedStyle(mark).fontSize,
                    normalFontLoaded: loaded.some(f => f.style === 'normal' && f.weight === '900'),
                    italicFontLoaded: loaded.some(f => f.style === 'italic' && f.weight === '900'),
                    theme: document.documentElement.dataset.theme
                };
            }''')
            assert result['text'] == 'THE GOLDEN HOUR', result
            assert result['normalFontLoaded'] and result['italicFontLoaded'], result
            assert result['theme'] == theme, result
            assert result['textWidth'] <= result['availableWidth'] + 1, result
            assert result['textLeft'] >= result['boxLeft'] - 1 and result['textRight'] <= result['boxRight'] + 1, result
            results.append({'width': width, **result, 'fits': True})
            if width in (320, 390):
                page.locator('.gh-footer').screenshot(path=str(OUT / f'footer-{width}-{theme}.png'))
            context.close()
    browser.close()
(OUT / 'brand-geometry.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps(results, indent=2))

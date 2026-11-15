import urllib.request
import re
import os
import zipfile

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

os.makedirs('frontend/public/fonts', exist_ok=True)
os.makedirs('scripts/fonts_tmp', exist_ok=True)

targets = [
    ('corpta', 'https://www.1001fonts.com/corpta-demo-font.html'),
    ('aeruno', 'https://www.1001fonts.com/aeruno-font.html')
]

for name, url in targets:
    print(f"\n=== Checking {name} ===")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        # Search for forms, buttons, or data attributes
        forms = re.findall(r'<form[^>]*action=[\"\']([^\"\']+)[\"\'][^>]*>', html)
        print("Form actions:", forms)
        buttons = re.findall(r'<button[^>]*>([^<]+)</button>', html)
        print("Buttons:", buttons[:10])
        # Look for any occurrence of zip or download or ttf or otf in the entire html
        tokens = set(re.findall(r'[\"\'\(]([^\s\"\'\(\)]*\.(?:zip|ttf|otf|woff2?))[ \"\'\)]', html, re.I))
        print("Font/zip files referenced:", tokens)
        dls = re.findall(r'https?://[^\s\"\'\<\>]+download[^\s\"\'\<\>]*', html, re.I)
        print("Download URLs:", dls[:5])
    except Exception as e:
        print(f"Error fetching {name}: {e}")

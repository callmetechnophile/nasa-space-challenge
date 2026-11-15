import urllib.request
import os

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
out_dir = 'frontend/public/fonts'
os.makedirs(out_dir, exist_ok=True)

urls = [
    ('corpta.otf', 'https://st.1001fonts.net/download/font/corpta-demo.regular.otf'),
    ('aeruno.otf', 'https://st.1001fonts.net/download/font/aeruno.trial.otf'),
    ('corpta.zip', 'https://www.1001fonts.com/download/corpta-demo.zip'),
    ('aeruno.zip', 'https://www.1001fonts.com/download/aeruno.zip'),
]

for filename, url in urls:
    dest = os.path.join(out_dir, filename)
    print(f"Downloading {url} -> {dest}...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
            print(f"  Received {len(content)} bytes, status={resp.status}, content-type={resp.headers.get('content-type')}")
            with open(dest, 'wb') as f:
                f.write(content)
    except Exception as e:
        print(f"  Error: {e}")

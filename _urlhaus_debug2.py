import urllib.request
from config import Config

url = 'https://urlhaus-api.abuse.ch/v1/url/'
body = 'url=https://google.com'.encode()
headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Auth-Key': Config.URLHAUS_KEY}
import ssl
ctx = ssl._create_unverified_context()
req = urllib.request.Request(url, data=body, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        print('status:', resp.status)
        print(resp.read().decode()[:600])
except Exception as e:
    print('ERR:', type(e).__name__, str(e)[:300])
    if hasattr(e, 'read'):
        print(e.read().decode()[:600])

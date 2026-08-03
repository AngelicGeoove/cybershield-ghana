import config
from services import threat_intel

targets = ['https://google.com/', 'http://example.com/', 'http://testphp.vulnweb.com/']
for t in targets:
    print('\n>>', t)
    r = threat_intel.check_url_urlhaus(t)
    print(r)
print('\nDone')

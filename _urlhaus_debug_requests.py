import os
import requests
import certifi
import config

URLHAUS_URL = 'https://urlhaus-api.abuse.ch/v1/url/'

key = os.environ.get('URLHAUS_KEY', '') or getattr(config.Config, 'URLHAUS_KEY', '')
print('URLHAUS_KEY loaded:', bool(key), 'len', len(key))

test_targets = ['https://google.com/', 'http://example.com/', 'http://testphp.vulnweb.com/']
header_names = ['Auth-Key', 'API-KEY', 'API-Key', 'api_key', 'key']

for target in test_targets:
    print('\n=== TARGET:', target)
    for h in header_names + [None]:
        headers = {}
        if h and key:
            headers[h] = key
        try:
            print('Trying headers:', headers or '(none)')
            # verify with certifi bundle
            resp = requests.post(URLHAUS_URL, data={'url': target}, headers=headers, timeout=10, verify=certifi.where())
            print('status_code:', resp.status_code)
            print('resp.text[:500]:', resp.text[:500])
        except requests.exceptions.SSLError as e:
            print('SSLError:', e)
            try:
                resp = requests.post(URLHAUS_URL, data={'url': target}, headers=headers, timeout=10, verify=False)
                print('RETRY verify=False status_code:', resp.status_code)
                print('resp.text[:500]:', resp.text[:500])
            except Exception as e2:
                print('Retry failed:', type(e2), e2)
        except Exception as e:
            print('Error:', type(e), e)

print('\nDone')

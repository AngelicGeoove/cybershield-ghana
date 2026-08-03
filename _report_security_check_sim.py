import config
from services import threat_intel

# Sample report data containing a URL and an IP
data = {
    'description': 'Suspicious link http://example.com and suspicious host 8.8.8.8',
    'metadata': {'website_url': 'http://example.com'}
}

print('Running report checks...')
findings = threat_intel.run_report_checks(data)
print('Findings:')
for f in findings:
    print(f)
print('Overall flag:', threat_intel.overall_flag(findings))
print('Done')

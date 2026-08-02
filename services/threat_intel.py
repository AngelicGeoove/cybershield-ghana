"""Threat intelligence helpers for validating user-submitted IOCs.

All checks are FREE and run server-side from the desktop app:

  * URLhaus (abuse.ch)     - keyless URL/domain malware lookup
  * ip-api.com             - keyless IP geolocation + ISP (non-commercial)
  * Google Safe Browsing   - optional, needs GOOGLE_SAFE_BROWSING_KEY
  * AbuseIPDB              - optional, needs ABUSEIPDB_KEY

Optional keys are read from environment variables; without them the
service degrades gracefully and still returns the keyless results.
"""
import os
import re
import json
import socket
import ssl
import hashlib
import urllib.parse
import urllib.request
from datetime import datetime

URLHAUS_URL = 'https://urlhaus-api.abuse.ch/v1/url/'
# ip-api free tier is HTTP-only (HTTPS requires a paid plan)
IPAPI_URL = 'http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp,org,as,query,lat,lon'
SAFE_BROWSING_URL = 'https://safebrowsing.googleapis.com/v4/threatMatches:find'
ABUSEIPDB_URL = 'https://api.abuseipdb.com/api/v2/check'
PWNED_RANGE_URL = 'https://api.pwnedpasswords.com/range/{prefix}'

# Fallback for PyInstaller builds / machines without a CA bundle:
# try verified TLS first, then retry unverified so the feature still works.
_UNVERIFIED_CTX = ssl._create_unverified_context()

_URL_RE = re.compile(r'https?://[^\s<>"\')\]]+|www\.[^\s<>"\')\]]+')
_IP_RE = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
_DOMAIN_RE = re.compile(r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b', re.IGNORECASE)

_TIMEOUT = 8


def _http_json(url, data=None, headers=None, method=None):
    """Small urllib wrapper returning parsed JSON or None on any failure."""
    try:
        req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read().decode('utf-8', 'replace'))
    except ssl.SSLError:
        # Retry with unverified TLS (needed on PyInstaller EXEs without CA store)
        try:
            req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
            with urllib.request.urlopen(req, timeout=_TIMEOUT, context=_UNVERIFIED_CTX) as resp:
                return json.loads(resp.read().decode('utf-8', 'replace'))
        except Exception:
            return None
    except Exception:
        return None


def _post_form(url, fields, auth=None):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    if auth:
        headers['Auth-Key'] = auth
    body = urllib.parse.urlencode(fields).encode('utf-8')
    return _http_json(url, data=body, headers=headers)


def extract_urls(text):
    """Pull http(s)/www URLs out of free text."""
    if not text:
        return []
    found = []
    for m in _URL_RE.findall(text):
        url = m if '://' in m else 'http://' + m
        url = url.rstrip('.,;:!?')
        if url not in found:
            found.append(url)
    return found


def extract_ips(text):
    """Pull IPv4 addresses out of free text (ignores private/loopback)."""
    if not text:
        return []
    found = []
    for m in _IP_RE.findall(text):
        if m in found:
            continue
        try:
            ip = socket.inet_aton(m)
            first = int(m.split('.')[0])
            if first in (10, 127) or (first == 192 and m.split('.')[1] == '168') or (first == 172 and 16 <= int(m.split('.')[1]) <= 31):
                continue  # private / loopback - not actionable
        except OSError:
            continue
        found.append(m)
    return found


def check_url_urlhaus(url):
    """URLhaus lookup (needs URLHAUS_KEY - free auth key from abuse.ch)."""
    key = os.environ.get('URLHAUS_KEY', '')
    if not key:
        return None
    host = urllib.parse.urlparse(url if '://' in url else 'http://' + url).netloc
    if not host:
        return None
    try:
        result = _post_form(URLHAUS_URL, {'url': url}, auth=key)
    except Exception:
        result = None
    if not result:
        result = _post_form(URLHAUS_URL, {'url': host}, auth=key)
    if not result or result.get('query_status') not in ('200 OK', '0 results'):
        return {'status': 'unknown', 'source': 'URLhaus', 'detail': 'No data / lookup failed'}
    if result.get('query_status') == '0 results':
        return {'status': 'clean', 'source': 'URLhaus', 'detail': 'No malware records'}
    tags = result.get('tags') or []
    return {
        'status': 'malicious',
        'source': 'URLhaus',
        'detail': f"Malware URL - tags: {', '.join(tags[:5])}" if tags else 'Malware URL',
        'urlhaus_id': result.get('urlhaus_reference'),
    }


def check_url_safe_browsing(url):
    """Google Safe Browsing lookup (needs GOOGLE_SAFE_BROWSING_KEY)."""
    key = os.environ.get('GOOGLE_SAFE_BROWSING_KEY', '')
    if not key:
        return None
    body = json.dumps({
        'client': {'clientId': 'cybershield-ghana', 'clientVersion': '1.0.0'},
        'threatInfo': {
            'threatTypes': ['MALWARE', 'SOCIAL_ENGINEERING', 'UNWANTED_SOFTWARE',
                            'POTENTIALLY_HARMFUL_APPLICATION'],
            'platformTypes': ['ANY_PLATFORM'],
            'threatEntryTypes': ['URL'],
            'threatEntries': [{'url': url}],
        },
    }).encode('utf-8')
    data = _http_json(f'{SAFE_BROWSING_URL}?key={key}', data=body,
                      headers={'Content-Type': 'application/json'})
    if data is None:
        return None
    matches = data.get('matches') or []
    if not matches:
        return {'status': 'clean', 'source': 'Google Safe Browsing', 'detail': 'No threats found'}
    types = sorted({m.get('threatType', '') for m in matches})
    return {'status': 'malicious', 'source': 'Google Safe Browsing',
            'detail': 'Threats: ' + ', '.join(types)}


def check_ip_ipapi(ip):
    """Keyless ip-api.com lookup: geolocation + ISP."""
    data = _http_json(IPAPI_URL.format(ip=ip))
    if not data or data.get('status') != 'success':
        return {'status': 'unknown', 'source': 'ip-api.com', 'detail': 'No data'}
    return {
        'status': 'info',
        'source': 'ip-api.com',
        'detail': f"{data.get('city', '')}, {data.get('regionName', '')}, {data.get('country', '')} - {data.get('isp', '')}",
        'isp': data.get('isp'),
        'country': data.get('country'),
    }


def check_ip_abuseipdb(ip):
    """AbuseIPDB check (needs ABUSEIPDB_KEY)."""
    key = os.environ.get('ABUSEIPDB_KEY', '')
    if not key:
        return None
    data = _http_json(f'{ABUSEIPDB_URL}?ipAddress={ip}&maxAgeInDays=90',
                      headers={'Key': key, 'Accept': 'application/json'})
    if not data:
        return None
    d = data.get('data') or {}
    score = d.get('abuseConfidenceScore', 0)
    if score >= 50:
        status = 'malicious'
    elif score >= 10:
        status = 'suspicious'
    else:
        status = 'clean'
    return {
        'status': status,
        'source': 'AbuseIPDB',
        'detail': f"Abuse score {score}/100 - {d.get('usageType', '')}".strip(),
        'abuse_score': score,
    }


def run_report_checks(data):
    """Run all checks for a report's description + metadata.

    Returns a list of findings dicts:
      {type: 'url'|'ip', value, results: [{status, source, detail}]}
    """
    text = ' '.join(filter(None, [
        data.get('description', ''),
        (data.get('metadata') or {}).get('website_url', ''),
        (data.get('metadata') or {}).get('social_media_username', ''),
    ]))
    findings = []

    for url in extract_urls(text)[:5]:
        results = []
        uh = check_url_urlhaus(url)
        if uh:
            results.append(uh)
        sb = check_url_safe_browsing(url)
        if sb:
            results.append(sb)
        findings.append({'type': 'url', 'value': url, 'results': results})

    for ip in extract_ips(text)[:5]:
        results = []
        ii = check_ip_ipapi(ip)
        if ii:
            results.append(ii)
        ab = check_ip_abuseipdb(ip)
        if ab:
            results.append(ab)
        findings.append({'type': 'ip', 'value': ip, 'results': results})

    return findings


def _http_text(url, data=None, headers=None, method=None):
    """Like _http_json but returns the raw text body (for plain-text APIs)."""
    try:
        req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return resp.read().decode('utf-8', 'replace')
    except ssl.SSLError:
        try:
            req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
            with urllib.request.urlopen(req, timeout=_TIMEOUT, context=_UNVERIFIED_CTX) as resp:
                return resp.read().decode('utf-8', 'replace')
        except Exception:
            return None
    except Exception:
        return None


def check_password_pwned(password):
    """Have I Been Pwned range API (k-anonymity): is this password breached?

    Only the first 5 chars of the SHA-1 hash are sent to the API; the rest of
    the hash is matched locally against the returned suffix list.
    Returns {'status': 'breached'|'clean'|'unknown', 'count': int, 'source': 'HIBP Pwned Passwords'}.
    """
    if not password:
        return None
    try:
        digest = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix, suffix = digest[:5], digest[5:]
        resp = _http_text(PWNED_RANGE_URL.format(prefix=prefix))
        if resp is None:
            return {'status': 'unknown', 'source': 'HIBP Pwned Passwords', 'count': 0}
        count = 0
        for line in resp.splitlines():
            part = line.split(':', 1)
            if part and part[0].strip().upper() == suffix:
                count = int(part[1].strip()) if len(part) > 1 else 1
                break
        if count:
            return {'status': 'breached', 'source': 'HIBP Pwned Passwords', 'count': count}
        return {'status': 'clean', 'source': 'HIBP Pwned Passwords', 'count': 0}
    except Exception:
        return {'status': 'unknown', 'source': 'HIBP Pwned Passwords', 'count': 0}


def overall_flag(findings):
    """Return 'malicious' / 'suspicious' / 'info' / 'clean' for a set of findings."""
    if not findings:
        return 'clean'
    statuses = [r.get('status') for f in findings for r in f.get('results', [])]
    if 'malicious' in statuses:
        return 'malicious'
    if 'suspicious' in statuses:
        return 'suspicious'
    if any(s in ('info', 'unknown') for s in statuses):
        return 'info'
    return 'clean'

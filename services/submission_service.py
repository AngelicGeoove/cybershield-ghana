import os
import webbrowser
import urllib.parse
import threading
from datetime import datetime, date

def prepare_report_content(data):
    reporter = data.get('reporter', {})
    metadata = data.get('metadata', {})
    lines = [
        'CYBER INCIDENT REPORT',
        '=' * 40,
        f'Reporter: {reporter.get("full_name", "")}',
        f'Organisation: {reporter.get("organisation", "")}',
        f'Email: {reporter.get("email", "")}',
        f'Phone: {reporter.get("phone", "")}',
        f'Location: {reporter.get("location", "")}',
        f'Age: {reporter.get("age", "")}',
        '',
        'INCIDENT DETAILS',
        '=' * 40,
        f'Category: {data.get("category", "")}',
        f'Incident Date: {metadata.get("incident_date", "")}',
        f'Incident Time: {metadata.get("incident_time", "")}',
        f'Platform: {metadata.get("platform", "")}',
        f'Description: {data.get("description", "")}',
        '',
        'ADDITIONAL INFORMATION',
        '-' * 40,
    ]
    for key, value in metadata.items():
        if value and key not in ('incident_date', 'incident_time', 'platform'):
            label = key.replace('_', ' ').title()
            lines.append(f'{label}: {value}')
    lines.append('')
    lines.append('END OF REPORT')
    return '\n'.join(lines)

def _open_browser_async(url):
    """Open browser in a separate thread to avoid blocking the request."""
    def _open():
        try:
            webbrowser.open(url)
        except Exception:
            pass  # Fail silently - don't break the request
    thread = threading.Thread(target=_open, daemon=True)
    thread.start()

def _truncate_for_url(text, max_chars=3500):
    """Truncate text to fit within URL length limits."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + '\n\n[Report truncated due to length limits]'

def submit_to_channel(channel, content, incident_id):
    channel = channel.lower()
    truncated_content = _truncate_for_url(content)
    
    if channel == 'csa-online-form':
        # Open CSA online form - include report content as query params where supported
        # Note: The actual form may not support prefilling via URL params
        url = 'https://www.csaghana.org/report'
        _open_browser_async(url)
        return {
            'status': 'sent',
            'external_ref': 'CSA Online Form',
            'error': 'Report opened in browser. Please copy the report content from the confirmation page to paste into the form.'
        }
    elif channel == 'email':
        # Open email client with pre-filled content
        subject = urllib.parse.quote(f'Cyber Incident Report - {incident_id}')
        body = urllib.parse.quote(f'Please review and send this cyber incident report to report@csa.gov.gh\n\n{truncated_content}')
        mailto_url = f'mailto:report@csa.gov.gh?subject={subject}&body={body}'
        _open_browser_async(mailto_url)
        return {
            'status': 'sent',
            'external_ref': 'Email Client',
            'error': None
        }
    elif channel == 'whatsapp':
        # Open WhatsApp with pre-filled message
        message = urllib.parse.quote(f'Cyber Incident Report - {incident_id}\n\n{truncated_content}')
        whatsapp_url = f'https://wa.me/233501603111?text={message}'
        _open_browser_async(whatsapp_url)
        return {
            'status': 'sent',
            'external_ref': 'WhatsApp',
            'error': None
        }
    else:
        return {
            'status': 'prepared',
            'external_ref': None,
            'error': f'Report prepared for channel: {channel}. Please complete submission through the official channel.'
        }
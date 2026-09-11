import re
from ai_client import chat_json

SYSTEM = '''You are KaryaSetu Site Update Agent. Convert a construction supervisor's natural-language site report into factual structured data. Never invent facts. Return JSON only.'''

def _normalize(data, transcript):
    if not isinstance(data, dict):
        data = {}
    m = re.search(r'(\d{1,3})\s*(?:percent|%)', transcript, re.I)
    progress = float(m.group(1)) if m else float(data.get('progress') or 0)
    progress = max(0, min(100, progress))
    m = re.search(r'(\d+)\s*days?', transcript, re.I)
    delay_days = int(m.group(1)) if m else int(float(data.get('delay_days') or 0))
    reason = str(data.get('delay_reason') or '').strip()
    if not reason:
        m = re.search(r'(?:because|due to)\s+(.+?)(?:[.!?]|$)', transcript, re.I)
        reason = m.group(1).strip() if m else ''
    description = str(data.get('activity_description') or '').strip() or transcript[:160].strip()
    remarks = str(data.get('remarks') or '').strip() or transcript.strip()
    risk = str(data.get('risk') or '').strip().upper()
    if risk not in {'HIGH', 'MEDIUM', 'LOW'}:
        risk = ''
    if not risk and delay_days >= 3:
        risk = 'HIGH'
    elif not risk and delay_days > 0:
        risk = 'MEDIUM'
    return {
        'activity_description': description,
        'progress': progress,
        'delay_days': delay_days,
        'delay_reason': reason,
        'remarks': remarks,
        'risk': risk,
        'agent': 'voice_update_agent'
    }

async def run(transcript: str):
    prompt = f'''Extract the site update.
Return exactly:
{{"activity_description":"","progress":0,"delay_days":0,"delay_reason":"","remarks":"","risk":""}}
progress is 0-100. delay_days is an integer. risk is HIGH, MEDIUM, LOW or empty.
Transcript: {transcript}'''
    try:
        data = await chat_json(SYSTEM, prompt)
    except Exception:
        data = {}
    return _normalize(data, transcript)

from ai_client import chat_json

SYSTEM = '''You are KaryaSetu Schedule Intelligence Agent. Match a reported construction activity to the correct L6 schedule activity. Use only the supplied candidates. Return JSON only.'''

async def run(description, candidates):
    if not candidates:
        return {'matched_id': None, 'confidence': 0, 'reason': 'No L6 activities available', 'agent': 'schedule_agent'}
    compact = [{'id': a.get('id'), 'code': a.get('activity_code'), 'name': a.get('activity_name'), 'parent': a.get('parent_activity')} for a in candidates]
    prompt = f'''Reported activity: {description}
Candidates:
{compact}
Choose the candidate that best matches the reported work. Return {{"matched_id":"candidate id","confidence":0,"reason":"short explanation"}}. confidence must be 0-1.'''
    try:
        data = await chat_json(SYSTEM, prompt)
        mid = data.get('matched_id')
        conf = max(0, min(1, float(data.get('confidence') or 0)))
        if not any(a.get('id') == mid for a in candidates):
            mid, conf = None, 0
        return {'matched_id': mid, 'confidence': conf, 'reason': str(data.get('reason') or ''), 'agent': 'schedule_agent'}
    except Exception as e:
        return {'matched_id': None, 'confidence': 0, 'reason': f'Model unavailable: {e}', 'agent': 'schedule_agent:fallback'}

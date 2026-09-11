from ai_client import chat_json

SYSTEM='''You are KaryaSetu Recovery Recommendation Agent. Produce one concise, practical corrective action for a construction project. Never invent unavailable project facts. Return JSON only.'''

async def run(activity, reason, gap, days, risk):
    prompt=f'''Activity: {activity}\nDelay reason: {reason or 'Not specified'}\nProgress gap: {gap}%\nDelay days: {days}\nRisk: {risk}\nReturn {{"action":"","priority":"LOW|MEDIUM|HIGH|CRITICAL"}}.'''
    try:data=await chat_json(SYSTEM,prompt)
    except Exception:data={}
    priority=str(data.get('priority') or risk).upper()
    if priority not in {'LOW','MEDIUM','HIGH','CRITICAL'}:priority=risk
    action=str(data.get('action') or 'Review the affected activity, remove the identified constraint, and update the recovery plan.')
    return {'action':action,'priority':priority,'agent':'recommendation_agent'}

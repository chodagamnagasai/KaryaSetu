from ai_client import chat_json

SYSTEM='''You are KaryaSetu Risk Detection Agent. Assess project execution risk from supplied progress facts. Never invent causes or impacts. Return JSON only.'''

async def run(activity, gap, delay_days, delay_reason, status):
    sev='CRITICAL' if delay_days>=3 or gap>=20 else ('HIGH' if delay_days>=2 or gap>=10 else ('MEDIUM' if status!='ON TRACK' else 'LOW'))
    prompt=f'''Activity: {activity}\nProgress gap: {gap}%\nDelay days: {delay_days}\nReason: {delay_reason or 'Not specified'}\nStatus: {status}\nReturn {{"risk":"LOW|MEDIUM|HIGH|CRITICAL","description":"","impact":""}}.'''
    try:data=await chat_json(SYSTEM,prompt)
    except Exception:data={}
    risk=str(data.get('risk') or sev).upper()
    if risk not in {'LOW','MEDIUM','HIGH','CRITICAL'}:risk=sev
    return {'risk':risk,'description':str(data.get('description') or delay_reason or f'Actual progress is {gap}% behind planned progress.'),'impact':str(data.get('impact') or ''),'agent':'risk_agent'}

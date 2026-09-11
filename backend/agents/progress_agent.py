from ai_client import chat_json

SYSTEM='''You are KaryaSetu Progress Analysis Agent. Analyze planned versus actual construction progress. Do not invent facts. Return JSON only.'''

async def run(planned, actual, delay_days):
    gap=round(float(planned)-float(actual),1)
    prompt=f'''Planned progress: {planned}%\nActual progress: {actual}%\nDelay days: {delay_days}\nReturn {{"gap":{gap},"status":"ON TRACK|AT RISK|DELAYED","summary":""}}.'''
    try:data=await chat_json(SYSTEM,prompt)
    except Exception:
        data={}
    status=str(data.get('status') or ('DELAYED' if delay_days>0 or gap>=10 else ('AT RISK' if gap>0 else 'ON TRACK'))).upper()
    if status not in {'ON TRACK','AT RISK','DELAYED'}:status='DELAYED' if delay_days>0 or gap>=10 else ('AT RISK' if gap>0 else 'ON TRACK')
    return {'gap':gap,'status':status,'summary':str(data.get('summary') or ''),'agent':'progress_agent'}

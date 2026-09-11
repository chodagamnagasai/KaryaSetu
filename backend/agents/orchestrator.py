from agents.voice_agent import run as voice_agent
from agents.schedule_agent import run as schedule_agent
from agents.progress_agent import run as progress_agent
from agents.risk_agent import run as risk_agent
from agents.recommendation_agent import run as recommendation_agent
from tools.schedule_tools import shortlist

class KaryaSetuOrchestrator:
    name='karyasetu_orchestrator'

    async def process_update(self, transcript, activities, forced_activity=None, forced_progress=None):
        trace=[]
        try:
            extracted=await voice_agent(transcript); trace.append('voice_update_agent')
        except Exception:
            extracted=self._fallback_extract(transcript); extracted['agent']='voice_update_agent:fallback'; trace.append('voice_update_agent:fallback')

        description=extracted['activity_description']
        candidates=shortlist(description, activities, 8)
        if forced_activity:
            activity=forced_activity; match={'matched_id':activity.get('id'),'confidence':1.0,'reason':'User-selected activity','agent':'schedule_agent'}
        else:
            try:
                match=await schedule_agent(description,candidates); trace.append('schedule_agent')
                activity=next((a for a in candidates if a.get('id')==match.get('matched_id')), candidates[0] if candidates else None)
                if match.get('matched_id') is None and activity:
                    match={'matched_id':activity.get('id'),'confidence':0.05,'reason':'Deterministic candidate fallback','agent':'schedule_agent:fallback'}
            except Exception:
                activity=candidates[0] if candidates else None; match={'matched_id':activity.get('id') if activity else None,'confidence':0.0,'reason':'Fallback lexical match','agent':'schedule_agent:fallback'}; trace.append('schedule_agent:fallback')
        if not activity:return {'extracted':extracted,'matched_activity':None,'status':'NO MATCH','agent_trace':trace}

        actual=float(forced_progress if forced_progress is not None else extracted.get('progress') or 0)
        planned=float(activity.get('planned_progress') or 0)
        progress=await progress_agent(planned,actual,int(extracted.get('delay_days') or 0)); trace.append('progress_agent')
        risk=await risk_agent(activity.get('activity_name',''),progress['gap'],int(extracted.get('delay_days') or 0),extracted.get('delay_reason',''),progress['status']); trace.append('risk_agent')
        recommendation=None
        if progress['status']!='ON TRACK' or risk['risk'] in {'HIGH','CRITICAL'}:
            recommendation=await recommendation_agent(activity.get('activity_name',''),extracted.get('delay_reason',''),progress['gap'],int(extracted.get('delay_days') or 0),risk['risk']); trace.append('recommendation_agent')
        return {'extracted':extracted,'matched_activity':activity,'similarity':round(float(match.get('confidence') or 0),3),'match_reason':match.get('reason',''),'progress_analysis':progress,'risk_analysis':risk,'recommendation_analysis':recommendation,'status':progress['status'],'progress_gap':progress['gap'],'agent_trace':trace,'orchestrator':self.name}

    @staticmethod
    def _fallback_extract(text):
        import re
        low=text.lower(); m=re.search(r'(\d{1,3})\s*(?:percent|%)',low); progress=float(m.group(1)) if m else 0
        d=re.search(r'(\d+)\s*day',low); days=int(d.group(1)) if d else 0
        reason='Heavy rain' if 'rain' in low or 'weather' in low else ('Material shortage' if 'material' in low else '')
        desc='Foundation excavation' if 'foundation' in low and 'excavat' in low else ('Excavation' if 'excavat' in low else text[:80])
        return {'activity_description':desc,'progress':progress,'delay_days':days,'delay_reason':reason,'remarks':text,'risk':'HIGH' if days else ''}

orchestrator=KaryaSetuOrchestrator()

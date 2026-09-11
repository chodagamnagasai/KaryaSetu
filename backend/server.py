from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Any
import os, re, uuid, logging, math, json, asyncio

import bcrypt
import jwt

ROOT = Path(__file__).parent
load_dotenv(ROOT / '.env')
MONGO_URL = os.getenv('MONGO_URL', '')
if not MONGO_URL:
    raise RuntimeError('backend/.env is missing MONGO_URL')
DB_NAME = os.getenv('DB_NAME', 'karyasetu')
JWT_SECRET = os.getenv('JWT_SECRET', 'change-me-in-production')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'openrouter/free')

client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=10000)
db = client[DB_NAME]
app = FastAPI(title='KaryaSetu', version='3.0.0', description='AI planning-to-execution bridge')
api = APIRouter(prefix='/api')
logger = logging.getLogger('karyasetu')
security = HTTPBearer(auto_error=False)
from agents.orchestrator import orchestrator
from tools.schedule_tools import shortlist


def now(): return datetime.now(timezone.utc).isoformat()
def clean(doc):
    if not doc: return None
    d = dict(doc); d.pop('_id', None); return d

def hash_password(v): return bcrypt.hashpw(v.encode(), bcrypt.gensalt()).decode()
def verify_password(v, h): return bcrypt.checkpw(v.encode(), h.encode())
def make_token(user):
    return jwt.encode({'sub': user['id'], 'role': user['role'], 'exp': datetime.now(timezone.utc)+timedelta(hours=12)}, JWT_SECRET, algorithm='HS256')

async def current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials or credentials.scheme.lower() != 'bearer':
        raise HTTPException(401, 'Please sign in to continue')
    try: payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=['HS256'])
    except jwt.PyJWTError: raise HTTPException(401, 'Your session has expired')
    user = await db.users.find_one({'id': payload.get('sub')}, {'_id':0, 'password_hash':0})
    if not user: raise HTTPException(401, 'User not found')
    return user

async def manager(user=Depends(current_user)):
    if user['role'] not in ['ADMIN','PROJECT MANAGER']: raise HTTPException(403, 'Manager access required')
    return user

class Login(BaseModel): email: str; password: str
class ProjectCreate(BaseModel): name: str; location: str=''; description: str=''
class ActivityCreate(BaseModel):
    project_id: str; activity_code: str; activity_name: str; level: str='L6'; parent_activity: str=''; planned_start: str=''; planned_end: str=''; planned_progress: float=Field(0, ge=0, le=100)
class ActivityEdit(BaseModel): actual_progress: Optional[float]=Field(None, ge=0, le=100); status: Optional[str]=None
class UpdateCreate(BaseModel):
    project_id: str; transcript: str=Field(min_length=3); activity_id: Optional[str]=None; progress: Optional[float]=Field(None, ge=0, le=100); language: str='en-IN'

SEED = [
('L5','Site Preparation','L5-01'),('L6','Site Clearing','L6-01'),('L6','Surveying','L6-02'),('L6','Excavation','L6-03'),
('L5','Foundation','L5-02'),('L6','Foundation Excavation','L6-04'),('L6','Reinforcement','L6-05'),('L6','Formwork','L6-06'),('L6','Concrete Pouring','L6-07'),
('L5','Structural Work','L5-03'),('L6','Column Construction','L6-08'),('L6','Beam Construction','L6-09'),('L6','Slab Work','L6-10'),
('L5','MEP','L5-04'),('L6','Electrical Installation','L6-11'),('L6','Plumbing','L6-12'),('L5','Finishing','L5-05'),('L6','Plastering','L6-13'),('L6','Painting','L6-14'),('L6','Final Finishing','L6-15')]

STOP=set('the a an and or of to for in on at with from is are was were work completed complete percent today yesterday this that site project activity block area has have by due behind delay delayed because very our we did done construction installation progress reporting update'.split())
SYN={'concrete':['pour','poured','pouring','concreting'],'column':['columns','column construction'],'beam':['beams','beam construction'],'slab':['slabs','slab work'],'steel':['reinforcement','rebar'],'reinforcement':['steel','rebar'],'excavate':['excavation','excavated'],'paint':['painting'],'plaster':['plastering'],'electrical':['electric'],'labour':['labor','manpower','workers'],'material':['cement','steel','delivery','shortage']}

def words(text):
    return [w for w in re.findall(r'[a-z0-9]+', text.lower()) if w not in STOP and len(w)>2]

def lexical_score(query,target):
    q=set(words(query)); t=set(words(target))
    for a,bs in SYN.items():
        if a in q: q.update(bs)
    if not q or not t:return 0.0
    return len(q&t)/math.sqrt(len(q)*len(t))

async def seed():
    accounts=[('Admin','admin@karyasetu.demo','Admin@123','ADMIN'),('Project Manager','manager@karyasetu.demo','Manager@123','PROJECT MANAGER'),('Site Supervisor','supervisor@karyasetu.demo','Supervisor@123','SITE SUPERVISOR')]
    for n,e,p,r in accounts:
        if not await db.users.find_one({'email':e}): await db.users.insert_one({'id':str(uuid.uuid4()),'name':n,'email':e,'password_hash':hash_password(p),'role':r,'created_at':now()})
    if await db.projects.count_documents({})==0:
        for idx,(name,loc) in enumerate([('Hyderabad Metro Infrastructure Project','Hyderabad, Telangana'),('Highway Construction Project','Bengaluru–Mysuru Corridor')]):
            pid=str(uuid.uuid4()); await db.projects.insert_one({'id':pid,'name':name,'location':loc,'description':'Infrastructure delivery programme','created_at':now()})
            parent=''
            for i,(level,n,code) in enumerate(SEED):
                if level=='L5': parent=code
                await db.activities.insert_one({'id':str(uuid.uuid4()),'project_id':pid,'activity_code':code,'activity_name':n,'level':level,'parent_activity':'' if level=='L5' else parent,'planned_start':f'2026-{(i%9)+1:02d}-05','planned_end':f'2026-{(i%9)+2:02d}-25','planned_progress':min(95,10+i*4+idx*3),'actual_progress':min(90,8+i*3+idx*2),'status':'ON TRACK','created_at':now()})

@app.on_event('startup')
async def startup():
    await db.command('ping'); await seed(); await db.users.create_index('email',unique=True)

@api.post('/auth/login')
async def login(body:Login):
    u=await db.users.find_one({'email':body.email.strip().lower()})
    if not u or not verify_password(body.password,u['password_hash']):raise HTTPException(401,'Incorrect email or password')
    d=clean(u); d.pop('password_hash',None); d['token']=make_token(d); return d

@api.get('/auth/me')
async def me(user=Depends(current_user)):return user

@api.get('/health')
async def health():
    await db.command('ping')
    return {'status':'ok','database':'connected','ai_provider':'OpenRouter','ai_model':OPENROUTER_MODEL}

@api.get('/ai/health')
async def ai_health(user=Depends(current_user)):
    return {'openrouter':bool(OPENROUTER_API_KEY),'model':OPENROUTER_MODEL,'agents':['orchestrator','voice_update_agent','schedule_agent','progress_agent','risk_agent','recommendation_agent']}

@api.get('/projects')
async def projects(user=Depends(current_user)):
    out=[]
    async for p in db.projects.find({}, {'_id':0}).sort('created_at',-1):
        p=clean(p); acts=await db.activities.find({'project_id':p['id']},{'_id':0}).to_list(5000); p['activity_count']=len(acts); p['overall_progress']=round(sum(float(a.get('actual_progress',0)) for a in acts)/len(acts),1) if acts else 0; out.append(p)
    return out

@api.post('/projects')
async def create_project(body:ProjectCreate,user=Depends(manager)):
    if not body.name.strip():raise HTTPException(400,'Project name is required')
    d={'id':str(uuid.uuid4()),'name':body.name.strip(),'location':body.location.strip(),'description':body.description.strip(),'created_at':now()}; await db.projects.insert_one(d); return clean(d)

@api.get('/projects/{pid}')
async def get_project(pid:str,user=Depends(current_user)):
    p=clean(await db.projects.find_one({'id':pid},{'_id':0}));
    if not p:raise HTTPException(404,'Project not found')
    p['activities']=[clean(x) async for x in db.activities.find({'project_id':pid},{'_id':0}).sort('activity_code',1)]; return p

@api.get('/users')
async def users(user=Depends(manager)):return [clean(x) async for x in db.users.find({}, {'_id':0,'password_hash':0})]

@api.get('/activities')
async def activities(project_id:Optional[str]=None,level:Optional[str]=None,status:Optional[str]=None,user=Depends(current_user)):
    q={};
    if project_id:q['project_id']=project_id
    if level:q['level']=level
    if status:q['status']=status
    return [clean(x) async for x in db.activities.find(q,{'_id':0}).sort('activity_code',1)]

@api.post('/activities')
async def create_activity(body:ActivityCreate,user=Depends(manager)):
    if body.level not in ['L5','L6']:raise HTTPException(400,'Level must be L5 or L6')
    if not await db.projects.find_one({'id':body.project_id}):raise HTTPException(404,'Project not found')
    d=body.model_dump()|{'id':str(uuid.uuid4()),'actual_progress':0.0,'status':'ON TRACK','created_at':now()}; await db.activities.insert_one(d); return clean(d)

@api.patch('/activities/{aid}')
async def edit_activity(aid:str,body:ActivityEdit,user=Depends(manager)):
    a=await db.activities.find_one({'id':aid});
    if not a:raise HTTPException(404,'Activity not found')
    d={k:v for k,v in body.model_dump().items() if v is not None}
    if 'actual_progress' in d and 'status' not in d:
        gap=float(a.get('planned_progress',0))-d['actual_progress']; d['status']='DELAYED' if gap>=10 else ('AT RISK' if gap>0 else 'ON TRACK')
    d['updated_at']=now(); await db.activities.update_one({'id':aid},{'$set':d}); return clean(await db.activities.find_one({'id':aid},{'_id':0}))

@api.post('/updates')
async def create_update(body:UpdateCreate,user=Depends(current_user)):
    if not await db.projects.find_one({'id':body.project_id}):raise HTTPException(404,'Project not found')
    activities=[clean(x) async for x in db.activities.find({'project_id':body.project_id,'level':'L6'},{'_id':0})]
    forced=clean(await db.activities.find_one({'id':body.activity_id,'project_id':body.project_id},{'_id':0})) if body.activity_id else None
    result=await orchestrator.process_update(body.transcript,activities,forced_activity=forced,forced_progress=body.progress)
    activity=result.get('matched_activity')
    if not activity:raise HTTPException(400,'No L6 activities found for this project')
    extracted=result['extracted']; progress=result['progress_analysis']; risk_analysis=result['risk_analysis']; recommendation_analysis=result.get('recommendation_analysis')
    actual=float(body.progress if body.progress is not None else extracted.get('progress') or 0)
    planned=float(activity.get('planned_progress') or 0); days=int(extracted.get('delay_days') or 0); status=progress['status']; gap=progress['gap']
    await db.activities.update_one({'id':activity['id']},{'$set':{'actual_progress':actual,'status':status,'last_update_at':now()}})
    upd={'id':str(uuid.uuid4()),'project_id':body.project_id,'activity_id':activity['id'],'supervisor_id':user['id'],'supervisor_name':user['name'],'transcript':body.transcript,'language':body.language,'extracted_description':extracted['activity_description'],'progress':actual,'planned_progress':planned,'progress_gap':gap,'delay_days':days,'delay_reason':extracted.get('delay_reason',''),'remarks':extracted.get('remarks',body.transcript),'confidence':result.get('similarity',0),'ai_engine':'OpenRouter multi-agent','agent_trace':result.get('agent_trace',[]),'created_at':now()}
    await db.updates.insert_one(upd)
    risk=None; rec=None
    if status!='ON TRACK' or risk_analysis.get('risk') in {'HIGH','CRITICAL'}:
        risk={'id':str(uuid.uuid4()),'project_id':body.project_id,'activity_id':activity['id'],'title':f"{activity['activity_name']} needs attention",'description':risk_analysis.get('description') or extracted.get('delay_reason') or f'Actual progress is {gap}% behind planned progress.','severity':risk_analysis.get('risk','MEDIUM'),'source':'KaryaSetu Risk Agent','created_at':now()}
        await db.risks.insert_one(risk)
        recommendation_analysis=recommendation_analysis or await orchestrator_recommendation_fallback(activity,gap,days,risk['severity'],risk['description'])
        rec={'id':str(uuid.uuid4()),'project_id':body.project_id,'activity_id':activity['id'],'problem':risk['description'],'action':recommendation_analysis['action'],'priority':recommendation_analysis['priority'],'created_at':now()}
        await db.recommendations.insert_one(rec)
    return {'update':clean(upd),'analysis':extracted,'matched_activity':activity,'similarity':result.get('similarity',0),'status':status,'progress_gap':gap,'risk':risk,'recommendation':rec['action'] if rec else None,'agents':result.get('agent_trace',[])}

async def orchestrator_recommendation_fallback(activity,gap,days,severity,description):
    from agents.recommendation_agent import run
    return await run(activity.get('activity_name',''),description,gap,days,severity)

@api.post('/voice/transcribe')
async def transcribe(payload:dict,user=Depends(current_user)):
    return {'transcript':payload.get('text',''),'mode':'browser-speech-or-text'}

@api.post('/voice/analyze')
async def analyze(payload:dict,user=Depends(current_user)):
    pid=payload.get('project_id'); transcript=str(payload.get('transcript','')).strip()
    if len(transcript)<3: raise HTTPException(422,'transcript must contain at least 3 characters')
    query={'level':'L6'}
    if pid: query['project_id']=pid
    activities=[clean(x) async for x in db.activities.find(query,{'_id':0})]
    result=await orchestrator.process_update(transcript,activities,forced_progress=payload.get('progress'))
    if pid: result['project_id']=pid
    else: result['project_scope']='all L6 schedule activities (no project_id supplied)'
    return result

@api.post('/updates/manual')
async def manual_update(payload:dict,user=Depends(current_user)):
    body=UpdateCreate(project_id=payload.get('project_id',''),transcript=payload.get('remarks') or payload.get('activity_name') or 'Manual project update',activity_id=payload.get('activity_id'),progress=payload.get('progress'),language=payload.get('language','en-IN'))
    return await create_update(body,user)

@api.post('/updates/import')
async def import_updates(project_id:str,file:UploadFile=File(...),user=Depends(current_user)):
    import pandas as pd
    try:
        df=pd.read_csv(file.file) if file.filename.lower().endswith('.csv') else pd.read_excel(file.file)
    except Exception as e: raise HTTPException(400,f'Could not read update file: {e}')
    results=[]; errors=[]
    for i,row in df.iterrows():
        try:
            data={str(k).strip().lower():row[k] for k in df.columns}
            aid=str(data.get('activity_id') or '').strip() or None
            transcript=str(data.get('transcript') or data.get('remarks') or data.get('update') or '')
            if len(transcript)<3: raise ValueError('transcript/update text is required')
            prog=data.get('progress'); prog=float(prog) if prog==prog and prog is not None else None
            r=await create_update(UpdateCreate(project_id=project_id,transcript=transcript,activity_id=aid,progress=prog),user)
            results.append(r)
        except Exception as e: errors.append({'row':int(i)+2,'error':str(e)})
    return {'imported':len(results),'errors':errors,'results':results}

async def recent(name,pid=None,limit=100):
    q={'project_id':pid} if pid else {}; return [clean(x) async for x in db[name].find(q,{'_id':0}).sort('created_at',-1).limit(limit)]
@api.get('/updates')
async def updates(project_id:Optional[str]=None,user=Depends(current_user)):return await recent('updates',project_id)
@api.get('/risks')
async def risks(project_id:Optional[str]=None,user=Depends(current_user)):return await recent('risks',project_id)
@api.get('/recommendations')
async def recommendations(project_id:Optional[str]=None,user=Depends(current_user)):return await recent('recommendations',project_id)

@api.get('/dashboard')
async def dashboard(project_id:Optional[str]=None,user=Depends(current_user)):
    q={'project_id':project_id} if project_id else {}; acts=[clean(x) async for x in db.activities.find(q,{'_id':0})]; risks=await recent('risks',project_id,20); updates=await recent('updates',project_id,10)
    total=len(acts); avg=round(sum(float(a.get('actual_progress',0)) for a in acts)/total,1) if total else 0
    return {'kpis':{'projects':await db.projects.count_documents({}),'progress':avg,'activities':total,'delayed':sum(a.get('status')=='DELAYED' for a in acts),'at_risk':sum(a.get('status')=='AT RISK' for a in acts),'risks':len(risks),'critical':sum(r.get('severity') in ['CRITICAL','HIGH'] for r in risks)},'activities':acts,'risks':risks,'updates':updates}

@api.post('/import/schedule')
async def import_schedule(project_id:str,file:UploadFile=File(...),user=Depends(manager)):
    import pandas as pd
    if not await db.projects.find_one({'id':project_id}):raise HTTPException(404,'Project not found')
    try: df=pd.read_csv(file.file) if file.filename.lower().endswith('.csv') else pd.read_excel(file.file)
    except Exception as e:raise HTTPException(400,f'Could not read schedule: {e}')
    df.columns=[re.sub(r'[^a-z0-9]+','_',str(c).strip().lower()).strip('_') for c in df.columns]
    aliases={'code':'activity_code','activity':'activity_name','name':'activity_name','start':'planned_start','end':'planned_end','planned':'planned_progress','progress':'planned_progress','parent':'parent_activity'}
    for old,new in aliases.items():
        if old in df.columns and new not in df.columns:df=df.rename(columns={old:new})
    missing={'activity_code','activity_name','level','planned_start','planned_end','planned_progress'}-set(df.columns)
    if missing:raise HTTPException(400,'Missing columns: '+', '.join(sorted(missing)))
    docs=[]; errors=[]
    for i,row in df.iterrows():
        try:
            level=str(row['level']).upper().strip(); level=level if level in ['L5','L6'] else 'L6'; pp=float(row['planned_progress']);
            if not 0<=pp<=100:raise ValueError('planned_progress must be 0-100')
            docs.append({'id':str(uuid.uuid4()),'project_id':project_id,'activity_code':str(row['activity_code']),'activity_name':str(row['activity_name']),'level':level,'parent_activity':str(row.get('parent_activity','')),'planned_start':str(row['planned_start']),'planned_end':str(row['planned_end']),'planned_progress':pp,'actual_progress':0.0,'status':'ON TRACK','created_at':now()})
        except Exception as e:errors.append({'row':int(i)+2,'error':str(e)})
    if docs:await db.activities.insert_many(docs)
    return {'imported':len(docs),'errors':errors}

app.include_router(api)
configured_origins=[x.strip() for x in os.getenv('CORS_ORIGINS','').split(',') if x.strip()]
origins=sorted(set(configured_origins + ['http://localhost:5173','http://127.0.0.1:5173']))
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r'^https://.*\.vercel\.app$',
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
@app.on_event('shutdown')
async def shutdown():client.close()

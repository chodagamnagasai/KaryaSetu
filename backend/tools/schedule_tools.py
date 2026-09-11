import re, math

STOP=set('the a an and or of to for in on at with from is are was were work completed complete percent today yesterday this that site project activity block area has have by due behind delay delayed because very our we did done construction installation progress reporting update'.split())
SYN={'concrete':['pour','poured','pouring','concreting'],'column':['columns','column construction'],'beam':['beams','beam construction'],'slab':['slabs','slab work'],'steel':['reinforcement','rebar'],'reinforcement':['steel','rebar'],'excavate':['excavation','excavated'],'paint':['painting'],'plaster':['plastering'],'electrical':['electric'],'labour':['labor','manpower','workers'],'material':['cement','steel','delivery','shortage']}

def words(text):
    return [w for w in re.findall(r'[a-z0-9]+', str(text).lower()) if w not in STOP and len(w)>2]

def lexical_score(query,target):
    q=set(words(query)); t=set(words(target))
    for a,bs in SYN.items():
        if a in q:q.update(bs)
    if not q or not t:return 0.0
    return len(q&t)/math.sqrt(len(q)*len(t))

def shortlist(description, activities, limit=8):
    ranked=[]
    for a in activities:
        text=f"{a.get('activity_code','')} {a.get('activity_name','')} {a.get('parent_activity','')}"
        ranked.append((lexical_score(description,text),a))
    return [a for _,a in sorted(ranked,key=lambda x:x[0],reverse=True)[:limit]]

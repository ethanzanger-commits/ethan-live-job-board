#!/usr/bin/env python3
import json, pathlib, datetime, urllib.request, urllib.error, re, html
root=pathlib.Path(__file__).parents[1]; p=root/'data/jobs.json'; jobs=json.loads(p.read_text()); now=datetime.datetime.now(datetime.timezone.utc).isoformat()
HEADERS={'User-Agent':'Mozilla/5.0 EthanJobBoard/1.0'}
def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=30) as r: return json.load(r)
def clean(s): return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',s or ''))).strip()
def route(company):
    c=company.lower()
    if 'lightricks' in c: return ('Hannah or Tom (referral list)','Send the official role link plus current CV and ask whether either can refer before applying.')
    if 'wix' in c or 'base44' in c: return ('Sam Schneidman (existing Wix/Base44 contact)','Send Sam the exact role link and updated CV. Ask whether he can refer or make the right internal handoff.')
    return ('No matching referrer found in the referral sheet','Use the official application path and lead with the U.S.-market, paid-media, and growth experience that matches the role.')
def fit(title,desc,location):
    text=(title+' '+desc).lower(); score=58
    for k,w in {'demand generation':18,'growth marketing':14,'paid media':14,'performance marketing':14,'partnership':10,'field marketing':10,'media':8,'marketing manager':8,'campaign':5,'analytics':5,'b2b':5}.items():
        if k in text: score+=w
    for k,w in {'hebrew':-6,'product marketing':-5,'developer':-25,'engineer':-25,'designer':-18,'sales development':-12}.items():
        if k in text: score+=w
    if 'jerusalem' in location.lower(): score+=7
    return max(35,min(96,score))
# Verify every curated job URL.
for j in jobs:
    try:
        req=urllib.request.Request(j['url'],headers=HEADERS)
        with urllib.request.urlopen(req,timeout=25) as r: body=r.read(400000).decode('utf-8','ignore').lower(); code=r.status
        dead=code>=400 or any(x in body for x in ['job is no longer available','position has been filled','this job has expired','page not found'])
        j['open']=not dead
    except urllib.error.HTTPError as e: j['open']=False if e.code in (404,410) else j.get('open',True)
    except Exception: pass
    j['checked_at']=now
# Discover new matching Lightricks roles from its official Greenhouse board.
try:
    for x in get_json('https://boards-api.greenhouse.io/v1/boards/lightricks/jobs?content=true').get('jobs',[]):
        title=x.get('title',''); loc=(x.get('location') or {}).get('name',''); desc=clean(x.get('content',''))
        if not (re.search(r'market|growth|demand|partner|media|campaign',title,re.I) and re.search(r'israel|jerusalem|tel aviv',loc,re.I)): continue
        url=x.get('absolute_url');
        if any(j['url'].split('?')[0]==url.split('?')[0] for j in jobs): continue
        contact,move=route('Lightricks'); score=fit(title,desc,loc)
        jobs.append({'id':'gh-'+str(x['id']),'rank':99,'company':'Lightricks','title':title,'score':score,'location':loc,'track':'Marketing','fit':'New match','why':clean(desc)[:280]+'…','contact':contact,'move':move,'url':url,'open':True,'checked_at':now,'source':'Official Lightricks Greenhouse board'})
except Exception: pass
# Discover new matching Wonderful roles from its official Ashby board.
try:
    for x in get_json('https://api.ashbyhq.com/posting-api/job-board/wonderful').get('jobs',[]):
        title=x.get('title',''); loc=x.get('location',''); desc=x.get('descriptionPlain','')
        if not (re.search(r'market|growth|demand|partner|media|campaign',title,re.I) and re.search(r'israel|tel aviv|jerusalem',loc,re.I)): continue
        url=x.get('jobUrl');
        if any(j['url']==url for j in jobs): continue
        contact,move=route('Wonderful'); score=fit(title,desc,loc)
        jobs.append({'id':'ashby-'+x['id'],'rank':99,'company':'Wonderful','title':title,'score':score,'location':loc,'track':'Marketing','fit':'New match','why':clean(desc)[:280]+'…','contact':contact,'move':move,'url':url,'open':True,'checked_at':now,'source':'Official Wonderful Ashby board'})
except Exception: pass
jobs.sort(key=lambda j:(not j.get('open',True),-j.get('score',0),j['company'],j['title']))
for i,j in enumerate(jobs,1): j['rank']=i
p.write_text(json.dumps(jobs,indent=2,ensure_ascii=False)+'\n')

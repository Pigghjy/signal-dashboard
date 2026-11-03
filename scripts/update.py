        match=re.search(r'https?://[^\s"\'}>]+',line)
        if match and valid_url(match.group()): links.append(match.group())
    return list(dict.fromkeys(links))

def save(name, items, errors):
    obj={'metadata':{'generated_at':NOW.isoformat(),'item_count':len(items),'errors':errors},'items':items}
    path=PUBLIC / name
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{name}: {len(items)} items, {len(errors)} errors')

def fetch_feed(url):
    r=requests.get(url,headers=HEADERS,timeout=18);r.raise_for_status()
    result=feedparser.parse(r.content)
    if not result.entries and result.get('bozo'): raise ValueError('feed unreadable')
    return result.entries

def parse_date(x):
    try:
        d=dateparse.parse(x)
        return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
    except Exception: return None

def ai_score(channel, articles):
    key=os.getenv('OPENAI_API_KEY')
    if not key: return None
    from openai import OpenAI
    client=OpenAI(api_key=key,timeout=30,max_retries=1)
    out={}
    for idx,item in enumerate(articles[:MAX_AI]):
        try:
            guide=('科技：保留 AI 模型/开源/互联网软件产品更新/新创融资/战略合作；过滤普通财报、监管、传统重资产、空泛观点。'
              if channel=='tech' else
              '财经：保留重要宏观政策/经济数据、股票基本面重大变动及有实质的新创融资；过滤纯股价噪音、重复评论、无信息的观点。')
            prompt=f'你是严谨的新闻筛选助手。只根据标题与RSS摘要判断，不要补充任何未给出的事实。{guide}\n输出 JSON object，仅包含 score (0或1)、brief (不超过55字中文)、reason (一句话中文)、category (财经限macro/equity/venture/other)、priority (整数1-3)。信息不足 score 0。\n新闻：'+json.dumps({'title':item['title'],'summary':item['summary']},ensure_ascii=False)
            response=client.chat.completions.create(model=os.getenv('OPENAI_MODEL','gpt-4.1-mini'),messages=[{'role':'user','content':prompt}],response_format={'type':'json_object'},temperature=0)
            d=json.loads(response.choices[0].message.content)
            out[item['item_id']]=d
        except Exception as exc:
            print('AI error:',item['item_id'],str(exc)[:120])
        time.sleep(.12)
    return out

TECH_RE=re.compile(r'\b(ai|agent|llm|model|open.source|startup|funding|launch|release|app|software|developer|anthropic|openai|google|meta|social|robotics|video|generative|coding|product|venture)\b',re.I)
FIN_RE=re.compile(r'\b(rate|fed|inflation|cpi|gdp|jobs|unemployment|merger|acquisition|investment|funding|ipo|earnings|guidance|venture|seed round|series [a-f]|policy|economy)\b',re.I)

def pipeline(channel, files):
    raw={};errors=[];cutoff=NOW-timedelta(days=DAYS)
    for file in files:
        for feed in read_links(file):
            try:
                for entry in fetch_feed(feed)[:MAX_FEED_ITEMS]:
                    link=str(entry.get('link','')).strip()
                    pub=parse_date(entry.get('published') or entry.get('updated') or '')
                    if not valid_url(link) or not pub or not (cutoff<=pub<=NOW+timedelta(minutes=5)): continue
                    iid='news_'+hashlib.sha1((feed+'\n'+link).encode()).hexdigest()[:12]
                    item={'item_id':iid,'source_url':feed,'title':plain(entry.get('title')),'link':link,'pub_date':pub.isoformat(),'summary':plain(entry.get('summary') or entry.get('description')),'channel':channel}
                    raw.setdefault(link,item)
            except Exception as exc:errors.append({'source':feed,'error':str(exc)[:180]})
    candidates=sorted(raw.values(),key=lambda a:a['pub_date'],reverse=True)
    scored=ai_score(channel,candidates)
    result=[]
    for item in candidates:
        a=(scored or {}).get(item['item_id'])
        if a:
            if int(a.get('score',0))!=1:continue
            item['brief']=str(a.get('brief') or item['summary'] or item['title'])
            item['reason']=str(a.get('reason',''))
            item['priority']=max(1,min(3,int(a.get('priority',1))))
            item['category']=str(a.get('category','other')) if channel=='finance' else 'tech'
            item['review_status']='ai_reviewed'
        else:
            text=item['title']+' '+item['summary']
            if not (TECH_RE if channel=='tech' else FIN_RE).search(text):continue
            item['brief']=item['summary'][:190] or item['title']
            item['priority']=1
            item['category']='tech' if channel=='tech' else ('venture' if re.search('funding|venture|seed round|series [a-f]',text,re.I) else 'macro' if re.search('fed|inflation|cpi|gdp|jobs|rate',text,re.I) else 'equity')
            item['review_status']='keyword_only'
        item['score']=1
        item['company']=[]
        item['details']=''  # no article body; do not hallucinate or claim extraction
        result.append(item)
    save('tech_news.json' if channel=='tech' else 'finance_dashboard.json',result,errors)

def discover_skills():
    errors=[];data=[]
    queries=['agent skills in:name,description','tarot astrology agent skill in:name,description','automation skill productivity in:name,description']
    for query in queries:
        try:
            params={'q':query,'sort':'updated','order':'desc','per_page':20}
            r=requests.get('https://api.github.com/search/repositories',params=params,headers={'Accept':'application/vnd.github+json','User-Agent':'SIGNAL-News-Dashboard'},timeout=20)
            r.raise_for_status()
            for repo in r.json().get('items',[]):
                if repo.get('fork') or repo.get('archived') or not repo.get('description') or repo.get('size',0)<5:continue
                url=repo.get('html_url','');name=repo.get('full_name','')
                if not valid_url(url) or repo.get('stargazers_count',0)<3:continue
                if any(x['link']==url for x in data):continue
                license_name=(repo.get('license') or {}).get('spdx_id') or '未确认'
                # Absence of license does not grant an open-source license.
                if license_name in ('NOASSERTION','未确认'):continue
                cat='fun' if re.search('tarot|astrology|horoscope|fortune|divination',name+' '+repo['description'],re.I) else 'work'
                data.append({'item_id':'github_'+hashlib.sha1(url.encode()).hexdigest()[:12], 'source_url':'https://api.github.com/search/repositories','title':name,'link':url,'pub_date':repo.get('pushed_at',''),'company':[repo.get('owner',{}).get('login','')], 'brief':plain(repo['description'])[:240], 'details':f'GitHub 仓库。许可证：{license_name}。Stars：{repo.get("stargazers_count",0)}。最近推送：{repo.get("pushed_at", "未知")}。尚未人工审计源码或验证安装安全性；不保证仓库包含 SKILL.md。', 'category':cat,'channel':'github','license':license_name,'stars':repo.get('stargazers_count',0)})
        except Exception as exc:errors.append({'query':query,'error':str(exc)[:180]})
    # Aim for variety; don't invent items if the API is unavailable.
    fun=[r for r in data if r['category']=='fun'];work=[r for r in data if r['category']=='work']
    picked=(work[:2]+fun[:1])[:3] if fun else work[:3]
    save('github_skills.json',picked,errors)

if __name__=='__main__':
    PUBLIC.mkdir(parents=True,exist_ok=True)
    pipeline('tech',['Link.md'])
    pipeline('finance',['Finance_Link.md'])
    discover_skills()
    (PUBLIC/'status.json').write_text(json.dumps({'generated_at':NOW.isoformat(),'status':'completed'},ensure_ascii=False),encoding='utf-8')

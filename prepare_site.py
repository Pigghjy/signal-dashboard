from pathlib import Path
import re
root=Path(__file__).resolve().parent.parent
src=(root/'dashboard_template.html').read_text(encoding='utf-8')
# Remove historical examples from production build; live data is fetched at startup.
src=re.sub(r'const tech=\[.*?\];\nconst githubSeed=', 'let tech=[];\nconst githubSeed=',src,count=1,flags=re.S)
src=src.replace('let github=[...githubSeed], finance=[]','let github=[], finance=[]')
src=src.replace("$('description').textContent=channel==='tech'?'科技新闻 · 8 条已核实的历史样本（并非 RSS 全量）'", "$('description').textContent=channel==='tech'?'科技新闻 · 自动读取最新 RSS 数据'")
src=src.replace("'财经情报 · 导入 finance_dashboard.json 后显示'", "'财经情报 · 自动读取最新 RSS 数据'")
src=src.replace("'GitHub Skills · 内置 3 个已核实项目入口；每天可导入最新精选 JSON'", "'GitHub Skills · 自动读取最新 GitHub 仓库数据'")
src=src.replace('已内置科技新闻 8 条；财经频道尚未导入数据。','正在加载每日新闻数据…')
src=src.replace('科技新闻 · 已嵌入 8 条历史示例数据','科技新闻 · 自动加载数据')
src=src.replace('财经和 Skills 数据需要手动导入。','数据每日自动更新。')
src=src.replace('财经和 Skills 数据可在网页中导入。','数据每日自动更新。')
src=src.replace('打开项目 ↗','查看原文 ↗')
src=src.replace("const filename=channel==='github'?'github_skills.json':'finance_dashboard.json';", "const filename=channel==='github'?'github_skills.json':channel==='tech'?'tech_news.json':'finance_dashboard.json';")
src=src.replace("(channel==='github'?importGithub:importFinance)(await r.json())", "channel==='tech'?(tech=sourceItems(await r.json()).map(x=>({...x,channel:'tech'})),render()):(channel==='github'?importGithub:importFinance)(await r.json())")
src=src.replace("(channel==='github'?importGithub:importFinance)(JSON.parse(await f.text()))", "channel==='tech'?(tech=sourceItems(JSON.parse(await f.text())).map(x=>({...x,channel:'tech'})),render()):(channel==='github'?importGithub:importFinance)(JSON.parse(await f.text()))")
src=src.replace("render();\n</script>", """render();
(async()=>{
 const specs=[['tech_news.json','tech'],['finance_dashboard.json','finance'],['github_skills.json','github']];
 const errs=[];
 for(const [file,kind] of specs){
   try{
    const r=await fetch('./'+file+'?v='+Date.now(),{cache:'no-store'});
    if(!r.ok)throw Error('HTTP '+r.status);
    const arr=sourceItems(await r.json());
    if(kind==='tech')tech=arr.map(x=>({...x,channel:'tech'}));
    if(kind==='finance')finance=arr.filter(x=>x.score!==0).map(x=>({...x,channel:'finance'}));
    if(kind==='github')github=arr.map(x=>({...x,channel:'github'}));
   }catch(e){errs.push(file+': '+e.message)}
 }
 $('status').textContent=errs.length?'部分数据加载失败：'+errs.join('；'):'数据已自动加载。科技 '+tech.length+' 条 · 财经 '+finance.length+' 条 · GitHub '+github.length+' 个。';
 render();
})();
</script>""")
(root/'public'/'index.html').write_text(src,encoding='utf-8')

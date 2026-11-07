import json,time,tempfile,ctypes,os
from pathlib import Path
from ctypes import wintypes
import sys,argparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pathlib import Path
from src.embedding import get_embeddings
from src.pdf_loader import load_directory
from src.text_splitter import split_documents
from src.rag_chain import answer,retrieval_diagnostics
from src.vector_store import build_store,load_store
from src.utils import ROOT
from langchain_core.documents import Document

class Counters(ctypes.Structure):
    _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage']]
def memory():
    if sys.platform=='win32':
        m=Counters();m.cb=ctypes.sizeof(m)
        assert ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.c_void_p(-1),ctypes.byref(m),m.cb)
        return round(m.WorkingSetSize/1024**2,1),round(m.PeakWorkingSetSize/1024**2,1)
    status=Path('/proc/self/status')
    if status.is_file():
        rows={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in status.read_text().splitlines() if ':' in line}
        return round(int(rows['VmRSS'].split()[0])/1024,1),round(int(rows['VmHWM'].split()[0])/1024,1)
    return None,None
parser=argparse.ArgumentParser(description='Actual multilingual FAISS smoke evaluation; no LLM calls.')
parser.add_argument('--output',type=Path,default=ROOT/'.verification/retrieval-evaluation.json')
args=parser.parse_args()
report={'backend':os.getenv('EMBEDDING_BACKEND','onnx'),'platform':sys.platform,'rss_before_model_mb':memory()[0]};started=time.perf_counter();model=get_embeddings();report['model_load_s']=round(time.perf_counter()-started,2);report['rss_after_model_mb']=memory()[0]
docs,_=load_directory(ROOT/'data');chunks=split_documents(docs)
with tempfile.TemporaryDirectory() as temp:
    start=time.perf_counter();store=build_store(chunks,model,Path(temp)/'base');report['index_s']=round(time.perf_counter()-start,2);report['chunks']=len(chunks);report['rss_after_index_mb']=memory()[0]
    cases=[('졸업인증 총점','AI·빅데이터학과',2022,5,'95점'),('프로그래밍 능력 인증 조건','AI·빅데이터학과',2022,5,'Level2'),('코딩 능력 인증 기준','AI·빅데이터학과',2022,5,'Level2'),('전체 인증 점수','AI·빅데이터학과',2022,5,'95점'),('필수 교과목 기준','AI·빅데이터학과',2022,5,'예비창업설계'),('코딩역량인증제 조건','의료IT공학과',2024,4,'코딩'),('TOPCIT 응시','정보보호학과',2023,3,'TOPCIT'),('학과활동 기준','AI·빅데이터학과',2023,5,'학과활동')]
    results=[]
    for q,d,y,page,term in cases:
        text,hits=answer(q,docs,d,y,store=store)
        results.append({'query':q,'department':d,'year':y,'ok':bool(hits) and all(h.metadata['page']==page and h.metadata.get('department')==d and h.metadata.get('year')==y for h in hits) and term in text,'diagnostics':retrieval_diagnostics(hits,store)})
    _,unknown=answer('졸업하려면 우주여행 자격증 몇점?',docs,'AI·빅데이터학과',2022,store=store);report['unknown_refused']=not unknown
    t=time.perf_counter();answer('졸업인증 총점',docs,'AI·빅데이터학과',2022,store=store);report['warm_repeat_ms']=round((time.perf_counter()-t)*1000,2)
    reloaded=load_store(model,Path(temp)/'base');t,h=answer('코딩역량인증제 조건',docs,'AI·빅데이터학과',2022,store=reloaded);report['reload_ok']=bool(h) and 'Level2' in t
    extra=Document(page_content='AI·빅데이터학과 2022학번 졸업인증 총점 100점',metadata={'source':'synthetic-conflict.pdf','page':1})
    menu=Document(page_content='식당 점심 메뉴 안내',metadata={'source':'unrelated-menu.pdf','page':1})
    multi=build_store(split_documents(docs+[extra,menu]),model,Path(temp)/'multi')
    t,h=answer('졸업인증 총점',docs+[extra,menu],'AI·빅데이터학과',2022,store=multi);report['conflict_preserved']=len(h)==2 and '95점' in t and '100점' in t and '총점 불일치' in t and 'unrelated-menu.pdf' not in t
    report['cases']=results;report['correct']=sum(r['ok'] for r in results);report['rss_end_mb'],report['peak_rss_mb']=memory()
    report['torch_imported']='torch' in sys.modules
    report['all_passed']=all(r['ok'] and r['diagnostics'].get('mode')=='hybrid' for r in results) and report['unknown_refused'] and report['reload_ok'] and report['conflict_preserved']
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False));assert report['all_passed']

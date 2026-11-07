"""Behavioral checks for actual vector use, evidence scope and cache integrity."""
from types import SimpleNamespace
import json
import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from src.rag_chain import retrieve,retrieval_diagnostics,scoped_original,supported
from src.graduation_rules import get_rule
from src.vector_store import build_store,load_store,QueryCachedEmbeddings
from src.text_splitter import split_documents
from src.pdf_loader import load_directory
from src.utils import ROOT

D='AI·빅데이터학과'

class CountingEmbeddings(Embeddings):
    def __init__(self): self.queries=0
    def embed_documents(self,texts): return [[float('코딩' in t),float('졸업인증' in t),1.] for t in texts]
    def embed_query(self,text):
        self.queries+=1
        return [float('코딩' in text),float('졸업인증' in text),1.]


def test_vector_query_is_real_cached_and_scope_safe(tmp_path):
    docs,_=load_directory(ROOT/'data');model=CountingEmbeddings()
    store=build_store(split_documents(docs),model,tmp_path)
    for _ in range(2):
        hits=retrieve('코딩역량인증제 조건',docs,D,2022,store)
        assert hits and all(d.metadata['department']==D and d.metadata['year']==2022 for d in hits)
        assert retrieval_diagnostics(hits,store)['mode']=='hybrid'
        assert hits[0].metadata['vector_rank']>=1 and 'Level2' in hits[0].page_content
    assert model.queries==1  # Second FAISS search reuses only the query vector.
    assert store.index.ntotal>1


def test_unknown_question_still_queries_vector_but_never_uses_nearest_wrong_rule(tmp_path):
    docs,_=load_directory(ROOT/'data');model=CountingEmbeddings()
    store=build_store(split_documents(docs),model,tmp_path)
    assert retrieve('우주여행 자격증',docs,D,2022,store)==[]
    assert model.queries==1
    assert retrieval_diagnostics([],store)['vector_ok'] is True


def test_generic_question_rejects_unrelated_uploaded_page():
    assert not supported('졸업인증 총점','오늘 점심 메뉴는 돈까스입니다.',D,2022)
    assert supported('졸업인증 총점','졸업인증 총점 95점',D,2022)
    docs,_=load_directory(ROOT/'data')
    unrelated=Document(page_content='식당 점심 메뉴 안내',metadata={'source':'menu.pdf','page':1})
    hits=retrieve('졸업인증 총점',docs+[unrelated],D,2022)
    assert hits and all(d.metadata['source']!='menu.pdf' for d in hits)


def test_additional_metadata_cannot_cross_cohort_or_department():
    wrong_year=Document(page_content='졸업인증 총점 100점',metadata={'source':'year.pdf','page':1,'department':D,'year':2023})
    wrong_department=Document(page_content='졸업인증 총점 100점',metadata={'source':'other.pdf','page':1,'department':'정보보호학과','year':2022})
    assert retrieve('졸업인증 총점',[wrong_year,wrong_department],D,2022)==[]


def test_extra_pdf_uses_matching_faiss_chunk_not_whole_page(tmp_path):
    body='무관한 안내. '*600+'\n\nSPECIALPOLICY 졸업인증 총점 100점.\n\n'+'기타 설명. '*600
    page=Document(page_content=body,metadata={'source':'additional.pdf','page':4})
    chunks=split_documents([page]);store=build_store(chunks,CountingEmbeddings(),tmp_path)
    hits=retrieve('SPECIALPOLICY',[page],D,2022,store)
    assert hits and len(hits[0].page_content)<len(body)
    assert hits[0].page_content in body and 'SPECIALPOLICY' in hits[0].page_content
    assert hits[0].metadata['chunk_id'] and hits[0].metadata['start_index']>=0


def test_corrupt_same_count_index_metadata_is_rejected(tmp_path):
    page=Document(page_content='학과활동',metadata={'source':'policy.pdf','page':1})
    model=CountingEmbeddings();build_store([page],model,tmp_path)
    rows=json.loads((tmp_path/'documents.json').read_text(encoding='utf-8'))
    rows[0]['text']='다른 문서로 변조'
    (tmp_path/'documents.json').write_text(json.dumps(rows),encoding='utf-8')
    with pytest.raises(ValueError,match='무결성'): load_store(model,tmp_path)


def test_vector_failure_is_reported_without_exposing_exception_text():
    class Broken:
        index=SimpleNamespace(ntotal=1)
        def similarity_search(self,*a,**kw): raise RuntimeError('secret-like-message-do-not-show')
    docs,_=load_directory(ROOT/'data');store=Broken()
    hits=retrieve('코딩역량인증제',docs,D,2022,store)
    diag=retrieval_diagnostics(hits,store)
    assert hits and diag['mode']=='keyword_fallback' and diag['error_type']=='RuntimeError'
    assert 'secret-like' not in str(diag)


def test_query_cache_is_bounded_and_does_not_retain_raw_questions():
    model=CountingEmbeddings();cached=QueryCachedEmbeddings(model,max_entries=2)
    for question in ['private question A','private question B','private question C']: cached.embed_query(question)
    assert len(cached._queries)==2 and all(isinstance(key,bytes) and len(key)==32 for key in cached._queries)
    assert 'private question' not in repr(cached._queries)

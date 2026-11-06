import os
import faiss
if os.getenv("RUN_EMBEDDING_TEST")=="1":
    import sentence_transformers
import pytest
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from src.vector_store import build_store,load_store
from src.pdf_loader import load_directory
from src.text_splitter import split_documents
from src.rag_chain import answer
from src.utils import ROOT

class FixtureEmbeddings(Embeddings):
    def embed_documents(self,texts): return [self.embed_query(t) for t in texts]
    def embed_query(self,text): return [float('TOPCIT' in text),float('학과활동' in text),1.0]


def test_faiss_save_reload(tmp_path):
    docs=[Document(page_content='TOPCIT 응시',metadata={'source':'test.pdf','page':1}),Document(page_content='학과활동',metadata={'source':'test.pdf','page':2})]
    embedding=FixtureEmbeddings()
    store=build_store(docs,embedding,tmp_path)
    assert store.similarity_search('TOPCIT',k=1)[0].metadata['page']==1
    reloaded=load_store(embedding,tmp_path)
    assert reloaded.similarity_search('학과활동',k=1)[0].metadata['page']==2

@pytest.mark.integration
@pytest.mark.skipif(os.getenv('RUN_EMBEDDING_TEST')!='1',reason='실제 모델 다운로드/로딩은 RUN_EMBEDDING_TEST=1로 실행')
def test_real_multilingual_embedding(tmp_path):
    from src.embedding import get_embeddings
    embeddings=get_embeddings()
    docs,_=load_directory(ROOT/'data')
    chunks=split_documents(docs)
    assert any(d.metadata.get('department')=='AI·빅데이터학과' and d.metadata.get('year')==2022 for d in chunks)
    store=build_store(chunks,embeddings,tmp_path)
    text,hits=answer('2022학번 AI·빅데이터학과 졸업인증 총점',docs,store=store)
    assert hits and all(h.metadata['page']==5 for h in hits)
    assert '95점' in text and '교과 10점' in text
    reloaded=load_store(embeddings,tmp_path)
    assert reloaded.index.ntotal==len(chunks)
    # Synthetic conflicting document exists only in this test, never in data/.
    extra=Document(page_content='AI·빅데이터학과 2022학번 졸업인증 총점 100점',metadata={'source':'synthetic-conflict.pdf','page':1})
    integrated=build_store(chunks+[extra],embeddings,tmp_path/'multi')
    response,evidence=answer('졸업인증 총점',docs+[extra],'AI·빅데이터학과',2022,store=integrated)
    assert len({doc.metadata['source'] for doc in evidence})==2
    assert '95점' in response and '100점' in response and '총점 불일치' in response

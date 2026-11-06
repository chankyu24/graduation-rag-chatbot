from pathlib import Path
from langchain_core.documents import Document
from src.pdf_loader import load_pdf,load_directory
from src.utils import ROOT
from src.rag_chain import answer,retrieve
from src.text_splitter import split_documents
from src.graduation_rules import load_rules

def test_pdf():
 docs=load_pdf(next((ROOT/'data').glob('*.pdf')))
 assert len(docs)==8 and '컴퓨터소프트웨어' in docs[1].page_content
 assert docs[1].metadata['page']==2
 assert all(d.metadata['source'] for d in split_documents(docs))
def test_retrieval_department():
 docs,_=load_directory(ROOT/'data')
 hits=retrieve('TOPCIT 응시',docs,'정보보호학과',2023)
 assert hits and all(h.metadata['page']==3 for h in hits)
def test_missing():
 assert '확인할 수 없' in answer('아무자료',[],'정보보호학과',2023)[0]
 assert '학과와 입학연도' in answer('졸업기준',[])[0]
def test_wrong_department():
 docs,_=load_directory(ROOT/'data')
 assert not retrieve('졸업',docs,'존재하지않는학과',2023)
def test_multi_document_conflict_preserved():
 docs=[Document(page_content='졸업인증 점수 총점 100점',metadata={'source':'a.pdf','page':1}),Document(page_content='졸업인증 점수 총점 200점',metadata={'source':'b.pdf','page':2})]
 text,hits=answer('졸업인증 점수 총점',docs,'정보보호학과',2023)
 assert len(hits)==2 and '100점' in text and '200점' in text and 'a.pdf' in text and 'b.pdf' in text

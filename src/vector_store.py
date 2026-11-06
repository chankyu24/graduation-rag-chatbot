import hashlib
import json
from pathlib import Path


def fingerprint(directory):
    return hashlib.sha256(b''.join(p.name.encode()+p.read_bytes() for p in sorted(Path(directory).glob('*.pdf')))).hexdigest()


def build_store(documents, embeddings, directory):
    if not documents:
        return None
    from langchain_community.vectorstores import FAISS
    import faiss
    store = FAISS.from_documents(documents, embeddings)
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    faiss.write_index(store.index, str(path/'index.faiss'))
    (path/'documents.json').write_text(json.dumps([
        {'text':d.page_content,'metadata':d.metadata} for d in documents], ensure_ascii=False), encoding='utf-8')
    return store


def load_store(embeddings, directory):
    """Reload our FAISS + JSON representation without executing pickle content."""
    import faiss
    from langchain_core.documents import Document
    from langchain_community.vectorstores import FAISS
    from langchain_community.docstore.in_memory import InMemoryDocstore
    path=Path(directory)
    rows=json.loads((path/'documents.json').read_text(encoding='utf-8'))
    docs={str(i):Document(page_content=r['text'],metadata=r['metadata']) for i,r in enumerate(rows)}
    index=faiss.read_index(str(path/'index.faiss'))
    if index.ntotal != len(docs): raise ValueError('인덱스와 문서 개수가 다릅니다. 인덱스를 다시 생성하세요.')
    return FAISS(embeddings,index,InMemoryDocstore(docs),{i:str(i) for i in range(len(docs))})

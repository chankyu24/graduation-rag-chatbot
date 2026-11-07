import hashlib
import json
from pathlib import Path
from collections import OrderedDict
from threading import RLock
from uuid import uuid4
from langchain_core.embeddings import Embeddings

INDEX_SCHEMA=2


class QueryCachedEmbeddings(Embeddings):
    """Bounded per-store LRU; no raw questions are retained by the cache."""
    def __init__(self,embeddings,max_entries=64):
        self.embeddings=embeddings
        self.max_entries=max_entries
        self._queries=OrderedDict()
        self._lock=RLock()

    def embed_documents(self,texts):
        return self.embeddings.embed_documents(texts)

    def embed_query(self,text):
        key=hashlib.sha256(text.encode('utf-8')).digest()
        with self._lock:
            if key in self._queries:
                self._queries.move_to_end(key)
                return list(self._queries[key])
            vector=tuple(self.embeddings.embed_query(text))
            self._queries[key]=vector
            if len(self._queries)>self.max_entries: self._queries.popitem(last=False)
            return list(vector)


def _file_hash(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as file:
        for block in iter(lambda:file.read(1024*1024),b''): digest.update(block)
    return digest.hexdigest()


def fingerprint(directory):
    digest=hashlib.sha256()
    for path in sorted(Path(directory).glob('*.pdf')):
        name=path.name.encode('utf-8')
        digest.update(len(name).to_bytes(8,'big'));digest.update(name)
        digest.update(bytes.fromhex(_file_hash(path)))
    return digest.hexdigest()


def build_store(documents, embeddings, directory):
    if not documents:
        return None
    from langchain_community.vectorstores import FAISS
    import faiss
    faiss.omp_set_num_threads(1)
    store = FAISS.from_documents(documents, QueryCachedEmbeddings(embeddings))
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    suffix='.'+uuid4().hex+'.tmp'
    index_temp=path/('index.faiss'+suffix)
    docs_temp=path/('documents.json'+suffix)
    manifest_temp=path/('manifest.json'+suffix)
    faiss.write_index(store.index, str(index_temp))
    docs_temp.write_text(json.dumps([
        {'text':d.page_content,'metadata':d.metadata} for d in documents], ensure_ascii=False), encoding='utf-8')
    manifest_temp.write_text(json.dumps({'schema':INDEX_SCHEMA,'count':store.index.ntotal,'dimension':store.index.d,
        'index_sha256':_file_hash(index_temp),'documents_sha256':_file_hash(docs_temp)}),encoding='utf-8')
    # Manifest last: interrupted writes trigger a rebuild, not mixed evidence.
    index_temp.replace(path/'index.faiss')
    docs_temp.replace(path/'documents.json')
    manifest_temp.replace(path/'manifest.json')
    return store


def load_store(embeddings, directory):
    """Reload our FAISS + JSON representation without executing pickle content."""
    import faiss
    from langchain_core.documents import Document
    from langchain_community.vectorstores import FAISS
    from langchain_community.docstore.in_memory import InMemoryDocstore
    path=Path(directory)
    try:
        manifest=json.loads((path/'manifest.json').read_text(encoding='utf-8'))
        if manifest.get('schema')!=INDEX_SCHEMA or manifest.get('index_sha256')!=_file_hash(path/'index.faiss') or manifest.get('documents_sha256')!=_file_hash(path/'documents.json'):
            raise ValueError('인덱스 무결성 검사 실패. 인덱스를 다시 생성하세요.')
    except (OSError,json.JSONDecodeError) as exc:
        raise ValueError('인덱스 파일이 불완전하거나 이전 형식입니다. 인덱스를 다시 생성하세요.') from exc
    rows=json.loads((path/'documents.json').read_text(encoding='utf-8'))
    docs={str(i):Document(page_content=r['text'],metadata=r['metadata']) for i,r in enumerate(rows)}
    index=faiss.read_index(str(path/'index.faiss'))
    faiss.omp_set_num_threads(1)
    if index.ntotal != len(docs) or index.ntotal!=manifest.get('count') or index.d!=manifest.get('dimension'):
        raise ValueError('인덱스와 문서 개수/차원이 다릅니다. 인덱스를 다시 생성하세요.')
    return FAISS(QueryCachedEmbeddings(embeddings),index,InMemoryDocstore(docs),{i:str(i) for i in range(len(docs))})

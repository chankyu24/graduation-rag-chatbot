"""One CPU model factory; the application owns model/resource caching."""
import os
from threading import RLock
from langchain_core.embeddings import Embeddings

DEFAULT_MODEL='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'


class CPUBoundedEmbeddings(Embeddings):
    """Serialize shared encoding to bound concurrent working memory."""
    def __init__(self,model):
        self.model=model
        self._encode_lock=RLock()

    def embed_documents(self,texts):
        with self._encode_lock: return self.model.embed_documents(texts)

    def embed_query(self,text):
        with self._encode_lock: return self.model.embed_query(text)


def get_embeddings(model_name=None):
    # Configure conservative defaults before tokenizer / PyTorch imports.
    for variable in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):
        os.environ.setdefault(variable,'1')
    os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
    selected=model_name or os.getenv('EMBEDDING_MODEL',DEFAULT_MODEL)
    if selected==DEFAULT_MODEL and os.getenv('EMBEDDING_BACKEND','onnx')=='onnx':
        from .embedding_onnx import QuantizedMultilingualEmbeddings
        return CPUBoundedEmbeddings(QuantizedMultilingualEmbeddings())
    from langchain_huggingface import HuggingFaceEmbeddings
    model=HuggingFaceEmbeddings(
        model_name=selected,
        model_kwargs={'device':'cpu'},
        encode_kwargs={'normalize_embeddings':True,'batch_size':8},
    )
    return CPUBoundedEmbeddings(model)

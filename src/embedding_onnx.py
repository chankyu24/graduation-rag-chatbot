"""Pinned multilingual MiniLM int8 inference without importing PyTorch."""
import json
from threading import RLock
import numpy as np
from langchain_core.embeddings import Embeddings

MODEL='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
REVISION='e8f8c211226b894fcb81acc59f3b34ba3efd5f42'
FILES=('onnx/model_quint8_avx2.onnx','tokenizer.json','tokenizer_config.json','sentence_bert_config.json')


def prepare_model():
    from huggingface_hub import hf_hub_download
    return {name:hf_hub_download(MODEL,name,revision=REVISION) for name in FILES}


class QuantizedMultilingualEmbeddings(Embeddings):
    def __init__(self):
        import onnxruntime as ort
        from tokenizers import Tokenizer
        paths=prepare_model()
        self.tokenizer=Tokenizer.from_file(paths['tokenizer.json'])
        with open(paths['tokenizer_config.json'],encoding='utf8') as f: config=json.load(f)
        with open(paths['sentence_bert_config.json'],encoding='utf8') as f: settings=json.load(f)
        pad=config.get('pad_token','<pad>')
        if isinstance(pad,dict): pad=pad['content']
        pad_id=self.tokenizer.token_to_id(pad)
        if pad_id is None: raise ValueError('Tokenizer padding token unavailable')
        self.tokenizer.enable_truncation(max_length=min(128,settings.get('max_seq_length',128)))
        self.tokenizer.enable_padding(pad_id=pad_id,pad_token=pad)
        options=ort.SessionOptions()
        options.intra_op_num_threads=1;options.inter_op_num_threads=1
        options.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
        options.enable_cpu_mem_arena=False
        self.session=ort.InferenceSession(paths[FILES[0]],sess_options=options,providers=['CPUExecutionProvider'])
        self.input_names={i.name for i in self.session.get_inputs()}
        self._lock=RLock()

    def embed_documents(self,texts):
        vectors=[]
        with self._lock:
            for start in range(0,len(texts),4):
                encoded=self.tokenizer.encode_batch(list(texts[start:start+4]))
                ids=np.asarray([e.ids for e in encoded],dtype=np.int64)
                mask=np.asarray([e.attention_mask for e in encoded],dtype=np.int64)
                inputs={'input_ids':ids,'attention_mask':mask,
                        'token_type_ids':np.asarray([e.type_ids for e in encoded],dtype=np.int64)}
                output=self.session.run(None,{k:v for k,v in inputs.items() if k in self.input_names})[0]
                if output.ndim==3:
                    weights=mask[...,None].astype(np.float32)
                    output=(output*weights).sum(axis=1)/np.maximum(weights.sum(axis=1),1e-9)
                output=np.asarray(output,dtype=np.float32)
                output/=np.maximum(np.linalg.norm(output,axis=1,keepdims=True),1e-12)
                vectors.extend(output.tolist())
        return vectors

    def embed_query(self,text):
        return self.embed_documents([text])[0]

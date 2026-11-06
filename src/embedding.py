import os
def get_embeddings():
 from langchain_huggingface import HuggingFaceEmbeddings
 return HuggingFaceEmbeddings(model_name=os.getenv('EMBEDDING_MODEL','sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'),model_kwargs={'device':'cpu'},encode_kwargs={'normalize_embeddings':True})

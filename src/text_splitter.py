"""Split general PDFs and retain verified table rows as coherent cohort documents."""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .graduation_rules import load_rules
from hashlib import sha256


def split_documents(documents):
    from .rag_chain import scoped_original
    rules = load_rules()
    original = rules['source']
    splitter = RecursiveCharacterTextSplitter(chunk_size=1400, chunk_overlap=250, add_start_index=True,separators=['\n\n','\n',' ',''])
    chunks = []
    seen = set()
    for doc in documents:
        if doc.metadata['source'] == original:
            for rule in rules['profiles']:
                if rule['page'] != doc.metadata['page']: continue
                for year in range(rule['years'][0], rule['years'][1]+1):
                    key = (rule['department'], year)
                    if key in seen: continue
                    seen.add(key)
                    row = scoped_original(rule, year)
                    row.metadata.update(year_min=year, year_max=year, section='대학공통 및 학과기준', verified_table=True)
                    # Keep the complete table row together even if over the generic chunk size.
                    chunks.append(row)
        else:
            chunks.extend(splitter.split_documents([doc]))
    for chunk in chunks:
        identity=f"{chunk.metadata.get('source')}|{chunk.metadata.get('page')}|{chunk.metadata.get('department')}|{chunk.metadata.get('year')}|{chunk.page_content}"
        chunk.metadata['chunk_id']=sha256(identity.encode('utf-8')).hexdigest()[:20]
    return chunks

from pathlib import Path
import fitz
from langchain_core.documents import Document
def load_pdf(path):
 with fitz.open(path) as pdf:
  if pdf.needs_pass: raise ValueError('암호화 PDF 미지원')
  return [Document(page_content=p.get_text(sort=True),metadata={'source':Path(path).name,'page':i+1}) for i,p in enumerate(pdf) if p.get_text().strip()]
def load_directory(directory):
 docs=[]; errors={}
 for p in sorted(Path(directory).glob('*.pdf')):
  try:
   pages=load_pdf(p)
   if not pages: errors[p.name]='텍스트 없음: OCR 필요'
   docs.extend(pages)
  except Exception as e: errors[p.name]=str(e)
 return docs,errors

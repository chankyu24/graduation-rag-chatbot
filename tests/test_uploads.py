import fitz
import pytest
from src.document_manager import save_pdf
from src.pdf_loader import load_directory
from src.rag_chain import answer
from src.utils import read_courses

def make_pdf(text):
    with fitz.open() as pdf:
        page=pdf.new_page()
        page.insert_text((40,60),text)
        return pdf.tobytes()

def test_upload_and_search(tmp_path):
    raw=make_pdf('SPECIALPOLICY: scholarship support 123 credits.')
    path=save_pdf(raw,'../../extra.pdf',tmp_path)
    assert path.parent==tmp_path
    assert save_pdf(raw,'same.pdf',tmp_path)==path
    docs,errors=load_directory(tmp_path)
    assert not errors and len(docs)==1
    text,hits=answer('SPECIALPOLICY',docs,'AI·빅데이터학과',2022)
    assert hits and '123' in text and path.name in text

def test_bad_upload(tmp_path):
    with pytest.raises(ValueError): save_pdf(b'not pdf','broken.pdf',tmp_path)
    assert not list(tmp_path.iterdir())
    with pytest.raises(ValueError): save_pdf(make_pdf('x'),'bad.txt',tmp_path)

def test_empty_scan(tmp_path):
    with fitz.open() as p:
        p.new_page(); raw=p.tobytes()
    with pytest.raises(ValueError,match='OCR'): save_pdf(raw,'scan.pdf',tmp_path)

def test_csv_bad_header():
    with pytest.raises(ValueError): read_courses('과목명,학점\n전공,3'.encode())
    with pytest.raises(ValueError): read_courses(b'')

def test_csv_cp949():
    assert read_courses('과목명,이수 여부,학점,성적\n예비창업설계,이수,3,A0\n'.encode('cp949'))==['예비창업설계']

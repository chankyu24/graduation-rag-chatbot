from hashlib import sha256
from types import SimpleNamespace

import fitz
import pytest

from src.graduation_rules import load_rules
from src.source_viewer import available_pdf_sources,resolve_pdf_source,source_page_asset
from src.utils import ROOT


def test_original_page5_preview_extracts_same_source_without_changing_pdf():
    path=ROOT/'data'/load_rules()['source']
    before=sha256(path.read_bytes()).hexdigest()
    asset=source_page_asset(path,5)
    assert asset['preview'].startswith(b'\x89PNG\r\n\x1a\n')
    with fitz.open(path) as original,fitz.open(stream=asset['page_pdf'],filetype='pdf') as excerpt:
        assert len(original)==8 and len(excerpt)==1
        assert excerpt[0].get_text()==original[4].get_text()
        assert '예비창업설계' in excerpt[0].get_text() and '95' in excerpt[0].get_text()
    assert sha256(path.read_bytes()).hexdigest()==before


@pytest.mark.parametrize('name',['../secret.pdf','..\\secret.pdf','/secret.pdf','C:\\secret.pdf','https://example.com/a.pdf','not-a-pdf.txt'])
def test_source_paths_cannot_escape_allowed_folders(tmp_path,name):
    assert resolve_pdf_source(name,[tmp_path]) is None


def test_only_present_pdf_citations_with_valid_page_metadata_are_available(tmp_path):
    (tmp_path/'one.pdf').write_bytes(b'%PDF-fixture-name-only')
    def doc(source,page):return SimpleNamespace(metadata={'source':source,'page':page})
    entries=available_pdf_sources([doc('one.pdf',1),doc('one.pdf',1),doc('missing.pdf',1),doc('one.pdf',True),doc('one.pdf',0),doc('one.pdf','1')],[tmp_path])
    assert [(entry['source'],entry['page']) for entry in entries]==[('one.pdf',1)]
    assert available_pdf_sources([doc('one.pdf',1)],[])==[]


@pytest.mark.parametrize('page',[0,True,9,'5'])
def test_page_preview_rejects_invalid_or_out_of_bounds_page(page):
    with pytest.raises(ValueError):source_page_asset(ROOT/'data'/load_rules()['source'],page)

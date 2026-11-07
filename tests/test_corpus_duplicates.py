"""Do not expose a renamed copy of the supplied multi-cohort PDF as new evidence."""
from pathlib import Path,PurePosixPath
import fitz

from src.document_manager import load_corpus, save_pdf
from src.graduation_rules import load_rules
from src.rag_chain import answer
from src.utils import ROOT


def pdf_bytes(text):
    with fitz.open() as pdf:
        pdf.new_page().insert_text((40, 60), text)
        return pdf.tobytes()


def test_common_pdf_wins_over_renamed_private_copy(tmp_path):
    base = tmp_path / 'base'; base.mkdir()
    private = tmp_path / 'private'; private.mkdir()
    raw = pdf_bytes('COMMON_POLICY')
    (base / 'official.pdf').write_bytes(raw)
    (private / 'a-renamed-copy.pdf').write_bytes(raw)
    docs, errors = load_corpus(base, private)
    assert not errors and len(docs) == 1
    assert docs[0].metadata == {'source': 'official.pdf', 'page': 1}


def test_real_source_copy_does_not_bypass_cohort_scoping(tmp_path):
    source = ROOT / 'data' / load_rules()['source']
    renamed = save_pdf(source.read_bytes(), 'renamed-graduation.pdf', tmp_path)
    docs, errors = load_corpus(ROOT / 'data', tmp_path)
    assert not errors and len(docs) == 8
    assert all(doc.metadata['source'] == source.name for doc in docs)
    text, hits = answer('졸업인증 총점', docs, 'AI·빅데이터학과', 2022)
    assert hits and all(doc.metadata['page'] == 5 for doc in hits)
    assert '교과 10점' in text and '95점' in text
    assert renamed.name not in text


def test_byte_distinct_documents_and_private_scope_are_preserved(tmp_path):
    base = tmp_path / 'base'; base.mkdir()
    private = tmp_path / 'private'; private.mkdir()
    other = tmp_path / 'other'; other.mkdir()
    common = pdf_bytes('SAME_WORDS')
    extra = pdf_bytes('SAME_WORDS')
    assert common != extra  # Distinct PDF metadata; do not deduplicate by text.
    (base / 'official.pdf').write_bytes(common)
    (private / 'extra.pdf').write_bytes(extra)
    assert len(load_corpus(base, private)[0]) == 2
    assert len(load_corpus(base, private, include_uploads=False)[0]) == 1
    assert len(load_corpus(base, other)[0]) == 1


def test_private_duplicates_are_collapsed_but_bad_files_still_reported(tmp_path):
    base = tmp_path / 'base'; base.mkdir()
    private = tmp_path / 'private'; private.mkdir()
    raw = pdf_bytes('PRIVATE_POLICY')
    (private / 'a.pdf').write_bytes(raw)
    (private / 'b.pdf').write_bytes(raw)
    (private / 'broken.pdf').write_bytes(b'not a PDF')
    with fitz.open() as pdf:
        pdf.new_page()
        (private / 'scan.pdf').write_bytes(pdf.tobytes())
    docs, errors = load_corpus(base, private)
    assert len(docs) == 1 and docs[0].metadata['source'] == 'a.pdf'
    assert errors['broken.pdf'] and 'OCR' in errors['scan.pdf']


def test_uppercase_pdf_upload_is_discoverable_on_linux_and_reused(tmp_path):
    base=tmp_path/'base';base.mkdir()
    private=tmp_path/'private'
    raw=pdf_bytes('SYNTHETIC_UPPERCASE_UPLOAD_PROBE')
    stored=save_pdf(raw,'UPPERCASE.PDF',private)
    # Posix glob behavior is case-sensitive even when this regression runs on Windows.
    assert PurePosixPath(stored.name).match('*.pdf')
    assert save_pdf(raw,'renamed.PdF',private)==stored
    assert len(list(private.iterdir()))==1
    docs,errors=load_corpus(base,private)
    assert not errors and len(docs)==1 and docs[0].metadata['source']==stored.name
    text,hits=answer('SYNTHETIC_UPPERCASE_UPLOAD_PROBE',docs,'AI·빅데이터학과',2022)
    assert hits and 'SYNTHETIC_UPPERCASE_UPLOAD_PROBE' in text and stored.name in text

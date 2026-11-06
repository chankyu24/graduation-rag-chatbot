"""Validate before writing so failed uploads never replace registered documents."""
from hashlib import sha256
from pathlib import Path
import fitz


def private_document_directory(account_id):
    """Keep uploads outside the common corpus and use no raw student ID in paths."""
    from .auth import database_path
    if not isinstance(account_id, str) or not account_id:
        raise ValueError('로그인한 계정이 필요합니다.')
    return database_path().parent / 'documents' / sha256(account_id.encode('utf-8')).hexdigest()


def load_corpus(base_directory, private_directory, include_uploads=True):
    from .pdf_loader import load_directory
    docs, errors = load_directory(base_directory)
    if include_uploads:
        private_docs, private_errors = load_directory(private_directory)
        docs += private_docs
        errors.update(private_errors)
    return docs, errors


def save_pdf(raw, filename, directory):
    if not raw or len(raw) > 30 * 1024 * 1024:
        raise ValueError('PDF는 0바이트 초과 30MB 이하여야 합니다.')
    safe = Path(filename.replace('\\', '/')).name
    if not safe or Path(safe).suffix.lower() != '.pdf':
        raise ValueError('PDF 확장자가 필요합니다.')
    try:
        with fitz.open(stream=raw, filetype='pdf') as pdf:
            if pdf.needs_pass:
                raise ValueError('암호화된 PDF는 지원하지 않습니다.')
            if not any(p.get_text().strip() for p in pdf):
                raise ValueError('추출 가능한 텍스트가 없습니다. OCR 처리 후 등록하세요.')
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError('PDF를 읽을 수 없습니다. 파일 손상 여부를 확인하세요.') from exc
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    digest = sha256(raw).hexdigest()
    for existing in directory.glob('*.pdf'):
        if sha256(existing.read_bytes()).hexdigest() == digest:
            return existing
    target = directory / (digest[:10] + '_' + safe)
    target.write_bytes(raw)
    return target

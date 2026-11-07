"""Open cited PDF pages from the current session's explicitly allowed folders.

Previews are rendered locally with PyMuPDF. No external viewer, URL fetching,
global document cache or additional PDF-viewer package is used.
"""
from hashlib import sha256
from pathlib import Path

import fitz


def _say(lang, ko, en, zh, ja):
    return {'ko':ko, 'en':en, 'zh':zh, 'ja':ja}.get(lang, ko)


def resolve_pdf_source(source, allowed_directories):
    """Resolve a basename only; reject traversal and links outside allowed folders."""
    if not isinstance(source,str) or not source or '/' in source or '\\' in source:
        return None
    if Path(source).name!=source or Path(source).suffix.lower()!='.pdf':
        return None
    for directory in allowed_directories:
        try:
            base=Path(directory).resolve(strict=True)
            candidate=(base/source).resolve(strict=True)
            if base.is_dir() and candidate.parent==base and candidate.is_file():
                return candidate
        except (OSError,ValueError):
            continue
    return None


def available_pdf_sources(documents, allowed_directories):
    """Return unique real PDF citations; callers must pass their scoped hits."""
    entries=[];seen=set()
    for document in documents:
        metadata=getattr(document,'metadata',{})
        source=metadata.get('source');page=metadata.get('page')
        if not isinstance(source,str) or type(page) is not int or page<1 or (source,page) in seen:
            continue
        path=resolve_pdf_source(source,allowed_directories)
        if path is None:
            continue
        token=sha256((str(path)+'\0'+str(page)).encode('utf8')).hexdigest()[:20]
        entries.append({'source':source,'page':page,'path':path,'token':token})
        seen.add((source,page))
    return entries


def source_page_asset(path, page):
    """Extract the original 1-based page and a bounded PNG without altering it."""
    if type(page) is not int or page<1:
        raise ValueError('Invalid PDF page')
    with fitz.open(path) as original:
        if original.needs_pass or page>len(original):
            raise ValueError('Unavailable PDF page')
        selected=original[page-1]
        longest=max(selected.rect.width,selected.rect.height)
        if longest<=0:
            raise ValueError('Invalid PDF page dimensions')
        scale=min(1.5,1200/longest)
        preview=selected.get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False).tobytes('png')
        with fitz.open() as excerpt:
            excerpt.insert_pdf(original,from_page=page-1,to_page=page-1)
            page_pdf=excerpt.tobytes(garbage=4,deflate=True)
    return {'preview':preview,'page_pdf':page_pdf}


def render_pdf_sources(raw_st, documents, allowed_directories, key_prefix, lang='ko'):
    """Show per-citation page buttons; render bytes only after an explicit click.

    Use a message-specific key_prefix. Pass only the active corpus's PDF folder
    in PDF-only mode, or that folder plus this user's upload folder otherwise.
    """
    entries=available_pdf_sources(documents,allowed_directories)
    if not entries:
        return
    selected_key=key_prefix+'_selected_pdf_page'
    with raw_st.expander(_say(lang,'출처 PDF 페이지 확인','Inspect cited PDF pages','查看引用PDF页面','出典PDFのページを確認'),expanded=bool(raw_st.session_state.get(selected_key))):
        for entry in entries:
            source,page,token=entry['source'],entry['page'],entry['token']
            raw_st.caption(f'{source} · p.{page}')
            raw_st.button(_say(lang,f'원문 p.{page} 열기',f'Open original p.{page}',f'打开原文第{page}页',f'原文p.{page}を開く'),key=key_prefix+'_'+token,
                          on_click=raw_st.session_state.__setitem__,args=(selected_key,token))
            if raw_st.session_state.get(selected_key)!=token:
                continue
            try:
                asset=source_page_asset(entry['path'],page)
                original_bytes=entry['path'].read_bytes()
            except (OSError,ValueError,RuntimeError):
                raw_st.warning(_say(lang,'해당 원문 페이지를 열 수 없습니다. 문서를 다시 등록하거나 페이지 번호를 확인하세요.','Unable to open this source page. Re-register the document or check its page number.','无法打开此原文页面，请重新登记文档或确认页码。','原文ページを開けません。資料を再登録するかページ番号を確認してください。'))
                continue
            raw_st.caption(_say(lang,f'아래는 원본 PDF의 {page}쪽 실제 화면입니다. 한 페이지 다운로드는 이 원문 페이지를 추출한 파일입니다.',f'This is original PDF page {page}. The one-page download extracts this page from the source.',f'下方显示原始PDF的第{page}页。单页下载文件由原文该页提取。',f'原本PDFの{page}ページです。1ページのダウンロードは原本の該当ページを抽出したものです。'))
            raw_st.download_button(_say(lang,'이 페이지 PDF 다운로드','Download this page as PDF','下载此页PDF','このページのPDFをダウンロード'),asset['page_pdf'],file_name=f'{Path(source).stem}_p{page}.pdf',mime='application/pdf',key=key_prefix+'_'+token+'_page',on_click='ignore')
            raw_st.download_button(_say(lang,'원본 PDF 전체 다운로드','Download complete original PDF','下载完整原始PDF','原本PDF全体をダウンロード'),original_bytes,file_name=source,mime='application/pdf',key=key_prefix+'_'+token+'_full',on_click='ignore')
            raw_st.image(asset['preview'],caption=f'{source} · p.{page}',width='stretch')

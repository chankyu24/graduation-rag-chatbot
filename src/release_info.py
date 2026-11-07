"""Identify the executable data and source independently of generated reports."""
import hashlib
import json
import os
import re
from pathlib import Path
from .utils import ROOT


def runtime_files(root=ROOT):
    root=Path(root)
    paths=[root/'app.py',root/'deploy.py',root/'requirements.txt']
    for folder,pattern in [('src','*.py'),('rules','*.json'),('references','*.json'),('data','*.pdf'),('.streamlit','*.toml')]:
        paths.extend((root/folder).rglob(pattern))
    return sorted((p for p in paths if p.is_file()),key=lambda p:p.relative_to(root).as_posix())


def release_info(root=ROOT):
    root=Path(root); digest=hashlib.sha256(); files={}
    for path in runtime_files(root):
        name=path.relative_to(root).as_posix()
        file_hash=hashlib.sha256(path.read_bytes()).hexdigest()
        files[name]=file_hash
        digest.update((name+'\0'+file_hash+'\n').encode('utf8'))
    commit=os.getenv('RAILWAY_GIT_COMMIT_SHA','')
    if not commit:
        try:
            saved=json.loads((root/'SOURCE_VERSION.json').read_text(encoding='utf8'))
            if saved.get('runtime_sha256')==digest.hexdigest(): commit=saved.get('source_commit','')
        except (OSError,ValueError,TypeError): pass
    return {'source_commit':commit if re.fullmatch('[0-9a-f]{40}',commit or '') else None,
            'runtime_sha256':digest.hexdigest(),'runtime_files':files}

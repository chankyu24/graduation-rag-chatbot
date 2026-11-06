import csv
import io
import unicodedata
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def normalize(s):
    return ''.join(unicodedata.normalize('NFC', str(s)).split())

def read_courses(raw):
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError('CSV는 5MB 이하여야 합니다.')
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            text = raw.decode('cp949')
        except UnicodeDecodeError as exc:
            raise ValueError('CSV를 UTF-8 또는 CP949로 저장해 주세요.') from exc
    courses = []
    try:
        reader = csv.reader(io.StringIO(text, newline=''), strict=True)
        fields = next(reader, [])
        headers = [normalize(h) for h in fields]
        if not {'과목명', '이수여부'} <= set(headers):
            raise ValueError('CSV에 과목명, 이수여부 열이 필요합니다.')
        if len(headers) != len(set(headers)) or any(not h for h in headers):
            raise ValueError('CSV 열 이름은 비어 있거나 중복될 수 없습니다. 띄어쓰기만 다른 열도 중복입니다.')
        for cells in reader:
            if not cells or not any(cell.strip() for cell in cells): continue
            line = reader.line_num
            if len(cells) != len(headers):
                raise ValueError(f'{line}행: CSV 열 수가 일치하지 않습니다.')
            row = dict(zip(headers, (v.strip() for v in cells)))
            passed = normalize(row.get('이수여부', '')).lower()
            if passed not in {'true','1','y','이수','예','완료','false','0','n','미이수','아니오',''}:
                raise ValueError(f'{line}행: 이수여부 값 {passed!r}을 확인하세요.')
            if passed in {'true','1','y','이수','예','완료'} and normalize(row.get('성적','')).upper() not in {'F','NP','U'}:
                if not row['과목명']:
                    raise ValueError(f'{line}행: 과목명이 비어 있습니다.')
                courses.append(row['과목명'])
    except csv.Error as exc:
        raise ValueError('CSV 따옴표 또는 행 형식이 올바르지 않습니다. CSV 형식으로 다시 저장해 주세요.') from exc
    return list(dict.fromkeys(courses))


def read_course_file(raw, filename):
    """Read CSV/XLSX with pandas, preserving explicit completion semantics."""
    if Path(filename).suffix.lower() == '.csv':
        return read_courses(raw)
    if Path(filename).suffix.lower() != '.xlsx':
        raise ValueError('CSV 또는 XLSX 파일만 지원합니다.')
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError('XLSX는 5MB 이하여야 합니다.')
    import zipfile
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            if sum(info.file_size for info in archive.infolist()) > 50 * 1024 * 1024:
                raise ValueError('압축 해제 크기가 너무 큰 XLSX입니다.')
        import pandas as pd
        # Preserve the actual first row. pandas' default header handling renames
        # duplicate/blank columns, hiding invalid files from read_courses().
        frame = pd.read_excel(io.BytesIO(raw), engine='openpyxl', header=None, dtype=str, keep_default_na=False)
        return read_courses(frame.to_csv(index=False, header=False).encode('utf-8-sig'))
    except ImportError as exc:
        raise ValueError('XLSX 처리에는 openpyxl과 pandas 설치가 필요합니다.') from exc
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError('XLSX 파일을 읽을 수 없습니다. 첫 시트의 양식과 파일 손상을 확인하세요.') from exc

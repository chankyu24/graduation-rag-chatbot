"""Reviewed public website facts, separate from the PDF-only corpus."""
import json
from langchain_core.documents import Document
from .utils import ROOT


def guide_data():
    return json.loads((ROOT/'references/department_guide.json').read_text(encoding='utf-8'))


def guide_documents():
    data=guide_data()
    docs=[]
    def add(text,url,page=0):
        docs.append(Document(page_content=data['department']+'\n'+text+'\n'+data['scope_note'],metadata={'source':url,'page':page,'kind':'website','department':data['department'],'checked_at':data['checked_at']}))
    office=data['office']
    add(f"학과사무실 연락처 전화번호: {office['telephone']}\n학과사무실 위치: {office['location']}",data['homepage'])
    for year,rows in data['curriculum'].items():
        add(f'{year}학년 교육과정 / 배우는 과목 / 수업 안내\n'+'\n'.join(f'{course}: {credits}학점' for course,credits in rows),data['curriculum_url'],int(year))
    return docs

"""Generate explicitly synthetic review files using the app's dependencies.

Run from the project root: python examples/generate_demo_files.py
No real student record or new university graduation rule is included.
"""
import csv
from pathlib import Path

import fitz
from openpyxl import Workbook
from openpyxl.styles import Alignment,Font,PatternFill


ROOT=Path(__file__).resolve().parent
HEADERS=['과목명','이수 학기','취득 학점','이수 여부','성적','교과 영역']
ROWS=[
    ['예비창업설계','2026-1',3,'이수','P','전공'],
    ['예비창업설계','2026-1',3,'이수','P','전공'],
    ['합성시연_미이수과목','2026-2',3,'미이수','','전공'],
    ['합성시연_낙제과목','2026-1',0,'이수','F','전공'],
]


def generate():
    ROOT.mkdir(parents=True,exist_ok=True)
    with (ROOT/'synthetic_courses.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(HEADERS);writer.writerows(ROWS)
    book=Workbook();sheet=book.active;sheet.title='합성_수강목록'
    sheet.append(HEADERS)
    for row in ROWS:sheet.append(row)
    for cell in sheet[1]:
        cell.fill=PatternFill('solid',fgColor='142B43')
        cell.font=Font(bold=True,color='FFFFFF')
        cell.alignment=Alignment(horizontal='center')
    for col,width in [('A',30),('B',17),('C',15),('D',17),('E',12),('F',17)]:sheet.column_dimensions[col].width=width
    sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    book.properties.title='합성 수강 목록 - 실제 학생 기록 아님'
    book.properties.creator='Graduation chatbot synthetic review fixture'
    book.save(ROOT/'synthetic_courses.xlsx')
    with fitz.open() as document:
        page=document.new_page(width=595,height=842)
        page.draw_rect(fitz.Rect(0,0,595,132),color=None,fill=(.08,.17,.26))
        page.insert_text((40,47),'합성 시연 자료',fontname='korea',fontsize=24,color=(1,1,1))
        page.insert_text((40,81),'실제 학교 규정이 아닙니다',fontname='korea',fontsize=16,color=(1,1,1))
        lines=[
            '이 파일은 다중 PDF 검색을 확인하는 과제용 가상 자료입니다.',
            '순천향대학교 공식 문서나 실제 학생의 이수 기록이 아닙니다.',
            '',
            '시연자료 확인코드: SCH_DEMO8391',
            '',
            '이 자료는 졸업인증 점수나 필수 조건을 추가하거나 변경하지 않습니다.',
            '확인코드는 학사 규정과 무관한 합성 문자열입니다.',
            '',
            '확인 방법',
            '1. 다중 문서 RAG에서 이 PDF를 업로드하고 등록합니다.',
            "2. '시연자료 확인코드 알려줘'라고 질문합니다.",
            '3. 답변의 SCH_DEMO8391, 파일명과 p.1 출처를 확인합니다.',
            '4. PDF 단독 RAG로 바꾸면 이 파일이 검색되지 않아야 합니다.',
            '',
            '원본 다면적 졸업인증제 PDF는 별도로 유지됩니다.',
        ]
        y=170
        for line in lines:
            if line:page.insert_text((40,y),line,fontname='korea',fontsize=11,color=(.10,.18,.25))
            y+=25
        page.draw_line((40,770),(555,770),color=(.78,.83,.82))
        page.insert_text((40,790),'SYNTHETIC DEMO ONLY - NOT A UNIVERSITY POLICY',fontsize=9,color=(.30,.38,.42))
        document.set_metadata({'title':'Synthetic demonstration only - not a university policy','author':'Synthetic fixture generator','subject':'Multi-document retrieval demonstration'})
        document.save(ROOT/'synthetic_extra_document.pdf',garbage=4,deflate=True)
    print('Generated synthetic_courses.csv, synthetic_courses.xlsx and synthetic_extra_document.pdf.')


if __name__=='__main__':generate()

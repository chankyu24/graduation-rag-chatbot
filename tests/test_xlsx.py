import io
import pandas as pd
import pytest
from src.utils import read_course_file


def test_xlsx_completed_not_enrolled():
    frame=pd.DataFrame([
        {'과목명':'예비창업설계','이수 학기':'2024-2','취득 학점':3,'이수 여부':'이수','성적':'A0','교과 영역':'전공'},
        {'과목명':'예비창업설계','이수 여부':'이수','성적':'A0'},
        {'과목명':'신청과목','이수 여부':'미이수'},
        {'과목명':'실패과목','이수 여부':'이수','성적':'F'},
    ])
    out=io.BytesIO(); frame.to_excel(out,index=False)
    assert read_course_file(out.getvalue(),'courses.xlsx')==['예비창업설계']

def test_xlsx_bad():
    with pytest.raises(ValueError): read_course_file(b'broken','courses.xlsx')
    with pytest.raises(ValueError): read_course_file(b'broken','courses.xls')

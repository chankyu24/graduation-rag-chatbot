import fitz
from src.utils import ROOT
from src.graduation_rules import load_rules,get_rule


def test_pdf_page5_table_coordinates():
    path=ROOT/'data'/load_rules()['source']
    with fitz.open(path) as pdf:
        page=pdf[4]
        # Visually verified 2022 subtotal row, ordered by actual x coordinates.
        words=page.get_text('words')
        numeric=sorted([w for w in words if 965 < w[1] < 980 and w[4].isdigit()],key=lambda w:w[0])
        assert [int(w[4]) for w in numeric]==[45,10,21,19]
        total=[w for w in words if w[0]>1100 and 1070<w[1]<1085]
        assert any(w[4]=='95' for w in total)
        text=page.get_text()
        for word in ['예비창업설계','회당1점','3~10점','10~30점','SQL개발자']:
            assert word in text
    rule=get_rule('AI·빅데이터학과',2022)
    assert list(rule['required'].values())==[int(w[4]) for w in numeric]

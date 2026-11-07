import pytest
from src.advisor import answer_advisor
from src.pdf_loader import load_directory
from src.utils import ROOT


@pytest.mark.parametrize('question',[
    '저 문서를 요약해서 나에게 졸업 어케하는지 알려줘',
    '이 PDF 핵심 내용을 정리해줘',
    '나는 졸업하려면 뭘 해야 해?',
])
def test_document_summary_uses_actual_pdf_and_all_required_categories(question):
    docs,errors=load_directory(ROOT/'data');assert not errors
    text,hits=answer_advisor(question,docs,'AI·빅데이터학과',2022)
    assert hits and all(d.metadata['page']==5 for d in hits)
    for value in ['95점','대학공통','비교과지정','비교과미지정','예비창업설계','학과활동','자격증','코딩역량','AI·SW','국제사회언어','졸업학점']:
        assert value in text
    assert '2 이상' in text and '개인 졸업을 확정하지 않습니다' in text


def test_summary_wording_does_not_erase_an_unsupported_subject():
    docs,_=load_directory(ROOT/'data')
    text,hits=answer_advisor('이 문서의 우주여행 자격증 졸업요건을 요약해줘',docs,'AI·빅데이터학과',2022)
    assert not hits and '근거를 확인할 수 없습니다' in text

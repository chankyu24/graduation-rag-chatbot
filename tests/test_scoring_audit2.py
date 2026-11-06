"""Regression cases found by the second scoring and upload audit."""
import io

import pandas as pd
import pytest

from src.graduation_checker import check
from src.utils import read_course_file
from test_ai_2022 import D, full_input


def xlsx(rows):
    output = io.BytesIO()
    pd.DataFrame(rows).to_excel(output, index=False, header=False)
    return output.getvalue()


@pytest.mark.parametrize('headers', [
    ['과목명', '과목명', '이수여부'],
    ['과목명', '이수여부', '이수 여부'],
    ['과목명', '이수여부', ''],
])
def test_xlsx_cannot_hide_duplicate_or_blank_headers(headers):
    raw = xlsx([headers, ['예비창업설계', '이수', '이수']])
    with pytest.raises(ValueError, match='중복'):
        read_course_file(raw, '수강목록.xlsx')


def test_xlsx_original_headers_and_grades_remain_usable():
    raw = xlsx([
        ['과목명', '이수 여부', '성적'],
        ['예비창업설계', '이수', 'P'],
        ['예비창업설계', '이수', 'P'],
        ['미이수과목', '미이수', 'A+'],
        ['낙제과목', '이수', 'F'],
    ])
    assert read_course_file(raw, '수강목록.xlsx') == ['예비창업설계']


@pytest.mark.parametrize('year', [2022.9, '2022', True, None])
def test_cohort_type_cannot_mix_common_and_department_rules(year):
    with pytest.raises(ValueError, match='입학연도'):
        check(D, year)


@pytest.mark.parametrize('courses', ['예비창업설계', None, [None], [123]])
def test_course_container_must_be_explicit_strings(courses):
    with pytest.raises(ValueError, match='문자열 목록'):
        check(D, 2022, courses)


@pytest.mark.parametrize('course', [None, ['언어과목'], 123])
def test_official_course_evidence_must_be_text(course):
    c, a, e = full_input()
    e['중핵교양 국제사회언어영역 택1']['course'] = course
    with pytest.raises(ValueError, match='과목명은 문자열'):
        check(D, 2022, c, a, evidence=e)


@pytest.mark.parametrize('requirements', [[], '교과=10'])
def test_official_requirements_shape_has_actionable_validation(requirements):
    with pytest.raises(ValueError, match='영역별 사전'):
        check(D, 2022, official_requirements=requirements)


def test_boolean_is_not_an_official_number_or_participation_count():
    for activity in ['학과활동', '코딩역량인증제 Level2 이상']:
        with pytest.raises(ValueError):
            check(D, 2022, activities={activity: True})
    with pytest.raises(ValueError):
        check(D, 2022, evidence={'비교과자율활동(공감)': {'points': True, 'confirmed': True}})
    with pytest.raises(ValueError):
        check(D, 2022, official_requirements={'교과': True})


def test_verified_full_case_still_uses_95_and_independent_areas():
    courses, activities, evidence = full_input()
    result = check(D, 2022, courses, activities, evidence=evidence)
    assert result['status'] == '충족'
    assert result['total_earned'] == result['total_required'] == 95
    assert [area['earned'] for area in result['areas']] == [45, 10, 21, 19]

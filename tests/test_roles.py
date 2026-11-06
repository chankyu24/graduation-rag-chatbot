import sqlite3
import pytest
from src import auth
from src.evaluation import evaluate_case

@pytest.fixture(autouse=True)
def isolated(tmp_path,monkeypatch):
    monkeypatch.setenv('GRADUATION_APP_DATA_DIR',str(tmp_path/'roles'))


def test_evaluator_without_student_id():
    professor=auth.register('review.teacher','교수 테스트','Teacherpass123','AI·빅데이터학과',2022,role='evaluator')
    assert professor['role']=='evaluator' and professor['account_id']=='evaluator:review.teacher'
    assert auth.authenticate('review.teacher','Teacherpass123',role='evaluator')==professor
    assert auth.authenticate('review.teacher','Teacherpass123') is None
    assert auth.authenticate('20229990','Teacherpass123',role='evaluator') is None


def test_existing_student_database_migrates_without_losing_data():
    path=auth.database_path(); path.parent.mkdir(parents=True)
    salt='12'*16
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE users (student_id TEXT PRIMARY KEY,name TEXT,department TEXT,admission_year INTEGER,salt TEXT,digest TEXT,iterations INTEGER,created REAL)')
        db.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?)',('20220010','Existing','AI·빅데이터학과',2022,salt,auth.derive('Existingpass123',salt),auth.ITERATIONS,0))
    user=auth.authenticate('20220010','Existingpass123')
    assert user['name']=='Existing' and user['role']=='student'


def test_evaluator_does_not_receive_student_data():
    student=auth.register('20229990','학생 테스트','Studentpass123','AI·빅데이터학과',2022)
    professor=auth.register('teacher01','교수 테스트','Teacherpass123','AI·빅데이터학과',2022,role='evaluator')
    auth.save_profile(student['account_id'],'AI_2022',{'private':'student record'})
    assert auth.load_profiles(professor['account_id'])=={}
    auth.change_password(professor['account_id'],'Teacherpass123','Newteacher123')
    assert auth.authenticate('teacher01','Newteacher123',role='evaluator')

@pytest.mark.parametrize('case,expected,points',[
    ('확인 가능한 조건 충족','충족',95),
    ('필수 과목 누락','미충족',90),
    ('자율활동 점수 부족','미충족',94),
    ('빈 기록','미충족',0),
    ('이수 정보 미확인','확인 필요',0),
])
def test_evaluation_cases(case,expected,points):
    result=evaluate_case('AI·빅데이터학과',2022,case)
    assert result['synthetic'] and result['status']==expected and result['total_earned']==points

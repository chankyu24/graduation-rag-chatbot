import pytest
from src import auth

@pytest.fixture(autouse=True)
def isolated_database(tmp_path,monkeypatch):
    monkeypatch.setenv('GRADUATION_APP_DATA_DIR',str(tmp_path/'accounts'))


def register(identifier='20229991',name='Test Student',password='Classroom12345'):
    return auth.register(identifier,name,password,'AI·빅데이터학과',2022)


def test_register_login_hash_and_wrong_password():
    user=register()
    assert user['name']=='Test Student' and 'digest' not in user
    assert auth.authenticate(user['student_id'],'Classroom12345')==user
    assert auth.authenticate(user['student_id'],'Wrongpass123') is None
    assert auth.authenticate('00000000','Classroom12345') is None
    with auth.connection() as db:
        row=db.execute('SELECT * FROM users').fetchone()
        assert row['digest']!='Classroom12345' and len(row['salt'])==32


def test_passwords_use_different_salts():
    register(); register('20229992')
    with auth.connection() as db:
        rows=db.execute('SELECT salt,digest FROM users').fetchall()
    assert rows[0]['salt']!=rows[1]['salt'] and rows[0]['digest']!=rows[1]['digest']


def test_duplicate_and_validation():
    register()
    with pytest.raises(ValueError): register()
    with pytest.raises(ValueError): register('bad')
    with pytest.raises(ValueError): register('20229992',password='short')
    with pytest.raises(ValueError): register('20229992',password='12345678901')


def test_throttle_and_expiry(monkeypatch):
    register(); clock=[1000.0]; monkeypatch.setattr(auth.time,'time',lambda:clock[0])
    for _ in range(5): assert auth.authenticate('20229991','incorrect123') is None
    with pytest.raises(ValueError,match='5분'): auth.authenticate('20229991','Classroom12345')
    clock[0]+=301
    assert auth.authenticate('20229991','Classroom12345')


def test_password_change():
    register(); auth.change_password('20229991','Classroom12345','Updatedpass123')
    assert auth.authenticate('20229991','Classroom12345') is None
    assert auth.authenticate('20229991','Updatedpass123')


def test_saved_inputs_isolated_and_reloadable():
    register(); register('20229992')
    auth.save_profile('20229991','AI_2022',{'widgets':{'course':['예비창업설계']},'result':{'status':'미충족'}})
    assert auth.load_profiles('20229991')['AI_2022']['widgets']['course']==['예비창업설계']
    assert auth.load_profiles('20229992')=={}
    auth.save_profile('20229992','AI_2022',{'widgets':{'course':[]}})
    assert auth.load_profiles('20229991')['AI_2022']['result']['status']=='미충족'

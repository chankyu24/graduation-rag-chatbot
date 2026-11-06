"""Independent classroom-app accounts; no university password or SSO integration."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from .utils import ROOT

ITERATIONS=600_000


def database_path():
    return Path(os.getenv('GRADUATION_APP_DATA_DIR',str(ROOT/'.local')))/'accounts.sqlite3'


@contextmanager
def connection():
    path=database_path()
    path.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(path,timeout=10) as db:
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            student_id TEXT PRIMARY KEY, name TEXT NOT NULL, department TEXT NOT NULL,
            admission_year INTEGER NOT NULL, salt TEXT NOT NULL, digest TEXT NOT NULL,
            iterations INTEGER NOT NULL, created REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS attempts (
            student_id TEXT PRIMARY KEY, failures INTEGER NOT NULL DEFAULT 0,
            locked_until REAL NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS saved_profiles (
            student_id TEXT NOT NULL REFERENCES users(student_id) ON DELETE CASCADE,
            profile TEXT NOT NULL, payload TEXT NOT NULL, updated REAL NOT NULL,
            PRIMARY KEY(student_id,profile)
        );
        ''')
        columns={row['name'] for row in db.execute('PRAGMA table_info(users)')}
        if 'role' not in columns:
            db.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'student'")
        yield db


def student_id(value):
    value=str(value).strip()
    if not re.fullmatch(r'\d{8,12}',value):
        raise ValueError('학번은 8~12자리 숫자로 입력하세요.')
    return value


def validate_password(password):
    if not isinstance(password,str) or not 10<=len(password)<=128:
        raise ValueError('앱 전용 비밀번호는 10~128자여야 합니다.')
    if not re.search(r'[A-Za-z]',password) or not re.search(r'\d',password):
        raise ValueError('비밀번호에 영문과 숫자를 함께 넣어 주세요.')


def derive(password,salt,iterations=ITERATIONS):
    return hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),bytes.fromhex(salt),iterations).hex()


def public_user(row):
    return {key:row[key] for key in ['student_id','name','department','admission_year','role']} | {'account_id':row['student_id']}


def account_identifier(identifier,role='student'):
    if role=='student': return student_id(identifier)
    if role!='evaluator': raise ValueError('지원하지 않는 접속 유형입니다.')
    username=str(identifier).strip().lower()
    if username.startswith('evaluator:'): username=username[len('evaluator:'):]
    if not re.fullmatch(r'[a-z][a-z0-9_.-]{3,39}',username):
        raise ValueError('평가용 아이디는 영문으로 시작하는 4~40자 영문·숫자·밑줄·점·하이픈으로 입력하세요.')
    return 'evaluator:'+username


def register(identifier,name,password,department,admission_year,role='student'):
    identifier=account_identifier(identifier,role)
    name=str(name).strip()
    if not 1<=len(name)<=60 or any(ord(c)<32 for c in name):
        raise ValueError('이름은 1~60자로 입력하세요.')
    validate_password(password)
    from .graduation_rules import load_rules
    if department not in {r['department'] for r in load_rules()['profiles']}:
        raise ValueError('지원하는 학과를 선택하세요.')
    if type(admission_year) is not int or not 2000<=admission_year<=2100:
        raise ValueError('입학연도를 확인하세요.')
    salt=secrets.token_hex(16)
    digest=derive(password,salt)
    try:
        with connection() as db:
            db.execute('INSERT INTO users (student_id,name,department,admission_year,salt,digest,iterations,created,role) VALUES (?,?,?,?,?,?,?,?,?)',
                       (identifier,name,department,admission_year,salt,digest,ITERATIONS,time.time(),role))
    except sqlite3.IntegrityError as exc:
        raise ValueError('이미 등록된 학번입니다.' if role=='student' else '이미 등록된 평가용 아이디입니다.') from exc
    return get_user(identifier)


def get_user(identifier):
    with connection() as db:
        row=db.execute('SELECT * FROM users WHERE student_id=?',(identifier,)).fetchone()
    return public_user(row) if row else None


def authenticate(identifier,password,role='student'):
    try: identifier=account_identifier(identifier,role)
    except ValueError: return None
    if not isinstance(password,str) or len(password)>128:
        return None
    now=time.time()
    with connection() as db:
        attempt=db.execute('SELECT * FROM attempts WHERE student_id=?',(identifier,)).fetchone()
        if attempt and attempt['locked_until']>now:
            raise ValueError('로그인 시도가 많습니다. 5분 후 다시 시도하세요.')
        row=db.execute('SELECT * FROM users WHERE student_id=?',(identifier,)).fetchone()
        actual=derive(password,row['salt'] if row else '00'*16,row['iterations'] if row else ITERATIONS)
        if row and hmac.compare_digest(actual,row['digest']):
            db.execute('DELETE FROM attempts WHERE student_id=?',(identifier,))
            return public_user(row)
        failures=(attempt['failures'] if attempt and attempt['locked_until']<=now and attempt['locked_until']==0 else 0)+1
        locked_until=now+300 if failures>=5 else 0
        db.execute('INSERT OR REPLACE INTO attempts VALUES (?,?,?)',(identifier,failures,locked_until))
    return None


def change_password(identifier,current_password,new_password):
    existing=get_user(identifier)
    user=authenticate(identifier,current_password,existing['role']) if existing else None
    if not user:
        raise ValueError('현재 비밀번호가 올바르지 않습니다.')
    validate_password(new_password)
    salt=secrets.token_hex(16)
    with connection() as db:
        db.execute('UPDATE users SET salt=?,digest=?,iterations=? WHERE student_id=?',
                   (salt,derive(new_password,salt),ITERATIONS,identifier))


def save_profile(identifier,profile,payload):
    encoded=json.dumps(payload,ensure_ascii=False,allow_nan=False)
    if len(encoded.encode('utf-8'))>2*1024*1024:
        raise ValueError('저장할 입력 내역이 너무 큽니다.')
    with connection() as db:
        if not db.execute('SELECT 1 FROM users WHERE student_id=?',(identifier,)).fetchone():
            raise ValueError('다시 로그인해 주세요.')
        db.execute('INSERT OR REPLACE INTO saved_profiles VALUES (?,?,?,?)',
                   (identifier,profile,encoded,time.time()))


def load_profiles(identifier):
    with connection() as db:
        rows=db.execute('SELECT profile,payload FROM saved_profiles WHERE student_id=?',(identifier,)).fetchall()
    return {row['profile']:json.loads(row['payload']) for row in rows}


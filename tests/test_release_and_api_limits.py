import shutil,json
from src.release_info import release_info,runtime_files
from src.llm_settings import llm_options
from src.utils import ROOT


def test_distribution_fingerprint_ignores_generated_reports_and_detects_rule_change(tmp_path,monkeypatch):
    monkeypatch.delenv('RAILWAY_GIT_COMMIT_SHA',raising=False)
    for p in runtime_files():
        target=tmp_path/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,target)
    expected=release_info()['runtime_sha256']
    assert release_info(tmp_path)['runtime_sha256']==expected
    (tmp_path/'SOURCE_VERSION.json').write_text(json.dumps({'source_commit':'a'*40,'runtime_sha256':expected}),encoding='utf8')
    (tmp_path/'README.md').write_text('generated report',encoding='utf8')
    assert release_info(tmp_path)['runtime_sha256']==expected
    assert release_info(tmp_path)['source_commit']=='a'*40
    rule=tmp_path/'rules/graduation_rules.json'
    rule.write_bytes(rule.read_bytes()+b'\n')
    assert release_info(tmp_path)['runtime_sha256']!=expected
    assert release_info(tmp_path)['source_commit'] is None


def test_api_output_and_retry_limits_are_bounded(monkeypatch):
    for value,expected in [('bad',800),('-1',128),('500',500),('999999',2000)]:
        monkeypatch.setenv('OPENAI_MAX_OUTPUT_TOKENS',value)
        options=llm_options()
        assert options['max_tokens']==expected
        assert options['timeout']==30 and options['max_retries']==0

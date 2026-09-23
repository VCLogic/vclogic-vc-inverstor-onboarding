import subprocess
import sys

from vclogic_onboarding.cli import main


def test_help_has_import_and_pitch_show_options():
    result=subprocess.run([sys.executable,'-m','vclogic_onboarding','prepare','--help'],capture_output=True,text=True)
    assert result.returncode==0
    for flag in ['--wiki','--from-pitch-show','--pitch-show-slug','--review','--skip-indexes']:
        assert flag in result.stdout


def test_cli_prepare_check_install(wiki,tmp_path,capsys):
    bundle=tmp_path/'bundle'
    assert main(['prepare','--wiki',str(wiki),'--output',str(bundle),'--skip-indexes'])==0
    assert main(['check','--bundle',str(bundle)])==0
    pipeline=tmp_path/'pipeline';pipeline.mkdir()
    assert main(['install','--bundle',str(bundle),'--pipeline-workspace',str(pipeline)])==0
    assert (pipeline/'inputs/investors/test-investor.toml').is_file()
    assert 'false' in capsys.readouterr().out


def test_cli_reports_invalid_source_without_traceback(tmp_path,capsys):
    assert main(['prepare','--wiki',str(tmp_path/'absent'),'--output',str(tmp_path/'out'),'--skip-indexes'])==1
    assert 'error' in capsys.readouterr().err

"""Produce engine-native configurations from pinned upstream templates."""
from __future__ import annotations

from importlib.resources import files
import json
from pathlib import Path
import tomllib

from vc_clone_graph.config import RunConfig
from vc_clone_graph.rehearsal_config import RehearsalConfig


def resource(name: str) -> bytes:
    return files('vclogic_onboarding').joinpath('resources',name).read_bytes()


def template(name: str) -> dict:
    return tomllib.loads(resource(name).decode())


def write_toml(path: Path, value: dict) -> None:
    # Engine configuration has only top-level scalars and flat tables.
    def scalar(item):
        if isinstance(item,(str,bool,int,float,list)):
            return json.dumps(item,ensure_ascii=False,allow_nan=False)
        raise ValueError(f'unsupported TOML value: {item!r}')
    lines=[]
    for key,item in value.items():
        if not isinstance(item,dict) and item is not None:
            lines.append(f'{key} = {scalar(item)}')
    for key,item in value.items():
        if isinstance(item,dict):
            lines.extend(['',f'[{key}]'])
            lines.extend(f'{k} = {scalar(v)}' for k,v in item.items() if v is not None)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('\n'.join(lines).lstrip()+'\n',encoding='utf-8')


def embedding_settings() -> dict:
    embedding=template('canonical.toml')['embedding']
    return {'backend':embedding['kind'], **{k:embedding[k] for k in (
        'model','revision','normalize','document_prefix','query_prefix')}}


def write_configs(root: Path,slug: str,*,precedents: bool) -> None:
    canonical=template('canonical.toml')
    canonical['run'].update(vc_slug=slug,episode_slug='onboarding-index',
        output_root=f'outputs/assessments/{slug}',checkpoint_path=f'outputs/assessments/{slug}/checkpoints.sqlite')
    canonical['precedents'].update(enabled=precedents,corpus_path=f'data/investors/{slug}/precedents')
    canonical['portfolio_memory']['enabled']=False
    rehearsal=template('rehearsal.toml')
    rehearsal['rehearsal'].update(output_root=f'outputs/rehearsals/{slug}',
        checkpoint_path=f'outputs/rehearsals/{slug}/checkpoints.sqlite')
    rehearsal['precedents']['enabled']=precedents
    rehearsal['portfolio_memory']['enabled']=False
    rehearsal['classification'].update(canonical_config_path=f'configs/investors/{slug}/canonical.toml',
        classifier_tiebreaker=False)
    RunConfig.model_validate(canonical)
    RehearsalConfig.model_validate(rehearsal)
    write_toml(root/f'configs/investors/{slug}/canonical.toml',canonical)
    write_toml(root/f'configs/investors/{slug}/rehearsal.toml',rehearsal)

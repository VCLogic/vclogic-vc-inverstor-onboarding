"""Convert evidence-linked review rows with the assessment's own dataset builders."""
from __future__ import annotations

from pathlib import Path

from vc_clone_graph.dataset_prep import compile_review_rows, write_pitch_package
from vc_clone_graph.firewall import safe_slug, verify_package
from vc_clone_graph.manifest_builder import build_episode_manifest
from vc_clone_graph.precedent_builder import build_precedent_corpus

from .files import digest, read_json, write_json


def enrich(root: Path,slug: str,review: Path,aliases: list[str],pitch_show_slug: str) -> dict:
    rows=read_json(review)
    if not isinstance(rows,list) or not rows:
        raise ValueError('review must be a nonempty list of evidence-linked review rows')
    transcripts=root/'source/pitch-show/episodes'
    for row in rows:
        safe_slug(row['episode_slug'],'episode_slug')
        path=transcripts/f"{row['episode_slug']}.json"
        if not path.is_file():
            raise ValueError(f'review episode was not collected: {row["episode_slug"]}')
        # The collector slug can differ from the memory slug. Normalize only the
        # structured participation identifier; leave transcript bytes untouched.
        episode=read_json(path)
        for member in episode.get('panel',[]):
            if member.get('slug')==pitch_show_slug:
                member['slug']=slug
        write_json(path,episode)
    compiled=compile_review_rows(review_rows=rows,transcript_root=transcripts,
        vc_slug=slug,investor_aliases=aliases)
    for row in compiled:
        row['evidence_source']=f"source/pitch-show/episodes/{row['episode_slug']}.json transcript"
    ledger_relative=f'evaluation/labels/{slug}.json'
    ledger=root/ledger_relative
    write_json(ledger,compiled)
    investor_root=root/f'inputs/data/investors/{slug}'
    corpus=investor_root/'precedents'
    records=build_precedent_corpus(transcripts,ledger,corpus,aliases)
    # The upstream builder records its input path. Use a portable source locator,
    # then update the engine's hash manifest after that metadata-only change.
    corpus_manifest=read_json(corpus/'corpus-manifest.json')
    for entry in corpus_manifest['records']:
        path=corpus/entry['record_path']
        payload=read_json(path);payload['decision']['audit_source']=ledger_relative
        write_json(path,payload);entry['record_sha256']=digest(path)
    write_json(corpus/'corpus-manifest.json',corpus_manifest)
    eligible=[]
    for row in compiled:
        if not row['evaluation_eligible']:
            continue
        write_pitch_package(episode_path=transcripts/f"{row['episode_slug']}.json",compiled_review=row,
            investor_root=investor_root,vc_slug=slug,audit_source=ledger_relative)
        build_episode_manifest(root/'inputs',slug,row['episode_slug'])
        verify_package(root/'inputs',slug,row['episode_slug'])
        eligible.append(row['episode_slug'])
    return {'reviewed_rows':len(compiled),'precedent_records':len(records),'eligible_pitches':eligible}

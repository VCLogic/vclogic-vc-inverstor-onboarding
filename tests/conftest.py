import hashlib

import pytest
from wiki_build.config import DIMENSIONS
from wiki_build.render import render


@pytest.fixture
def wiki(tmp_path):
    text = 'I value founders who keep their promises.'
    prepared = {
        'vc_slug': 'test-investor', 'identity': {'canonical_name': 'Test Investor', 'aliases': ['Test']},
        'documents': [{'doc_id': 'source:one', 'text': text, 'sha256': hashlib.sha256(text.encode()).hexdigest(),
                       'url': 'https://example.com/interview', 'title': 'Interview', 'published_at': None,
                       'input_path': 'corpus/all_documents.jsonl', 'input_line': 1}],
        'portfolio': [], 'warnings': ['Thin corpus'], 'corpus_chars': len(text),
        'thin_corpus': True, 'no_pitch_sources': True, 'input_hashes': {},
    }
    evidence = [{'id': 'test-0001', 'source': 'source:one', 'quote': text,
                 'label': 'founder_qualities', 'direction': 'positive', 'support': 'explicit',
                 'interpretation': 'Value reliable founders.'}]
    synthesis = {
        'persona': '# Test Investor\n\n' + '\n\n'.join('## '+d+'\n\n'+
            ('- In: Value reliable founders. [ev:test-0001]' if d == 'founder_team' else 'Insufficient evidence.')
            for d in DIMENSIONS) + "\n\n## Distinctive / doesn't-fit-the-taxonomy\n\nInsufficient evidence.",
        'theses': '# Theses\n\n- Reliability matters. [ev:test-0001]',
        'portfolio_and_constraints': '# Portfolio\n\nNo verified holdings available. Mandate unknown.',
    }
    path = tmp_path/'wiki'
    render(path, prepared, evidence, synthesis, {'model': 'fixture'})
    return path

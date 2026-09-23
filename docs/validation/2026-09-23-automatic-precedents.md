# Automatic historical retrieval validation

## Implementation

`--from-pitch-show` now runs automatic decision extraction and separate model verification, validates exact investor quotes and conditions locally, builds engine-native historical records, and enables historical retrieval. `--collect-only` preserves download-only behavior; `--decision-model` overrides the shipped default. Human review overrides machine extraction and remains the only source of evaluation labels and eligible historical pitch packages.

Machine rows explicitly state that they are not human-audited. Their audit source is an installed `inputs/data/investors/<slug>/machine-decisions.json` file. Full source transcripts and index hashes are checked by the assessment engine. Timing and decision semantics still depend on model judgment; deterministic checks prove quote/turn/speaker binding, not semantic correctness.

## Offline verification

59 tests pass. Coverage includes exact evidence, wrong speakers/turns/quotes, later diligence, model disagreement, conditions, malformed responses, failed provider calls, oversized/missing transcripts, human override merging, index relocation, and absence of machine-generated evaluation labels. Wheel and source distribution build. A separate read-only review found no blocking issues.

## Bounded live test

Used the two archived live Mac Conwell episodes with `--alias Mac` and the configured OpenRouter credential. Four model calls reported a combined $0.01599715. Both outcomes were machine In decisions with exact investor quotes; Tether retained the condition `pending that Delaware C Corp`. No evaluation labels were created.

Real Nomic indexes built successfully. Installing the smoke bundle to a temporary workspace wrote 64 files. Engine-native historical search returned lexical and dense hits. `open_decision` returned Tether's condition, machine provenance and an existing ledger locator. `for_target` excluded the target episode. The temporary workspace was removed; no installation into the active assessment repository occurred.

The user's existing `bundles/mac-conwell-rarebreed-ventures` is preserved. Enrichment uses the separate version `bundles/mac-conwell-rarebreed-ventures-v2`; these data bundles and the credential file are ignored by Git.

## Full live collection and extraction

The completed live collection examined all 228 discovered candidate pages and retained 32 matching episodes with transcripts. It reported no download failures, no missing transcripts, and complete discovery coverage for this run. This is source-discovery coverage, not a guarantee of decision correctness.

The separate enriched bundle contains 6 machine In, 13 machine Out, and 13 unobserved decisions. Unobserved records include specials, unclear outcomes and one condition that failed verbatim validation. All 32 transcripts are retained for retrieval. The full extraction made 51 model calls with reported cost $0.16014957 (approximately $0.17615 including the initial two-episode smoke run). No evaluation labels or historical evaluation pitch packages were generated.

Commands used:

```bash
uv run --extra embeddings investor-onboarding prepare \
  --wiki ../vclogic-vc-investment-memory/wiki/mac-conwell \
  --output bundles/mac-conwell-rarebreed-ventures-v2 \
  --from-pitch-show \
  --pitch-show-slug mac-conwell-rarebreed-ventures \
  --alias Mac \
  --skip-indexes

OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 uv run --extra embeddings investor-onboarding index \
  --bundle bundles/mac-conwell-rarebreed-ventures-v2
```

The full real index build passed. A fresh temporary install wrote 414 files; a second install was idempotent. Both configs enabled precedents. The relocated wiki index loaded 1,335 chunks and the historical corpus loaded all 32 episodes. Real dense search succeeded; contrastive search with a sufficiently large candidate pool returned two In and three Out episodes. Decision reads retained machine audit provenance and conditions, and the target episode was inaccessible through the filtered corpus. No human evaluation labels existed. Bundle check reports `ready_for_assessment: true` and `capabilities.precedents: true`.

The contrastive check explicitly uses `candidate_pool_k=1000`: a small chunk candidate pool does not guarantee five distinct episode hits. This is an existing engine retrieval behavior, not an onboarding interface change. Full paid assessment generation was not run.

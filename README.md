# VCLogic investor onboarding

A separate CLI repository that converts an investor wiki from `vclogic-vc-investment-memory` into the files expected by `vclogic-vc-agentic-assessment`.

```text
investment-memory wiki → investor-onboarding bundle → assessment pipeline
```

The tool generates the investor TOML registration, curated wiki, canonical and rehearsal TOML configurations, and semantic indexes. You do not write those TOML files yourself. It validates the source with the investment-memory validator and the output with the assessment engine's validators.

## Setup

Keep these repositories next to one another:

```text
/home/dpasch01/
  vclogic-vc-investment-memory/
  vclogic-vc-investor-onboarding/
  vclogic-vc-agentic-assessment/
```

Python 3.11–3.13 and `uv` are required. Local sibling dependencies are configured in `pyproject.toml`.

```bash
cd /home/dpasch01/vclogic-vc-investor-onboarding
uv sync
uv run investor-onboarding --help
```

## Import a wiki

Build a complete bundle (the first run downloads the local embedding model):

```bash
uv run --extra embeddings investor-onboarding prepare \
  --wiki ../vclogic-vc-investment-memory/wiki/mac-conwell \
  --output bundles/mac-conwell-ready-v1

uv run investor-onboarding check --bundle bundles/mac-conwell-ready-v1

uv run investor-onboarding install \
  --bundle bundles/mac-conwell-ready-v1 \
  --pipeline-workspace ../vclogic-vc-agentic-assessment
```

To inspect the conversion first without downloading embedding models:

```bash
uv run investor-onboarding prepare \
  --wiki ../vclogic-vc-investment-memory/wiki/mac-conwell \
  --output bundles/mac-conwell-v1 \
  --skip-indexes

uv run --extra embeddings investor-onboarding index --bundle bundles/mac-conwell-v1
```

`--skip-indexes` produces `ready_for_assessment: false`. Complete the indexes before installing for assessment use. Indexing uses local embeddings; onboarding does not call a paid language model. Running the assessment later needs its own provider credentials.

Optional identity overrides: `--slug`, `--display-name`, `--firm`, `--role`, and repeatable `--alias`. Supply firm/role when needed; the importer does not infer current employment from historical mentions.

## Investors from The Pitch

Add `--from-pitch-show` to download the official investor profile and matching episodes/transcripts, and record reported investments and decisions. Use `--pitch-show-slug` when the site's investor identifier differs from the wiki identifier:

```bash
uv run investor-onboarding prepare \
  --wiki /path/to/generated/wiki \
  --output bundles/investor-collected-v1 \
  --from-pitch-show \
  --pitch-show-slug investor-site-slug \
  --skip-indexes
```

The bundle contains `source/pitch-show/` with the profile, episodes, decisions, source receipts, collection status, and `review-template.json`. Missing transcripts, failed requests, and collection caps are reported explicitly. Absence from an investment list is **not** treated as an Out decision.

Use `--max-episodes 10` for a bounded collection; coverage will be marked incomplete if capped. To use cached downloads without network requests, add `--pitch-show-cache /path/to/cache`. Supported caches are this tool's `source/pitch-show` directory or the original scraper's directory containing `data/investors` and `data/episodes` (the `data` directory itself also works).

### Promote reviewed decisions into assessment data

Downloaded decisions are evidence for review. They do not automatically become ground-truth labels. Copy `review-template.json` outside the bundle, review the transcript, and supply a nonempty JSON list such as:

```json
[
  {
    "episode_slug": "1-example",
    "final_decision": "Out",
    "pitch_window_decision": "Out",
    "initial_response": "Out",
    "decision_context": "initial_panel",
    "label_basis": "explicit investor statement",
    "audit_notes": "Checked the speaker and decision timing against the transcript.",
    "evidence_contains": "I am out because the market is too small."
  }
]
```

Use actual episode identifiers and exact transcript evidence. Add `--alias 'Transcript Speaker Name'` if necessary. Then prepare a new bundle:

```bash
uv run --extra embeddings investor-onboarding prepare \
  --wiki /path/to/generated/wiki \
  --output bundles/investor-reviewed-v2 \
  --from-pitch-show \
  --pitch-show-slug investor-site-slug \
  --pitch-show-cache bundles/investor-collected-v1/source/pitch-show \
  --review /path/to/review.json
```

The assessment engine compiles reviewed rows into an audited decision ledger, historical precedents, and eligible pitch packages. Pitch packages remove decision evidence from the pitch presented for assessment. Missing or ambiguous evidence fails validation.

## Output and installation

Each bundle includes:

- `bundle.json`: version, file hashes, capabilities, collection status, and readiness.
- `inputs/investors/<slug>.toml` and `inputs/wiki/<slug>/`.
- `configs/investors/<slug>/{canonical,rehearsal}.toml`.
- `inputs/indexes/`: semantic indexes when built.
- `source/wiki/`: original wiki snapshot for validation and provenance.
- With reviewed pitches: `evaluation/labels/<slug>.json` and `inputs/data/investors/<slug>/`.

`install` checks all conflicts before writing and never overwrites differing files. Identical files are skipped. It archives source evidence under `onboarding/<slug>/source/` in the target workspace. Ledger evidence locators are relative to the bundle; their `source/` prefix maps to `onboarding/<slug>/source/` after installation. The target must exist. A new version that conflicts with an installed investor requires explicit version management outside this tool; there is no force-overwrite flag.

Portfolio prose remains available in wiki retrieval. Structured portfolio memory and a trained decision classifier are not produced; generated configs disable the unsupported retrieval/fallback paths. Historical precedents are enabled only when reviewed records exist. Readiness refers to generated assessment assets, not external API credentials or complete historical coverage.

This repository contains no web application or API. The original LangGraph assessment logic remains in the assessment repository; this CLI prepares its inputs. Pinned configuration/taxonomy resources and source hashes are recorded in `src/vclogic_onboarding/resources/provenance.json`.

## Development

```bash
uv sync --extra dev
uv run pytest -q
uv build
```

Tests use deterministic embedding doubles and offline Pitch Show responses. They do not require model downloads, paid inference, or a live full-site crawl.

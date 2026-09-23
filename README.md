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

`--skip-indexes` produces `ready_for_assessment: false`. Complete the indexes before installing for assessment use. Indexing uses local embeddings. Wiki-only onboarding does not call a paid language model; automatic Pitch Show decision extraction does. Running the assessment later needs its own provider credentials.

Optional identity overrides: `--slug`, `--display-name`, `--firm`, `--role`, and repeatable `--alias`. Supply firm/role when needed; the importer does not infer current employment from historical mentions.

## Investors from The Pitch

Add `--from-pitch-show` to download the official investor profile and matching episodes/transcripts, extract evidence-linked pitch-window decisions, and build historical retrieval. Set `OPENROUTER_API_KEY` in your environment or this repository's `.env` first. The flag authorizes paid extraction and verification calls through OpenRouter; `--decision-model` overrides the default model in the shipped canonical config. Use `--pitch-show-slug` when the site's investor identifier differs from the wiki identifier:

```bash
uv run --extra embeddings investor-onboarding prepare \
  --wiki /path/to/generated/wiki \
  --output bundles/investor-collected-v1 \
  --from-pitch-show \
  --pitch-show-slug investor-site-slug \
  --alias "Transcript Speaker Name"
```

For Mac Conwell, use `--pitch-show-slug mac-conwell-rarebreed-ventures --alias Mac`. The wiki identifier remains `mac-conwell`; the output directory name does not change it. Live requests respect standard HTTP proxy and certificate environment settings.

The bundle contains `source/pitch-show/` with the profile, episodes, decisions, source receipts, collection status, and `review-template.json`. Missing transcripts, failed requests, and collection caps are reported explicitly. Absence from an investment list is **not** treated as an Out decision.

Use `--max-episodes 10` to collect at most ten matching investor episodes (panel appearances or profile-reported investments). Unrelated pages and failed requests do not consume this limit, so more than ten candidate pages may be examined. The collection report records `candidate_count` and `examined_count`; coverage is incomplete when unexamined candidates remain. To reuse collected evidence without downloading it again, add `--pitch-show-cache /path/to/cache`. Supported caches are this tool's `source/pitch-show` directory or the original scraper's directory containing `data/investors` and `data/episodes` (the `data` directory itself also works).

### Automatic historical retrieval

The default workflow sends each usable transcript through an extraction pass and a separate verification pass. Local validation checks the exact investor speaker, turn, quote, and any condition. Only agreeing pitch-window decisions become machine In/Out records; ambiguous, invalid, later-diligence or unverified decisions remain unobserved. Timing is model-checked, not deterministically proven or human-audited. Missing transcripts are reported and excluded. Transcripts above 180,000 characters remain searchable with an unobserved decision; they are never silently truncated.

Machine decisions live under `inputs/data/investors/<slug>/machine-decisions.json`. Prompts, responses, usage, model identity, source hashes and abstention reasons live under `source/pitch-show/extraction/`. The assessment engine's builders create the historical corpus and semantic index; both generated configs enable precedents when records exist. Collection completeness is reported separately from index readiness. Machine extraction never creates evaluation labels or eligible historical evaluation pitch packages.

Use `--collect-only` to download evidence without model extraction. `--skip-indexes` skips embedding generation only; it does not skip extraction. `--pitch-show-cache` avoids collection network requests but automatic extraction still calls the model. An API failure aborts preparation; the existing bundle is preserved. Choose a new output version when enriching a wiki-only bundle.

For example:

```bash
uv run --extra embeddings investor-onboarding prepare \
  --wiki ../vclogic-vc-investment-memory/wiki/mac-conwell \
  --output bundles/mac-conwell-rarebreed-ventures-v2 \
  --from-pitch-show \
  --pitch-show-slug mac-conwell-rarebreed-ventures \
  --alias Mac
```

Inspect `check` output for `capabilities.precedents: true`, `ready_for_assessment: true`, and the extraction counts. These indicate usable historical retrieval, not human-audited labels or exhaustive site coverage.

### Promote reviewed decisions into assessment data

Machine and profile-reported decisions do not automatically become ground-truth labels. Human `--review` rows override automatic extraction for their episodes; other episodes still receive automatic extraction. Use `--collect-only --review ...` for the previous human-review-only workflow. Copy `review-template.json` outside the bundle, review the transcript, and supply a nonempty JSON list such as:

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
- With automatic Pitch Show enrichment: machine decisions and historical corpus under `inputs/data/investors/<slug>/`.
- With human-reviewed pitches: `evaluation/labels/<slug>.json` and eligible pitch packages.

`install` checks all conflicts before writing and never overwrites differing files. Identical files are skipped. It archives source evidence under `onboarding/<slug>/source/` in the target workspace. Ledger evidence locators are relative to the bundle; their `source/` prefix maps to `onboarding/<slug>/source/` after installation. The target must exist. A new version that conflicts with an installed investor requires explicit version management outside this tool; there is no force-overwrite flag.

Portfolio prose remains available in wiki retrieval. Structured portfolio memory and a trained decision classifier are not produced; generated configs disable the unsupported retrieval/fallback paths. Historical precedents are enabled when machine or human-reviewed transcript records exist. Readiness refers to generated assessment assets, not external API credentials or complete historical coverage.

This repository contains no web application or API. The original LangGraph assessment logic remains in the assessment repository; this CLI prepares its inputs. Pinned configuration/taxonomy resources and source hashes are recorded in `src/vclogic_onboarding/resources/provenance.json`.

## Development

```bash
uv sync --extra dev
uv run pytest -q
uv build
```

Tests use deterministic embedding doubles and offline Pitch Show responses. They do not require model downloads, paid inference, or a live full-site crawl.

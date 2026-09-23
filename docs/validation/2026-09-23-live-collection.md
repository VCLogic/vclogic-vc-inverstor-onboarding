# Live collection and embedding validation — 2026-09-23

## Changes verified

- `--max-episodes` now counts unique matching investor episodes, in both live and cache modes. Unrelated pages and failed requests do not consume the limit. Reports expose candidate and examined counts. The limit is not a request budget; unmatched investors can require scanning all candidates.
- Live HTTP requests respect environment proxy settings. Explicitly disabling them caused a connection timeout in this environment. CLI HTTP errors now produce a concise error rather than a traceback.
- Episode parsing supports the site's JSON-LD actor `@id` references, including fragment removal, alongside the older description/url format. JSON-LD transcript text is a fallback when the HTML transcript is missing.

## Live evidence

Command: `uv run investor-onboarding prepare --wiki ../vclogic-vc-investment-memory/wiki/mac-conwell --output bundles/mac-conwell-live-v3 --from-pitch-show --pitch-show-slug mac-conwell-rarebreed-ventures --max-episodes 2 --skip-indexes` (executed with a 180-second process timeout).

The official investor directory supplied the site-specific slug. Profile and sitemap discovery succeeded. Collection examined 6 of 228 candidates and retained:

- `129-reddrop-pitching-the-big-vision`: matched panel, available transcript, profile-reported In.
- `102-tether-bodyguard-of-the-grid`: matched panel, available transcript, Unknown reported decision.

No request failures or missing transcripts occurred in the completed bounded run. Coverage is correctly incomplete and capped. No audited historical labels were created. Profile absence still never implies Out.

An earlier diagnostic run exposed the actor-format mismatch; it was interrupted after saving 214 HTML pages. Replaying those saved pages with the corrected parser matched 30 appearances, including specials. This is diagnostic evidence, not proof of complete coverage. Snapshots and bundles are ignored by Git.

## Real embedding and isolated handoff

`uv sync --extra dev --extra embeddings` succeeded. `uv run --extra embeddings investor-onboarding index --bundle bundles/mac-conwell-v1` downloaded and loaded the pinned Nomic model and completed indexing. This previously unindexed example is now assessment-ready for its wiki-only capabilities.

The indexed bundle was installed into a temporary workspace, never the active assessment repository. The assessment package loaded both generated configs and the relocated wiki index with complete embeddings required. The index contained 1,335 chunks with 768-dimensional embeddings; a real embedded query returned three hits. Installation wrote 45 files including the receipt. The temporary workspace was removed afterward.

This verifies the wiki asset handoff and real retrieval, not a complete model-generated assessment. No paid inference was run, no real decisions were promoted without human review, and no assessment interfaces were changed. Reviewed historical builders remain covered by offline tests; real historical embedding and full assessment execution remain follow-up work.

## Checks

- `uv run pytest -q`: 38 passed.
- `uv build`: wheel and source distribution built.
- Regression coverage includes live/cache matching limits, stopping downloads after the limit, failed candidates, actor IDs, JSON-LD transcript fallback, proxy configuration, and CLI network errors.

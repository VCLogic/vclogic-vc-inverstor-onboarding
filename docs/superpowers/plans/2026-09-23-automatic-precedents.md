# Automatic Precedents Implementation Plan

**Goal:** Make Pitch Show onboarding supply usable historical retrieval automatically.
**Architecture:** Separate model extraction and local evidence validation from the existing human-reviewed dataset pipeline. Reuse assessment providers, schemas, corpus builder and embedding implementation.
**Tech stack:** Python, Pydantic, existing OpenRouter adapter, pytest.

- [x] Add `tests/test_extraction.py`: valid investor evidence; wrong speaker/quote/index; verification disagreement; later diligence; unknown decisions; missing transcript; oversized transcript; machine artifacts never create evaluation labels; failure propagation.
- [x] Implement `src/vclogic_onboarding/extraction.py`: strict proposal and verification schemas, prompt source isolation, bounded full-transcript requests, exact turn validation, source/model/usage receipts, corpus assembly with portable audit locators. Accept injected provider for offline tests.
- [x] Extend `bundle.prepare` and CLI: automatic extraction, `--collect-only`, `--decision-model`, human override handling, extraction summary. Fail missing credentials before collection; lazy provider creation where no usable transcripts exist is not required.
- [x] Update existing download-only tests to select `collect_only=True`. Add integration coverage for real corpus indexing with deterministic embeddings and relocation, human override merging and no fabricated labels.
- [x] Run `uv run pytest -q`, `uv build`, `git diff --check`.
- [x] Exercise bounded live cached Mac transcripts with real generation if credentials exist. Prepare a new enriched bundle, build real indexes and install to a temporary workspace; inspect engine historical search/decision reads. Preserve user's existing bundle and active assessment workspace.
- [x] Document command changes, provenance limitations and verified outcomes; commit and push authorized repository changes.

Execution notes: The two-episode live generation and real retrieval handoff passed. Full collection/extraction and real indexing completed for 32 episodes. Temporary install, dense and contrastive retrieval, decision provenance, conditions, and target exclusion passed. 59 offline tests and package builds pass. Independent read-only review found no blocking issues. User approved automated extraction and configured the local credential. Work remained in this onboarding repository; no engine interface changes.

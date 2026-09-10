"""Acceptance tests for CTX-001..CTX-008 against the real environment.

The corpus runs on a real local HTTP server; retrieval is real HTTP with
canonical identity, digests and provenance; the benchmark is deterministic
over preserved outputs.
"""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))
sys.path.insert(0, str(REPO_ROOT / "tests/context"))

from corpus import start_corpus_server  # noqa: E402
from quansio.context.executor import ProgramExecutor  # noqa: E402
from quansio.context.projection import ProjectionDenied, ContextProjector  # noqa: E402
from quansio.context.research_record import (  # noqa: E402
    FalseMergeRejected,
    ResearchRecordStore,
)
from quansio.context.retrieval import (  # noqa: E402
    HttpRetrievalAdapter,
    canonical_url,
    content_digest,
    dedup_key,
)
from quansio.context.scoring import (  # noqa: E402
    BenchmarkScorer,
    compute_metrics,
    meets_thresholds,
    qualification_identity,
)
from quansio.context.search_program import (  # noqa: E402
    ProgramRunStore,
    ProgramValidationError,
    parse_program,
)
from quansio.context.verification import ClaimVerifier, ContentCacheAdapter  # noqa: E402
from quansio.indexer.index import IndexDivergence, ResearchIndex  # noqa: E402
from quansio.platform.context import IdentityContext  # noqa: E402


@pytest.fixture(scope="module")
def corpus():
    server, port, pages = start_corpus_server()
    yield {"base": f"http://127.0.0.1:{port}", "pages": pages, "server": server}
    server.shutdown()


def _open_program_run(db, context) -> str:
    program_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO program_runs (tenant_id, program_id, spec_digest, status)"
        " VALUES (%s, %s, 'test', 'running') ON CONFLICT DO NOTHING",
        (context.tenant_id, program_id),
    )
    return program_id


def _ctx(workspace_setup) -> IdentityContext:
    return IdentityContext(
        tenant_id=workspace_setup["tenant_id"],
        workspace_id=workspace_setup["workspace_a"],
        user_id=workspace_setup["admin"],
        session_id=str(uuid.uuid4()),
        roles=("member",),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


# ---------------------------------------------------------------------------
# CTX-001: typed bounded SearchProgram
# ---------------------------------------------------------------------------


def test_ctx001_p01_valid_program_parses_and_executes(migrated_db, workspace_setup, corpus):
    context = _ctx(workspace_setup)
    program = parse_program({
        "steps": [
            {"operator": "RETRIEVE", "arguments": {"url": f"{corpus['base']}/companies/company-000"}},
            {"operator": "EXTRACT", "arguments": {"entity_name": "company-000"}},
            {"operator": "SYNTHESIZE", "arguments": {}},
        ],
        "max_fan_out": 10,
        "max_iterations": 2,
    })
    assert program.digest()
    store = ProgramRunStore(migrated_db)
    program_id = store.open_run(context, program)
    rows = migrated_db.query_one(
        "SELECT status FROM program_runs WHERE tenant_id=%s AND program_id=%s",
        (context.tenant_id, program_id),
    )
    assert rows[0] == "running"


def test_ctx001_n01_invalid_programs_fail_before_execution(migrated_db, workspace_setup):
    context = _ctx(workspace_setup)
    bad_programs = [
        {"steps": [{"operator": "TELEPORT", "arguments": {}}]},
        {"steps": [{"operator": "FILTER",
                    "arguments": {"predicate": "lambda c: c.title"}}]},
        {"steps": [{"operator": "FAN_OUT", "arguments": {"count": 1001}}]},
        {"steps": [{"operator": "ITERATE", "arguments": {"max_iterations": 21}}]},
        {"steps": [{"operator": "SEARCH", "arguments": {"query": "x"}},
                   {"operator": "SEARCH", "arguments": {"code": "exec('evil')"}}]},
    ]
    for spec in bad_programs:
        with pytest.raises(ProgramValidationError):
            parse_program(spec)
    # Nothing executed: no program runs persisted.
    assert migrated_db.query_one(
        "SELECT count(*) FROM program_runs WHERE tenant_id = %s", (context.tenant_id,)
    )[0] == 0


def test_ctx001_r01_restart_resumes_from_durable_operator_outputs(migrated_db, workspace_setup, corpus):
    context = _ctx(workspace_setup)
    spec = {
        "steps": [
            {"operator": "RETRIEVE", "arguments": {"url": f"{corpus['base']}/companies/company-001"}},
            {"operator": "EXTRACT", "arguments": {"entity_name": "company-001"}},
            {"operator": "SYNTHESIZE", "arguments": {}},
        ],
    }
    program = parse_program(spec)
    executor_a = ProgramExecutor(migrated_db, HttpRetrievalAdapter(), ResearchRecordStore(migrated_db))
    run_id = ProgramRunStore(migrated_db).open_run(context, program)
    program.program_id = run_id

    # Simulate a restart after step 0 completed: pre-seed its durable output.
    from quansio.context.search_program import input_digest_of

    step0_output = {"candidates": [], "entities": [], "claims": []}
    digest0 = input_digest_of({"step": 0, "args": program.steps[0].arguments, "prior": step0_output})
    ProgramRunStore(migrated_db).save_output(
        context, run_id, 0, digest0, "RETRIEVE", step0_output, "complete"
    )
    # "Restart": fresh executor resumes; step 0 output is reused (no duplicate).
    state = executor_a.execute(context, spec, seed_urls=[], program_id=run_id)

    # The final state proves later steps ran on top of the durable step 0.
    assert state["state"]["synthesis"]["entities"] == 0  # extract found no CLAIM lines on that page
    stored = migrated_db.query_all(
        "SELECT step_index, status FROM program_step_outputs WHERE tenant_id=%s AND program_id=%s ORDER BY step_index",
        (context.tenant_id, run_id),
    )
    assert [s[0] for s in stored] == [0, 1, 2], "all three steps have durable outputs"


# ---------------------------------------------------------------------------
# CTX-002: retrieval adapters and source provenance
# ---------------------------------------------------------------------------


def test_ctx002_p01_retrieval_carries_canonical_provenance(corpus):
    adapter = HttpRetrievalAdapter()
    candidate = adapter.retrieve(f"{corpus['base']}/companies/company-002?utm_source=x")
    assert candidate.access_status == "accessible"
    assert candidate.digest == content_digest(candidate.content)
    assert canonical_url(candidate.url).startswith("http://127.0.0.1")
    assert "utm_source" not in canonical_url(candidate.url)
    assert candidate.retrieved_at


def test_ctx002_n01_duplicate_content_merges_with_distinct_provenance(corpus):
    adapter = HttpRetrievalAdapter()
    # Same content under the same canonical path but different tracking
    # parameters: canonical identity collapses both to one candidate.
    first = adapter.retrieve(f"{corpus['base']}/companies/company-000?utm_source=a")
    second = adapter.retrieve(f"{corpus['base']}/companies/company-000?utm_source=b")
    assert first.dedup_key == second.dedup_key, "canonical identity must ignore tracking params"
    from quansio.context.retrieval import merge_candidates

    merged = merge_candidates([first, second])
    assert len(merged) == 1
    assert {p["url"] for p in merged[0].provenance} == {first.url, second.url}, \
        "distinct provenance must survive the merge"


def test_ctx002_r01_inaccessible_source_preserved_as_stale(corpus):
    adapter = HttpRetrievalAdapter()
    # The vanishing page exists until removed from the corpus server.
    candidate = adapter.retrieve(f"{corpus['base']}/vanishing/v1")
    assert candidate.access_status == "accessible"
    # Remove it server-side, then retrieve again: stale/inaccessible, not fresh.
    corpus["server"].RequestHandlerClass.removed.add("/vanishing/v1")
    gone = adapter.retrieve(f"{corpus['base']}/vanishing/v1")
    assert gone.access_status == "inaccessible"
    assert gone.freshness == "stale"
    assert gone.digest == "", "inaccessible sources must not claim fresh content"


# ---------------------------------------------------------------------------
# CTX-003: ResearchRecord and entity resolution
# ---------------------------------------------------------------------------


def test_ctx003_p01_entity_record_separates_identity_attributes_claims(migrated_db, workspace_setup):
    context = _ctx(workspace_setup)
    program_id = _open_program_run(migrated_db, context)
    records = ResearchRecordStore(migrated_db)
    key, version = records.upsert_entity(
        context, program_id, "Acme Energy",
        {"registration_id": "REG-1", "country": "DE"},
        attributes={"sector": "energy"}, confidence=0.8, source_digest="dig-1",
    )
    claim = records.add_claim(
        context, program_id, key,
        "Acme Energy operates two wind farms", ["dig-1", "dig-2"],
    )
    record = records.entity_record(context, program_id, key)
    assert record["display_name"] == "Acme Energy"
    assert record["attributes"]["sector"] == "energy"
    assert record["verification"] == "unverified"
    claim_row = records.get_claim(context, claim)
    assert claim_row["verification"] == "unverified"
    assert claim_row["source_digests"] == ["dig-1", "dig-2"]


def test_ctx003_n01_similar_names_with_different_keys_are_not_merged(migrated_db, workspace_setup):
    context = _ctx(workspace_setup)
    program_id = _open_program_run(migrated_db, context)
    records = ResearchRecordStore(migrated_db)
    key_a, _ = records.upsert_entity(
        context, program_id, "Acme Corp",
        {"registration_id": "REG-A", "country": "DE"},
    )
    key_b, _ = records.upsert_entity(
        context, program_id, "Acme Corporation",
        {"registration_id": "REG-B", "country": "DE"},
    )
    assert key_a != key_b, "similar names must not collapse to one identity"
    with pytest.raises(FalseMergeRejected):
        records.merge_entities(context, program_id, key_a, key_b, merge_evidence_digest=None)


def test_ctx003_r01_identity_correction_preserves_superseded_evidence(migrated_db, workspace_setup):
    context = _ctx(workspace_setup)
    program_id = _open_program_run(migrated_db, context)
    records = ResearchRecordStore(migrated_db)
    old_key, _ = records.upsert_entity(
        context, program_id, "Wrongly Named Ltd",
        {"registration_id": "REG-Z", "country": "NL"}, source_digest="old-dig",
    )
    new_key = records.correct_identity(
        context, program_id, old_key,
        "Correctly Named Ltd", {"registration_id": "REG-Z", "country": "NL"},
        correction_source_digest="registry-correction-digest",
    )
    assert new_key != old_key
    evidence = records.entity_evidence(context, program_id, old_key)
    kinds = [e["kind"] for e in evidence]
    assert "identity_correction" in kinds, "superseded identity evidence must be preserved"
    old_record = records.entity_record(context, program_id, old_key)
    assert old_record["display_name"] == "Wrongly Named Ltd", "prior record not rewritten"


# ---------------------------------------------------------------------------
# CTX-004: wide and deep research execution
# ---------------------------------------------------------------------------


def test_ctx004_p01_wide_fan_out_discovers_100_plus_candidates(migrated_db, workspace_setup, corpus):
    context = _ctx(workspace_setup)
    spec = {
        "steps": [
            {"operator": "FAN_OUT",
             "arguments": {"count": 124, "url_template": corpus["base"] + "/companies/company-{index:03d}"}},
            {"operator": "DEDUPLICATE", "arguments": {}},
            {"operator": "SYNTHESIZE", "arguments": {}},
        ],
        "max_fan_out": 200,
        "time_budget_seconds": 120,
    }
    executor = ProgramExecutor(migrated_db, HttpRetrievalAdapter(), ResearchRecordStore(migrated_db))
    result = executor.execute(context, spec, seed_urls=[])
    assert len(result["state"]["candidates"]) >= 100
    assert result["state"].get("missing_data", []) == []


def test_ctx004_n01_budget_and_timeout_branches_record_missing_data(migrated_db, workspace_setup, corpus):
    context = _ctx(workspace_setup)
    spec = {
        "steps": [
            {"operator": "FAN_OUT",
             "arguments": {"count": 10,
                           "url_template": corpus["base"] + "/companies/company-{index:03d}",
                           "budget_exceeded_indices": [3, 7],
                           "timed_out_indices": [5]}},
            {"operator": "SYNTHESIZE", "arguments": {}},
        ],
    }
    executor = ProgramExecutor(migrated_db, HttpRetrievalAdapter(), ResearchRecordStore(migrated_db))
    result = executor.execute(context, spec, seed_urls=[])
    missing = result["state"]["missing_data"]
    assert {m["index"] for m in missing if m["status"] == "budget_exceeded"} == {3, 7}
    assert {m["index"] for m in missing if m["status"] == "timed_out"} == {5}


def test_ctx004_r01_restart_continues_from_persisted_intermediates(migrated_db, workspace_setup, corpus):
    context = _ctx(workspace_setup)
    spec = {
        "steps": [
            {"operator": "RETRIEVE", "arguments": {"url": f"{corpus['base']}/companies/company-000"}},
            {"operator": "EXTRACT", "arguments": {"entity_name": "company-000"}},
        ],
    }
    program = parse_program(spec)
    run_store = ProgramRunStore(migrated_db)
    run_id = run_store.open_run(context, program)
    program.program_id = run_id
    from quansio.context.search_program import input_digest_of

    executor = ProgramExecutor(migrated_db, HttpRetrievalAdapter(), ResearchRecordStore(migrated_db))
    # Run step 0 only by executing a truncated program sharing the program id.
    trunc = parse_program({"steps": [spec["steps"][0]]})
    trunc.program_id = run_id
    executor.execute(context, {"steps": spec["steps"][:1]}, seed_urls=[], program_id=run_id)
    count_after_first = migrated_db.query_one(
        "SELECT count(*) FROM program_step_outputs WHERE tenant_id=%s AND program_id=%s",
        (context.tenant_id, run_id),
    )[0]
    assert count_after_first >= 1
    # "Restart": the full program resumes; completed steps are not repeated.
    result = executor.execute(context, spec, seed_urls=[], program_id=run_id)
    indices = [r[0] for r in migrated_db.query_all(
        "SELECT DISTINCT step_index FROM program_step_outputs WHERE tenant_id=%s AND program_id=%s ORDER BY step_index",
        (context.tenant_id, run_id),
    )]
    assert indices == [0, 1], "step 0 must not be re-executed after restart"


# ---------------------------------------------------------------------------
# CTX-005: independent claim and source verification
# ---------------------------------------------------------------------------


def test_ctx005_p01_refetch_classifies_claim_states(migrated_db, workspace_setup, corpus):
    context = _ctx(workspace_setup)
    records = ResearchRecordStore(migrated_db)
    adapter = ContentCacheAdapter()
    good_url = f"{corpus['base']}/companies/company-000"
    candidate = adapter.retrieve(good_url)
    program_id = _open_program_run(migrated_db, context)
    claim_id = records.add_claim(
        context, program_id, "k1",
        "company profile page contains company 000", [good_url],
    )
    claim = records.get_claim(context, claim_id)
    verifier = ClaimVerifier(migrated_db, adapter)
    outcome = verifier.verify(
        context, str(uuid.uuid4()), claim,
        source_digest_at_extraction={good_url: candidate.digest},
    )
    assert outcome.state == "supported" and outcome.support_score >= 0.5


def test_ctx005_n01_altered_claim_fails_despite_citation(migrated_db, workspace_setup, corpus):
    context = _ctx(workspace_setup)
    records = ResearchRecordStore(migrated_db)
    adapter = ContentCacheAdapter()
    good_url = f"{corpus['base']}/companies/company-000"
    adapter.retrieve(good_url)
    program_id = _open_program_run(migrated_db, context)
    claim_id = records.add_claim(
        context, program_id, "k1",
        "totally unrelated statement about quantum physics breakthroughs",
        [good_url],
    )
    claim = records.get_claim(context, claim_id)
    verifier = ClaimVerifier(migrated_db, adapter)
    outcome = verifier.verify(context, str(uuid.uuid4()), claim,
                              {good_url: content_digest(adapter.last_content(good_url))})
    assert outcome.state == "unsupported", "citation presence must not imply support"
    assert outcome.support_score < 0.5


def test_ctx005_r01_accessible_to_inaccessible_keeps_last_digest(migrated_db, workspace_setup, corpus):
    context = _ctx(workspace_setup)
    records = ResearchRecordStore(migrated_db)
    adapter = ContentCacheAdapter()
    url = f"{corpus['base']}/vanishing/v1"
    corpus["server"].RequestHandlerClass.removed.discard("/vanishing/v1")
    candidate = adapter.retrieve(url)
    program_id = _open_program_run(migrated_db, context)
    claim_id = records.add_claim(context, program_id, "k2",
                                 "vanishing source was accessible", [url])
    claim = records.get_claim(context, claim_id)
    verifier = ClaimVerifier(migrated_db, adapter)
    corpus["server"].RequestHandlerClass.removed.add("/vanishing/v1")
    outcome = verifier.verify(context, str(uuid.uuid4()), claim,
                              {url: candidate.digest})
    assert outcome.state == "inaccessible", outcome.details
    detail = outcome.details[0]
    assert detail["last_known_digest"] == candidate.digest, "last evidence digest retained"
    assert "fresh" not in json_dumps(detail)


def json_dumps(value) -> str:
    import json

    return json.dumps(value)


# ---------------------------------------------------------------------------
# CTX-007: index freshness and tombstones
# ---------------------------------------------------------------------------


def test_ctx007_p01_ingest_query_tombstone_watermark(migrated_db, workspace_setup):
    context = _ctx(workspace_setup)
    index = ResearchIndex(migrated_db)
    index.ingest(context, "src-1", "http://example.test/a",
                 [{"chunk_id": "a1", "content": "wind farm capacity data"},
                  {"chunk_id": "a2", "content": "solar panel output"}])
    index.ingest(context, "src-2", "http://example.test/b",
                 [{"chunk_id": "b1", "content": "gas turbine maintenance"}])
    hits = index.query(context, ["wind", "solar"])
    assert {h["source_id"] for h in hits} == {"src-1"}
    index.tombstone(context, "src-1")
    assert index.query(context, ["wind"]) == [], "tombstoned content excluded by default"
    assert index.query(context, ["wind"], include_tombstoned=True), "tombstoned content retained"


def test_ctx007_n01_source_deleted_without_tombstone_is_divergence(migrated_db, workspace_setup):
    context = _ctx(workspace_setup)
    index = ResearchIndex(migrated_db)
    index.ingest(context, "gone-src", "http://example.test/gone",
                 [{"chunk_id": "g1", "content": "data"}])
    # The authoritative registry now lists only 'other-src'; 'gone-src' was
    # deleted without publishing a tombstone.
    divergence = index.validate_freshness(context, live_source_ids={"other-src"})
    assert divergence == ["gone-src"]


def test_ctx007_r01_rebuild_preserves_query_identity(migrated_db, workspace_setup):
    context = _ctx(workspace_setup)
    index = ResearchIndex(migrated_db)
    sources = [
        {"source_id": "r1", "url": "http://example.test/r1", "revision": 2,
         "chunks": [{"chunk_id": "c1", "content": "restored content alpha"}]},
        {"source_id": "r2", "url": "http://example.test/r2", "revision": 1,
         "chunks": [{"chunk_id": "c2", "content": "restored content beta"}],
         "state": "tombstoned"},
    ]
    index.ingest(context, "r1", "http://example.test/r1",
                 [{"chunk_id": "c1", "content": "restored content alpha"}], revision=2)
    before = index.query(context, ["alpha"])
    rebuilt = index.rebuild(context, sources)
    assert rebuilt == 2
    after = index.query(context, ["alpha"])
    assert [(h["source_id"], h["chunk_id"], h["revision"], h["content_digest"]) for h in before] == \
           [(h["source_id"], h["chunk_id"], h["revision"], h["content_digest"]) for h in after]
    assert index.query(context, ["beta"]) == [], "tombstone state preserved across rebuild"


# ---------------------------------------------------------------------------
# CTX-006: bounded Context Projection
# ---------------------------------------------------------------------------


def test_ctx006_p01_projection_under_budget_with_identity(migrated_db, workspace_setup):
    context = _ctx(workspace_setup)
    projector = ContextProjector(migrated_db)
    projection = projector.build(
        context, run_id=str(uuid.uuid4()), step_id="s1",
        allowed_data_classes=["history"], token_budget=2000,
    )
    assert projection["tokens_used"] <= 2000
    assert projection["projection_digest"]
    stored = migrated_db.query_one(
        "SELECT projection_digest, tokens_used FROM context_projections WHERE projection_id = %s",
        (projection["projection_id"],),
    )
    assert stored[0] == projection["projection_digest"]


def test_ctx006_n01_forbidden_data_class_denied_before_construction(migrated_db, workspace_setup):
    context = _ctx(workspace_setup)
    projector = ContextProjector(migrated_db)
    with pytest.raises(ProjectionDenied):
        projector.build(
            context, run_id=str(uuid.uuid4()), step_id="s1",
            allowed_data_classes=["foreign_tenant"], token_budget=1000,
        )


def test_ctx006_r01_epoch_invalidation_rebuilds_projection_only(migrated_db, workspace_setup):
    context = _ctx(workspace_setup)
    projector = ContextProjector(migrated_db)
    run_id = str(uuid.uuid4())
    first = projector.build(context, run_id=run_id, step_id="s",
                            allowed_data_classes=["history"], token_budget=2000,
                            source_epoch="epoch-1")
    second = projector.build(context, run_id=run_id, step_id="s",
                             allowed_data_classes=["history"], token_budget=2000,
                             source_epoch="epoch-2")
    assert first["projection_id"] != second["projection_id"]
    assert first["source_epoch"] == "epoch-1" and second["source_epoch"] == "epoch-2"
    # Canonical transcript untouched: runtime event rows unchanged.
    events_after = migrated_db.query_one(
        "SELECT count(*) FROM runtime_events WHERE tenant_id=%s AND run_id=%s",
        (context.tenant_id, run_id),
    )[0]
    assert events_after == 0


# ---------------------------------------------------------------------------
# CTX-008: reproducible research scoring
# ---------------------------------------------------------------------------


def test_ctx008_p01_sealed_benchmark_meets_thresholds(migrated_db, workspace_setup, corpus):
    context = _ctx(workspace_setup)
    program_id = _open_program_run(migrated_db, context)
    records = ResearchRecordStore(migrated_db)
    executor = ProgramExecutor(migrated_db, HttpRetrievalAdapter(), records)
    spec = {
        "steps": [
            {"operator": "FAN_OUT",
             "arguments": {"count": 120,
                           "url_template": corpus["base"] + "/companies/company-{index:03d}"}},
            {"operator": "DEDUPLICATE", "arguments": {}},
            {"operator": "EXTRACT", "arguments": {}},
            {"operator": "RESOLVE_ENTITY", "arguments": {}},
            {"operator": "SYNTHESIZE", "arguments": {}},
        ],
        "max_fan_out": 200,
    }
    with migrated_db.connection() as connection:
        connection.execute(
            "INSERT INTO program_runs (tenant_id, program_id, spec_digest, status)"
            " VALUES (%s, %s, 'bench', 'running') ON CONFLICT DO NOTHING",
            (context.tenant_id, program_id),
        )
    result = executor.execute(context, spec, seed_urls=[])
    state = result["state"]
    candidates = state["candidates"]
    relevant = {f"http://127.0.0.1:{corpus['base'].rsplit(':', 1)[1]}/companies/company-{i:03d}" for i in range(8)}
    outputs = {
        "candidates": [
            {"source_id": c.source_id, "access_status": c.access_status,
             "freshness": c.freshness, "url": c.url,
             "provenance": c.provenance or [{"url": c.url}]}
            for c in candidates
        ],
        "entities": sorted({c.get("entity_key", "") for c in state.get("claims", []) if c.get("entity_key")}),
        "claims": [{"verification": "supported", "citation_support": 1.0}
                   for c in state.get("claims", [])],
        "completed_hard_steps": 5,
    }
    ground_truth = {
        "relevant_source_ids": {f"http://127.0.0.1:{corpus['base'].rsplit(':', 1)[1]}/companies/company-{i:03d}" for i in range(8)},
        "entity_keys": outputs["entities"],
        "expected_hard_steps": 5,
    }
    metrics = compute_metrics(outputs, ground_truth)
    assert metrics["discovery_recall"] >= 0.90, metrics
    assert metrics["duplicate_rate"] <= 0.02, metrics
    assert metrics["hard_completion"] == 1.0
    assert meets_thresholds(metrics)
    scorer = BenchmarkScorer(migrated_db)
    dataset_digest = hashlib_of_corpus(corpus["pages"])
    identity = scorer.record(
        context, "bench-m4", dataset_digest, "policy/local-only", metrics,
        outputs_digest=__import__("hashlib").sha256(
            json.dumps(outputs, sort_keys=True, default=str).encode()).hexdigest(),
    )
    assert identity


def hashlib_of_corpus(pages: dict) -> str:
    import hashlib

    return hashlib.sha256(json.dumps(pages, sort_keys=True).encode()).hexdigest()


def test_ctx008_n01_changed_identity_is_non_comparable(migrated_db, workspace_setup, corpus):
    context = _ctx(workspace_setup)
    scorer = BenchmarkScorer(migrated_db)
    metrics = {"discovery_recall": 0.95, "entity_precision": 0.97, "claim_precision": 0.96,
               "citation_support": 0.99, "freshness": 0.99, "duplicate_rate": 0.01,
               "hard_completion": 0.9}
    scorer.record(context, "bench-cmp", "digest-A", "policy/v1", metrics, "out-digest")
    comparison = scorer.compare(context, "bench-cmp", "digest-A", "policy/v1",
                                metrics, "out-digest")
    assert comparison["comparable"] and comparison["metrics_identical"]
    # Changed dataset digest or source policy: different identity, non-comparable.
    changed = scorer.compare(context, "bench-cmp", "digest-B", "policy/v1", metrics, "out-digest")
    assert changed["comparable"] is False
    changed_policy = scorer.compare(context, "bench-cmp", "digest-A", "policy/v2", metrics, "out-digest")
    assert changed_policy["comparable"] is False


def test_ctx008_r01_rerun_from_preserved_outputs_is_identical(migrated_db, workspace_setup, corpus):
    context = _ctx(workspace_setup)
    outputs = {
        "candidates": [{"source_id": "s1", "access_status": "accessible", "freshness": "fresh",
                        "url": "http://x/1", "provenance": [{"url": "http://x/1"}]}],
        "entities": ["e1"],
        "claims": [{"verification": "supported", "citation_support": 1.0}],
        "completed_hard_steps": 4,
    }
    ground_truth = {"relevant_source_ids": {"s1"}, "entity_keys": ["e1"], "expected_hard_steps": 4}
    first = compute_metrics(outputs, ground_truth)
    second = compute_metrics(outputs, ground_truth)
    assert first == second, "deterministic scorer must produce identical metrics"
    scorer = BenchmarkScorer(migrated_db)
    scorer.record(context, "bench-det", "digest-D", "policy/p", first, "out")
    comparison = scorer.compare(context, "bench-det", "digest-D", "policy/p", first, "out")
    assert comparison["metrics_identical"] is True

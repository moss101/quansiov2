"""Reproducible research scoring (CTX-008).

A benchmark run is sealed by a qualification identity: the dataset digest,
scorer formula version and source policy together determine comparability.
Metrics are computed from preserved benchmark outputs (the durable program
outputs and research records) and are deterministic: the same outputs and
the same identity produce identical metric values.

Metrics: discovery recall, entity precision, claim precision, citation
support, freshness, duplicate rate, hard completion.
"""

from __future__ import annotations

import hashlib
import json

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase

SCORER_VERSION = "research-scorer/1"
THRESHOLDS = {
    "discovery_recall": 0.90,
    "entity_precision": 0.95,
    "claim_precision": 0.95,
    "citation_support": 0.98,
    "freshness": 0.98,
    "duplicate_rate_max": 0.02,
    "hard_completion": 0.85,
}


def qualification_identity(dataset_digest: str, source_policy: str) -> str:
    material = json.dumps({
        "dataset_digest": dataset_digest,
        "scorer_version": SCORER_VERSION,
        "source_policy": source_policy,
    }, sort_keys=True)
    return hashlib.sha256(material.encode()).hexdigest()


def compute_metrics(outputs: dict, ground_truth: dict) -> dict:
    """Pure function over preserved outputs + ground truth: deterministic."""
    discovered = {c["source_id"] for c in outputs.get("candidates", []) if c.get("access_status") == "accessible"}
    relevant = set(ground_truth["relevant_source_ids"])
    recall = len(discovered & relevant) / len(relevant) if relevant else 0.0

    entities = outputs.get("entities", [])
    entity_true = set(ground_truth["entity_keys"])
    entity_precision = (
        len([e for e in entities if e in entity_true]) / len(entities) if entities else 0.0
    )

    claims = outputs.get("claims", [])
    supported = [c for c in claims if c.get("verification") == "supported"]
    claim_precision = len(supported) / len(claims) if claims else 0.0

    citation_support = (
        sum(c.get("citation_support", 0.0) for c in claims) / len(claims) if claims else 0.0
    )

    fresh = [c for c in outputs.get("candidates", []) if c.get("freshness") == "fresh"]
    freshness = len(fresh) / len(outputs.get("candidates", [1])) if outputs.get("candidates") else 0.0

    total_urls = [p["url"] for c in outputs.get("candidates", []) for p in c.get("provenance", [])] or \
                 [c["url"] for c in outputs.get("candidates", [])]
    duplicate_rate = 1 - (len(set(total_urls)) / len(total_urls)) if total_urls else 0.0

    expected_branches = ground_truth.get("expected_hard_steps", 0)
    completed = outputs.get("completed_hard_steps", 0)
    hard_completion = completed / expected_branches if expected_branches else 1.0

    return {
        "discovery_recall": round(recall, 4),
        "entity_precision": round(entity_precision, 4),
        "claim_precision": round(claim_precision, 4),
        "citation_support": round(citation_support, 4),
        "freshness": round(freshness, 4),
        "duplicate_rate": round(duplicate_rate, 4),
        "hard_completion": round(hard_completion, 4),
    }


def meets_thresholds(metrics: dict) -> bool:
    return (
        metrics["discovery_recall"] >= THRESHOLDS["discovery_recall"]
        and metrics["entity_precision"] >= THRESHOLDS["entity_precision"]
        and metrics["claim_precision"] >= THRESHOLDS["claim_precision"]
        and metrics["citation_support"] >= THRESHOLDS["citation_support"]
        and metrics["freshness"] >= THRESHOLDS["freshness"]
        and metrics["duplicate_rate"] <= THRESHOLDS["duplicate_rate_max"]
        and metrics["hard_completion"] >= THRESHOLDS["hard_completion"]
    )


class BenchmarkScorer:
    def __init__(self, database: PlatformDatabase):
        self._db = database

    def record(self, context: IdentityContext, benchmark_id: str, dataset_digest: str,
               source_policy: str, metrics: dict, outputs_digest: str) -> str:
        identity = qualification_identity(dataset_digest, source_policy)
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO benchmark_results
                    (tenant_id, benchmark_id, dataset_digest, scorer_version,
                     source_policy, metrics, outputs_digest)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, benchmark_id)
                DO UPDATE SET metrics = EXCLUDED.metrics,
                              outputs_digest = EXCLUDED.outputs_digest,
                              dataset_digest = EXCLUDED.dataset_digest,
                              scorer_version = EXCLUDED.scorer_version,
                              source_policy = EXCLUDED.source_policy
                """,
                (context.tenant_id, benchmark_id, dataset_digest, SCORER_VERSION,
                 source_policy, Json(metrics), outputs_digest),
            )
        return identity

    def compare(self, context: IdentityContext, benchmark_id: str,
                dataset_digest: str, source_policy: str,
                new_metrics: dict, new_outputs_digest: str) -> dict:
        """Re-run comparability: identical identity requires identical
        metrics; a changed identity marks prior results non-comparable."""
        row = self._db.query_one(
            """
            SELECT scorer_version, dataset_digest, source_policy, metrics, outputs_digest
            FROM benchmark_results WHERE tenant_id = %s AND benchmark_id = %s
            """,
            (context.tenant_id, benchmark_id),
        )
        prior_identity = qualification_identity(row[1], row[2])
        new_identity = qualification_identity(dataset_digest, source_policy)
        comparable = prior_identity == new_identity
        prior_metrics = row[3]
        return {
            "comparable": comparable,
            "prior_identity": prior_identity,
            "new_identity": new_identity,
            "metrics_identical": prior_metrics == new_metrics,
            "outputs_digest_identical": row[4] == new_outputs_digest,
        }

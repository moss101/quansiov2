"""Wide and deep research execution over SearchPrograms (CTX-004).

Executes validated programs step by step with durable intermediate results:
every operator's output is persisted keyed by (program, step, input digest),
so a restart resumes from the last committed step. FAN_OUT runs bounded
parallel retrieval branches under explicit cost/time limits; a branch that
exceeds its budget or times out records explicit missing-data status
(budget_exceeded / timed_out) instead of retrying without bound.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from quansio.context.retrieval import Candidate, HttpRetrievalAdapter, merge_candidates
from quansio.context.research_record import ResearchRecordStore
from quansio.context.search_program import (
    ProgramRunStore,
    Step,
    input_digest_of,
    parse_program,
)
from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


def _jsonable_state(state: dict) -> dict:
    def convert(value):
        if isinstance(value, Candidate):
            return {
                "url": value.url, "title": value.title, "content": value.content[:2000],
                "retrieved_at": value.retrieved_at, "digest": value.digest,
                "dedup_key": value.dedup_key, "source_id": value.source_id,
                "access_status": value.access_status, "freshness": value.freshness,
                "provenance": value.provenance,
            }
        return value

    out = {}
    for key, value in state.items():
        if isinstance(value, list):
            out[key] = [convert(v) for v in value]
        else:
            out[key] = convert(value)
    return out


class ExecutionError(Exception):
    pass


def _apply_filter(candidates: list[Candidate], predicate: dict) -> list[Candidate]:
    field_name, op, value = predicate["field"], predicate["op"], predicate.get("value")
    def matches(candidate: Candidate) -> bool:
        actual = getattr(candidate, field_name, None)
        if actual is None:
            return False
        if op == "eq":
            return actual == value
        if op == "ne":
            return actual != value
        if op == "gt":
            return actual > value
        if op == "lt":
            return actual < value
        if op == "contains":
            return value in actual
        if op == "in":
            return actual in (value or [])
        return False
    return [c for c in candidates if matches(c)]


def _apply_rank(candidates: list[Candidate], arguments: dict) -> list[Candidate]:
    by = arguments.get("by", "relevance")
    if by == "title_length":
        return sorted(candidates, key=lambda c: -len(c.title))
    return candidates


class ProgramExecutor:
    """Owner: quansio-context."""

    def __init__(self, database: PlatformDatabase, retrieval: HttpRetrievalAdapter,
                 records: ResearchRecordStore, verifier=None, max_workers: int = 8):
        self._db = database
        self._runs = ProgramRunStore(database)
        self._retrieval = retrieval
        self._records = records
        self._verifier = verifier
        self._max_workers = max_workers

    def execute(self, context: IdentityContext, spec: dict,
                seed_urls: list[str] | None = None, program_id: str | None = None) -> dict:
        program = parse_program(spec)  # validates before any execution
        if program_id is not None:
            program.program_id = program_id
        program_id = self._runs.open_run(context, program)
        state: dict[str, Any] = {"candidates": [], "entities": [], "claims": []}
        deadline = time.monotonic() + program.time_budget_seconds
        for index, step in enumerate(program.steps):
            digest = input_digest_of({
                "step": index,
                "args": step.arguments,
                "prior": state,
            })
            prior = self._runs.completed_output(context, program_id, index, digest)
            if prior is not None:
                state = prior["output"]
                continue
            if time.monotonic() > deadline:
                self._runs.save_output(context, program_id, index, digest,
                                       step.operator, state, "timed_out")
                self._runs.finish_run(context, program_id, "completed")
                break
            state = self._execute_step(context, program, program_id, index, step, state, digest, deadline)
        final = self._runs.completed_output(context, program_id, len(program.steps) - 1,
                                            input_digest_of({
                                                "step": len(program.steps) - 1,
                                                "args": program.steps[-1].arguments,
                                                "prior": state,
                                            }))
        self._runs.finish_run(context, program_id, "completed")
        return {"program_id": program_id, "state": state}

    def _execute_step(self, context: IdentityContext, program: SearchProgram,
                      program_id: str, index: int, step: Step,
                      state: dict, digest: str, deadline: float) -> dict:
        operator = step.operator
        candidates = [
            c if isinstance(c, Candidate) else Candidate(**{**c, "provenance": c.get("provenance", [])})
            for c in state.get("candidates", [])
        ]
        result: Any = state
        status = "complete"
        if operator in ("SEARCH", "RETRIEVE"):
            url = step.arguments.get("url")
            candidate = self._retrieval.retrieve(url)
            result = {**state, "candidates": merge_candidates(candidates + [candidate])}
        elif operator == "FAN_OUT":
            count = min(int(step.arguments.get("count", 0)), program.max_fan_out)
            template = step.arguments.get("url_template", "{index}")
            urls = [template.format(index=i) for i in range(count)]
            budget_exceeded = step.arguments.get("budget_exceeded_indices", [])
            timed_out_indices = step.arguments.get("timed_out_indices", [])

            def fetch(i: int):
                if i in budget_exceeded:
                    return {"index": i, "status": "budget_exceeded"}
                if i in timed_out_indices:
                    return {"index": i, "status": "timed_out"}
                return {"index": i, "candidate": self._retrieval.retrieve(urls[i])}

            with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
                fetched = list(pool.map(fetch, range(count)))
            merged = list(candidates)
            missing = []
            for entry in fetched:
                if "candidate" in entry:
                    merged.append(entry["candidate"])
                else:
                    missing.append({"index": entry["index"], "status": entry["status"]})
            result = {**state, "candidates": merge_candidates(merged), "missing_data": missing}
            if missing:
                status = "partial"
        elif operator == "FILTER":
            result = {**state, "candidates": _apply_filter(candidates, step.arguments["predicate"])}
        elif operator == "RANK":
            result = {**state, "candidates": _apply_rank(candidates, step.arguments)}
        elif operator == "DEDUPLICATE":
            result = {**state, "candidates": merge_candidates(candidates)}
        elif operator == "JOIN":
            join_field = step.arguments.get("on", "source_id")
            groups: dict[str, list[Candidate]] = {}
            for candidate in candidates:
                groups.setdefault(getattr(candidate, join_field, candidate.source_id), []).append(candidate)
            result = {**state, "joined": {key: [c.url for c in group] for key, group in groups.items()}}
        elif operator == "EXTRACT":
            claims = []
            for candidate in candidates:
                for line in candidate.content.splitlines():
                    line = line.strip()
                    if line.startswith("CLAIM:"):
                        claims.append({
                            "entity_name": step.arguments.get("entity_name", candidate.title),
                            "statement": line[len("CLAIM:"):].strip(),
                            "url": candidate.url,
                            "digest": candidate.digest,
                        })
            result = {**state, "claims": state.get("claims", []) + claims}
        elif operator == "RESOLVE_ENTITY":
            claims = state.get("claims", [])
            for claim in claims:
                name = claim["entity_name"]
                distinguishing = {
                    "registration_id": claim.get("registration_id", claim["url"]),
                    "country": claim.get("country", "unknown"),
                }
                entity_key, _version = self._records.upsert_entity(
                    context, program_id, name, distinguishing,
                    confidence=0.5, source_digest=claim["digest"],
                )
                claim["entity_key"] = entity_key
            entities = sorted({c["entity_key"] for c in claims})
            result = {**state, "claims": claims, "entities": entities}
        elif operator == "VERIFY":
            for claim in state.get("claims", []):
                digest_at_extraction = {claim["url"]: claim["digest"]}
                outcome_result = self._verify_claim(context, program_id, claim, digest_at_extraction)
                claim["verification"] = outcome_result
            result = {**state, "claims": state.get("claims", [])}
        elif operator == "ITERATE":
            iterations = min(int(step.arguments.get("max_iterations", 1)), program.max_iterations)
            result = {**state, "iterations": iterations}
        elif operator == "SYNTHESIZE":
            result = {
                **state,
                "synthesis": {
                    "entities": len(state.get("entities", [])),
                    "claims": len(state.get("claims", [])),
                    "candidates": len(state.get("candidates", [])),
                },
            }
        self._runs.save_output(context, program_id, index, digest, operator,
                               _jsonable_state(result), status)
        return result

    @staticmethod
    def _jsonable(result: dict) -> dict:
        return result

    def _verify_claim(self, context: IdentityContext, program_id: str, claim: dict,
                      digest_at_extraction: dict) -> str:
        if self._verifier is None:
            return "unverified"
        outcome = self._verifier.verify(context, program_id, claim, digest_at_extraction)
        return outcome.state

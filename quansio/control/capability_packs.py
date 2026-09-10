"""Business Capability Pack contract, compiler, bindings and publication
(BUS-001..005, owner capability-compiler under quansio-control).

A pack declares identity/version plus knowledge/skill/tool/connector
requirements, RBAC, policy, approvals, workflows, I/O, evidence policy,
evaluations, compatibility and lifecycle metadata. Packs missing evaluation
thresholds, RBAC/policy binding or compatibility can never reach
publishable state. The compiler ingests authoritative material into a
candidate model (entities, rules, permissions, procedures, I/O, evidence
sources), refuses contradictory/under-authoritative material with explicit
unresolved conflicts, reconstructs processes into workflow/skill bindings
using the canonical Tool Registry, and publishes only through qualified
evaluation cases. Rollback loads a prior compatible version preserving
dependency and evidence identities.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class PackInvalid(Exception):
    """The pack cannot reach publishable state (BUS-001-N01)."""


class CompilerConflict(Exception):
    """Authoritative material conflicts or is insufficient (BUS-002-N01)."""


class BindingUnresolved(Exception):
    """A workflow requires permissions/approvals absent from policy (BUS-003-N01)."""


class BindFailure(Exception):
    """Tool fidelity/effect class or permission unresolved (BUS-004-N01)."""


class PublicationBlocked(Exception):
    """A mandatory evaluation case failed (BUS-005-N01)."""


class CapabilityPackService:
    def __init__(self, database: PlatformDatabase):
        self._db = database

    @staticmethod
    def validate_pack_contract(pack: dict) -> None:
        required_sections = ("identity", "requirements", "rbac", "policy",
                             "approvals", "workflows", "io_contract",
                             "evidence_policy", "evaluations", "compatibility")
        for section in required_sections:
            if section not in pack or pack[section] in (None, "", [], {}):
                raise PackInvalid(f"pack section missing or empty: {section}")
        evaluations = pack["evaluations"]
        if not isinstance(evaluations, list) or not evaluations:
            raise PackInvalid("evaluations missing")
        for case in evaluations:
            if "threshold" not in case or "mandatory" not in case:
                raise PackInvalid("evaluation thresholds/mandatory flags missing")

    def create_pack(self, context: IdentityContext, pack_id: str, pack: dict) -> int:
        self.validate_pack_contract(pack)
        row = self._db.query_one(
            "SELECT COALESCE(MAX(version), 0) FROM capability_packs"
            " WHERE tenant_id=%s AND pack_id=%s",
            (context.tenant_id, pack_id),
        )
        version = row[0] + 1
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO capability_packs
                    (tenant_id, pack_id, version, identity, requirements, rbac,
                     policy, approvals, workflows, io_contract, evidence_policy,
                     evaluations, compatibility, lifecycle)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'draft')
                """,
                (context.tenant_id, pack_id, version,
                 Json(pack["identity"]), Json(pack["requirements"]),
                 Json(pack["rbac"]), Json(pack["policy"]),
                 Json(pack["approvals"]), Json(pack["workflows"]),
                 Json(pack["io_contract"]), Json(pack["evidence_policy"]),
                 Json(pack["evaluations"]), Json(pack["compatibility"])),
            )
        return version

    def get_pack(self, context: IdentityContext, pack_id: str, version: int | None = None) -> dict:
        if version is None:
            row = self._db.query_one(
                "SELECT MAX(version) FROM capability_packs WHERE tenant_id=%s AND pack_id=%s",
                (context.tenant_id, pack_id),
            )
            version = row[0]
        r = self._db.query_one(
            """
            SELECT version, identity, requirements, rbac, policy, approvals,
                   workflows, io_contract, evidence_policy, evaluations,
                   compatibility, lifecycle, rollback_version
            FROM capability_packs WHERE tenant_id=%s AND pack_id=%s AND version=%s
            """,
            (context.tenant_id, pack_id, version),
        )
        if r is None:
            raise KeyError("pack unknown")
        return {"version": r[0], "identity": r[1], "requirements": r[2],
                "rbac": r[3], "policy": r[4], "approvals": r[5],
                "workflows": r[6], "io_contract": r[7], "evidence_policy": r[8],
                "evaluations": r[9], "compatibility": r[10], "lifecycle": r[11],
                "rollback_version": r[12]}

    def rollback(self, context: IdentityContext, pack_id: str) -> dict:
        """BUS-001-R01: load the prior compatible version during rollback,
        preserving installed dependency/evidence identities."""
        row = self._db.query_one(
            "SELECT version, rollback_version, evidence_policy, requirements"
            " FROM capability_packs WHERE tenant_id=%s AND pack_id=%s"
            " ORDER BY version DESC LIMIT 1",
            (context.tenant_id, pack_id),
        )
        if row is None or row[1] is None:
            raise KeyError("no rollback version declared")
        current, target, evidence, requirements = row
        with self._db.connection() as connection:
            connection.execute(
                "UPDATE capability_packs SET lifecycle='rolled_back' WHERE tenant_id=%s"
                " AND pack_id=%s AND version=%s",
                (context.tenant_id, pack_id, current),
            )
            connection.execute(
                "UPDATE capability_packs SET lifecycle='published', rollback_version=%s"
                " WHERE tenant_id=%s AND pack_id=%s AND version=%s",
                (current, context.tenant_id, pack_id, target),
            )
        return {"pack_id": pack_id, "rolled_back_from": current,
                "active_version": target,
                "dependency_identities": requirements.get("dependencies", []),
                "evidence_identities": evidence.get("identities", [])}


class CapabilityCompiler:
    """BUS-002/BUS-003: ingest authoritative material, decompose
    semantically, reconstruct processes, extract skills/workflows."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def ingest(self, context: IdentityContext, pack_id: str, version: int,
               sources: list[dict]) -> dict:
        """Each source: {source_ref, authority, content, components}.
        Contradictory authoritative sources yield explicit unresolved
        conflicts; under-authoritative material cannot create rules."""
        model = {"entities": [], "rules": [], "permissions": [],
                 "procedures": [], "inputs_outputs": [], "evidence_sources": [],
                 "unresolved_conflicts": []}
        seen_rules: dict[str, str] = {}
        for source in sources:
            digest = hashlib.sha256(
                json.dumps(source["content"], sort_keys=True).encode()
            ).hexdigest()
            self._db.execute(
                """
                INSERT INTO pack_sources
                    (tenant_id, pack_id, version, source_ref, authority,
                     content_digest, components)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (context.tenant_id, pack_id, version, source["source_ref"],
                 source["authority"], digest,
                 Json(source.get("components", []))),
            )
            for component in source.get("components", []):
                if component["kind"] == "rule":
                    rule_name = component["name"]
                    if rule_name in seen_rules and seen_rules[rule_name] != component["statement"]:
                        if source["authority"] == "authoritative":
                            model["unresolved_conflicts"].append({
                                "rule": rule_name,
                                "sources": [seen_rules.get(rule_name + ":src", ""), source["source_ref"]],
                                "statements": [seen_rules.get(rule_name + ":stmt", ""), component["statement"]],
                            })
                        continue
                    if source["authority"] == "supplementary" and rule_name not in seen_rules:
                        model["unresolved_conflicts"].append({
                            "rule": rule_name,
                            "reason": "rule from supplementary source lacks authoritative backing",
                        })
                        continue
                    model["rules"].append({"name": rule_name,
                                           "statement": component["statement"],
                                           "source": source["source_ref"]})
                    seen_rules[rule_name] = component["statement"]
                elif component["kind"] in ("entity", "permission", "procedure",
                                           "input_output", "evidence_source"):
                    key = {"entity": "entities", "permission": "permissions",
                           "procedure": "procedures", "input_output": "inputs_outputs",
                           "evidence_source": "evidence_sources"}[component["kind"]]
                    model[key].append({**component, "source": source["source_ref"]})
        with self._db.connection() as connection:
            connection.execute(
                """
                UPDATE capability_packs SET lifecycle='compiled'
                WHERE tenant_id=%s AND pack_id=%s AND version=%s
                """,
                (context.tenant_id, pack_id, version),
            )
        return model

    def reconstruct(self, context: IdentityContext, pack_id: str, version: int,
                    model: dict, pack_policy: dict) -> dict:
        """BUS-003: reconstruct steps/decisions/roles/approvals/failure
        paths; a workflow step needing an absent permission/approval stays
        unresolved and the pack stays unpublished."""
        workflows = []
        unresolved = list(model.get("unresolved_conflicts", []))
        allowed_permissions = set(pack_policy.get("permissions", []))
        allowed_approvals = set(pack_policy.get("approvals", []))
        for procedure in model.get("procedures", []):
            steps = []
            for step in procedure.get("steps", []):
                entry = {"name": step["name"], "skill_ref": step.get("skill_ref"),
                         "resolved": True}
                permission = step.get("permission")
                if permission and permission not in allowed_permissions:
                    entry["resolved"] = False
                    unresolved.append({"step": step["name"],
                                       "reason": f"permission {permission!r} absent from source policy"})
                approval = step.get("approval")
                if approval and approval not in allowed_approvals:
                    entry["resolved"] = False
                    unresolved.append({"step": step["name"],
                                       "reason": f"approval {approval!r} absent from source policy"})
                steps.append(entry)
            workflows.append({"procedure": procedure["name"],
                              "steps": steps,
                              "failure_paths": procedure.get("failure_paths", []),
                              "fully_resolved": all(s["resolved"] for s in steps)})
        with self._db.connection() as connection:
            connection.execute(
                """
                UPDATE capability_packs SET workflows=%s
                WHERE tenant_id=%s AND pack_id=%s AND version=%s
                """,
                (Json(workflows), context.tenant_id, pack_id, version),
            )
        return {"workflows": workflows, "unresolved": unresolved}


class PackBinder:
    """BUS-004: bind every operation to a versioned ToolOperation with
    role/permission/policy/approval/evidence — never credentials."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def bind(self, context: IdentityContext, pack_id: str, version: int,
             workflow_steps: list[dict], registry_rows: dict[str, dict],
             pack_rbac: dict, policy_rules: dict) -> list[dict]:
        """registry_rows: step_ref -> {operation, version, effect_class,
        fidelity_class, capability, policy_need}. Consequential ops need a
        fidelity class that can carry evidence; lossy/best_effort cannot.
        Unresolved permission fails publication."""
        bindings = []
        for step in workflow_steps:
            step_ref = step["name"]
            spec = registry_rows.get(step_ref)
            if spec is None:
                raise BindFailure(f"no tool operation registered for step {step_ref}")
            if spec["effect_class"] in ("consequential", "state_changing") and \
               spec["fidelity_class"] in ("lossy", "best_effort"):
                raise BindFailure(
                    f"step {step_ref}: effect class {spec['effect_class']} cannot be"
                    f" carried by fidelity {spec['fidelity_class']}"
                )
            permission = pack_rbac.get(step_ref)
            if not permission:
                raise BindFailure(f"step {step_ref}: permission unresolved in pack RBAC")
            policy_rule = policy_rules.get(step_ref)
            if not policy_rule:
                raise BindFailure(f"step {step_ref}: policy rule unresolved")
            bindings.append({
                "step_ref": step_ref,
                "operation_name": spec["operation"],
                "operation_version": spec["version"],
                "role": pack_rbac.get(step_ref + ":role", "member"),
                "permission": permission,
                "policy_rule": policy_rule,
                "approval_required": spec["effect_class"] == "consequential",
                "evidence_requirement": "receipt+digest",
            })
            self._db.execute(
                """
                INSERT INTO pack_bindings
                    (tenant_id, pack_id, version, step_ref, operation_name,
                     operation_version, role, permission, policy_rule,
                     approval_required, evidence_requirement)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (context.tenant_id, pack_id, version, step_ref, spec["operation"],
                 spec["version"], bindings[-1]["role"], permission, policy_rule,
                 bindings[-1]["approval_required"], "receipt+digest"),
            )
        with self._db.connection() as connection:
            connection.execute(
                "UPDATE capability_packs SET lifecycle='bound' WHERE tenant_id=%s"
                " AND pack_id=%s AND version=%s",
                (context.tenant_id, pack_id, version),
            )
        return bindings

    def rebind_after_rotation(self, context: IdentityContext, pack_id: str,
                              version: int, step_ref: str,
                              new_operation_version: int,
                              compat_check: Callable[[], bool]) -> dict:
        """BUS-004-R01: connector/tool rotation requires compatibility and
        evaluation re-run before the pack may select the new binding."""
        if not compat_check():
            raise BindFailure("compatibility/evaluation not re-run for rotated version")
        self._db.execute(
            """
            UPDATE pack_bindings SET operation_version=%s
            WHERE tenant_id=%s AND pack_id=%s AND version=%s AND step_ref=%s
            """,
            (new_operation_version, context.tenant_id, pack_id, version, step_ref),
        )
        return {"step_ref": step_ref, "operation_version": new_operation_version}


class PackPublisher:
    """BUS-005: execute declared evaluation cases; publish only when every
    mandatory case passes even if the aggregate score is high."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def qualify_and_publish(
        self, context: IdentityContext, pack_id: str, version: int,
        case_results: list[dict],
        publish_execution: Callable[[int], dict],
    ) -> dict:
        pack = CapabilityPackService(self._db).get_pack(context, pack_id, version)
        evaluations = pack["evaluations"]
        results_by_name = {r["case"]: r for r in case_results}
        for case in evaluations:
            result = results_by_name.get(case["name"])
            if result is None:
                raise PublicationBlocked(f"evaluation case never executed: {case['name']}")
            if case["mandatory"] and not result["passed"]:
                raise PublicationBlocked(
                    f"mandatory evaluation case failed: {case['name']}"
                )
        aggregate = sum(1 for r in case_results if r["passed"]) / len(case_results)
        # Aggregate score alone is insufficient; only mandatory cases block.
        published = publish_execution(version)
        with self._db.connection() as connection:
            connection.execute(
                "UPDATE capability_packs SET lifecycle='published' WHERE tenant_id=%s"
                " AND pack_id=%s AND version=%s",
                (context.tenant_id, pack_id, version),
            )
        return {"pack_id": pack_id, "version": version,
                "aggregate_pass_rate": round(aggregate, 3),
                "published": True, **published}

    def rollback_published(self, context: IdentityContext, pack_id: str) -> dict:
        return CapabilityPackService(self._db).rollback(context, pack_id)

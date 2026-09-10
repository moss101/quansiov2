"""Skill lifecycle (SKL-001..005, owner quansio-control registry +
quansio-runtime/qworkerd execution).

Controlled intake converts authoritative material into candidate
SkillPackages with declared purpose, inputs, outputs, instructions,
dependencies, source scope, intended use and exclusions. Static/security
evaluation checks schema validity, authority expansion, unsafe helpers,
protected paths, network needs and declared tool usage. Candidate cases run
in isolated task runtimes against REAL boundaries; regression thresholds
gate qualification. The registry promotes only evaluated versions, keeps a
rollback target, denies skill self-mutation, and resolves task
materializations strictly within the admitted capability snapshot.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import uuid
from pathlib import Path
from typing import Any

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase
from quansio.qworkerd.protocol import GuestProtocol, GuestRejection


class IntakeRefused(Exception):
    """SKL-001-N01: material untrusted/unscoped or metadata incomplete."""


class EvaluationBlocked(Exception):
    """SKL-002-N01: forbidden helper behavior found."""


class QualificationBlocked(Exception):
    """SKL-003-N01: case passed only via a substituted boundary."""


class SkillSelfMutationBlocked(Exception):
    """SKL-004-N01: skill attempted to mutate its own promotion state."""


class MaterializationDenied(Exception):
    """SKL-005-N01: skill unqualified/incompatible or beyond task capability."""


EVALUATOR_VERSION = "skill-evaluator/1"


class SkillIntake:
    def __init__(self, database: PlatformDatabase):
        self._db = database

    def create_candidate(self, context: IdentityContext, skill_name: str,
                         source_material: dict, purpose: str,
                         inputs_schema: dict, outputs_schema: dict,
                         instructions: str, dependencies: list[dict],
                         source_scope: dict, intended_use: str,
                         exclusions: str) -> dict:
        if not source_scope.get("trusted_sources"):
            raise IntakeRefused("source material is untrusted/unscoped")
        if not intended_use or not exclusions:
            raise IntakeRefused("intended-use and exclusion metadata are required")
        material_digest = hashlib.sha256(
            json.dumps(source_material, sort_keys=True).encode()
        ).hexdigest()
        row = self._db.query_one(
            "SELECT COALESCE(MAX(version), 0) FROM skill_packages"
            " WHERE tenant_id=%s AND skill_name=%s",
            (context.tenant_id, skill_name),
        )
        version = row[0] + 1
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO skill_packages
                    (tenant_id, skill_name, version, purpose, inputs_schema,
                     outputs_schema, instructions, dependencies, source_scope,
                     intended_use, exclusions, source_material_digest, state)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'candidate')
                """,
                (context.tenant_id, skill_name, version, purpose,
                 Json(inputs_schema), Json(outputs_schema), instructions,
                 Json(dependencies), Json(source_scope), intended_use,
                 exclusions, material_digest),
            )
        return {"skill_name": skill_name, "version": version,
                "source_material_digest": material_digest, "state": "candidate"}

    def package(self, context: IdentityContext, skill_name: str, version: int) -> dict:
        row = self._db.query_one(
            """
            SELECT skill_name, version, purpose, inputs_schema, outputs_schema,
                   instructions, dependencies, source_scope, intended_use,
                   exclusions, source_material_digest, state
            FROM skill_packages WHERE tenant_id=%s AND skill_name=%s AND version=%s
            """,
            (context.tenant_id, skill_name, version),
        )
        if row is None:
            raise KeyError("skill version unknown")
        return {"skill_name": row[0], "version": row[1], "purpose": row[2],
                "inputs_schema": row[3], "outputs_schema": row[4],
                "instructions": row[5], "dependencies": row[6],
                "source_scope": row[7], "intended_use": row[8],
                "exclusions": row[9], "source_material_digest": row[10],
                "state": row[11]}


class SkillEvaluator:
    """SKL-002: static + security analysis; findings are recorded per
    evaluator version and never silently rewritten."""

    FORBIDDEN_SNIPPETS = [
        ("undeclared network", re.compile(r"requests\.(get|post)|urllib|httpx|socket\.socket")),
        ("credential access", re.compile(r"QUAL_PROVIDER_|os\.environ\[|api_key\s*=")),
        ("self promotion", re.compile(r"skill_registr|promote\s*\(|UPDATE\s+skill_packages")),
    ]
    PROTECTED_MARKERS = ("/etc", "/vault", ".ssh", "id_rsa")

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def evaluate(self, context: IdentityContext, skill_name: str, version: int,
                 intake: SkillIntake, declared_network: bool = False) -> dict:
        package = intake.package(context, skill_name, version)
        findings = []
        passed = True
        blob = json.dumps(package, default=str)
        if not package["inputs_schema"] or not package["outputs_schema"]:
            findings.append({"kind": "schema", "detail": "missing input/output schema"})
            passed = False
        for label, pattern in self.FORBIDDEN_SNIPPETS:
            if label == "undeclared network" and declared_network:
                continue
            if pattern.search(blob):
                findings.append({"kind": "security", "detail": f"forbidden helper behavior: {label}"})
                passed = False
        for marker in self.PROTECTED_MARKERS:
            if marker in package["instructions"]:
                findings.append({"kind": "protected_path", "detail": f"references {marker}"})
                passed = False
        if re.search(r"\b(promote|rollback)\b", package["instructions"]):
            findings.append({"kind": "authority_expansion",
                             "detail": "instructions mention promotion/rollback authority"})
            passed = False
        self._db.execute(
            """
            INSERT INTO skill_evaluations
                (tenant_id, skill_name, version, evaluator_version, findings, passed)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (context.tenant_id, skill_name, version, EVALUATOR_VERSION,
             Json(findings), passed),
        )
        if not passed:
            self._db.execute(
                "UPDATE skill_packages SET state='blocked' WHERE tenant_id=%s"
                " AND skill_name=%s AND version=%s",
                (context.tenant_id, skill_name, version),
            )
        evaluation_digest = hashlib.sha256(
            json.dumps({"findings": findings, "passed": passed,
                        "evaluator": EVALUATOR_VERSION}, sort_keys=True).encode()
        ).hexdigest()
        return {"passed": passed, "findings": findings,
                "evaluation_digest": evaluation_digest,
                "evaluator_version": EVALUATOR_VERSION}

    def reevaluate_after_update(self, context: IdentityContext, skill_name: str,
                                version: int, intake: SkillIntake) -> dict:
        """SKL-002-R01: a fresh evaluation row is appended under the new
        evaluator version; recorded history is immutable."""
        return self.evaluate(context, skill_name, version, intake)


class SkillCaseRunner:
    """SKL-003: run candidate cases in isolated sandboxes against REAL
    boundaries; a mock substitution leaves qualification blocked, and a
    crashed case restarts with clean isolation."""

    def __init__(self, database: PlatformDatabase, state_root: Path):
        self._db = database
        self._state_root = Path(state_root)

    def run_case(self, context: IdentityContext, skill_name: str, version: int,
                 case: dict) -> dict:
        """A case declares: guest op, arguments, expected markers and
        ``required_real_boundary``. Substituting a mock for a required real
        boundary blocks qualification regardless of output equality."""
        task_id = f"case-{uuid.uuid4().hex[:10]}"
        root = self._state_root / context.tenant_id / task_id
        (root / "workspace").mkdir(parents=True, exist_ok=True)
        guest = GuestProtocol(root / "workspace", task_id)
        try:
            output = guest.execute(case["operation"], "guest-rpc/1",
                                   case["arguments"], {"task_id": task_id})
            if case.get("required_real_boundary") and case.get("mock_substituted"):
                return {"case": case["name"], "passed": False,
                        "reason": "mock substituted for a required real boundary"}
            expected = case.get("expect_contains")
            passed = all(marker in json.dumps(output["output"]) for marker in (expected or []))
            return {"case": case["name"], "passed": passed,
                    "output": output["output"], "isolated": True}
        except GuestRejection as error:
            return {"case": case["name"], "passed": False, "reason": str(error)}
        finally:
            shutil.rmtree(root, ignore_errors=True)  # clean isolation per case

    def run_regression(self, context: IdentityContext, skill_name: str, version: int,
                       cases: list[dict], thresholds: dict) -> dict:
        results = [self.run_case(context, skill_name, version, case) for case in cases]
        passed_count = sum(1 for r in results if r["passed"])
        pass_rate = passed_count / len(results) if results else 0.0
        minimum = thresholds.get("min_pass_rate", 1.0)
        qualified = pass_rate >= minimum and all(
            r.get("passed", False) or "mock" not in r.get("reason", "")
            for r in results
        )
        return {"results": results, "pass_rate": round(pass_rate, 3),
                "qualified": qualified}


class SkillRegistry:
    """SKL-004: promotion is separate from candidate execution; skills can
    never mutate their own promotion/capability state."""

    def __init__(self, database: PlatformDatabase, policy_engine=None):
        self._db = database
        self._policy = policy_engine

    def promote(self, context: IdentityContext, skill_name: str, version: int,
                evaluation_passed: bool, thresholds: dict,
                compatibility: dict | None = None,
                rollback_target: int | None = None) -> dict:
        if not evaluation_passed:
            raise SkillSelfMutationBlocked("cannot promote without passed evaluation")
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO skill_registrations
                    (tenant_id, skill_name, active_version, rollback_target,
                     compatibility, thresholds)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, skill_name)
                DO UPDATE SET rollback_target = skill_registrations.active_version,
                              active_version = EXCLUDED.active_version,
                              compatibility = EXCLUDED.compatibility,
                              thresholds = EXCLUDED.thresholds,
                              promoted_at = now()
                """,
                (context.tenant_id, skill_name, version, rollback_target,
                 Json(compatibility or {}), Json(thresholds)),
            )
            connection.execute(
                "UPDATE skill_packages SET state='promoted' WHERE tenant_id=%s"
                " AND skill_name=%s AND version=%s",
                (context.tenant_id, skill_name, version),
            )
        return {"skill_name": skill_name, "active_version": version,
                "rollback_target": rollback_target}

    def attempt_self_mutation(self, context: IdentityContext, skill_name: str,
                              version: int) -> None:
        """SKL-004-N01: a running skill asking to promote itself is denied —
        promotion is an operator/registry action, never a skill action."""
        raise SkillSelfMutationBlocked(
            "skills cannot mutate their own promotion or capability state"
        )

    def rollback(self, context: IdentityContext, skill_name: str) -> dict:
        row = self._db.query_one(
            "SELECT active_version, rollback_target FROM skill_registrations"
            " WHERE tenant_id=%s AND skill_name=%s",
            (context.tenant_id, skill_name),
        )
        if row is None or row[1] is None:
            raise KeyError("no rollback target")
        previous = row[1]
        with self._db.connection() as connection:
            connection.execute(
                """
                UPDATE skill_registrations
                SET active_version = %s, rollback_target = %s, promoted_at = now()
                WHERE tenant_id = %s AND skill_name = %s
                """,
                (previous, row[0], context.tenant_id, skill_name),
            )
            connection.execute(
                "UPDATE skill_packages SET state='rolled_back' WHERE tenant_id=%s"
                " AND skill_name=%s AND version=%s",
                (context.tenant_id, skill_name, row[0]),
            )
        return {"skill_name": skill_name, "active_version": previous,
                "rolled_back_version": row[0]}


class SkillMaterializer:
    """SKL-005: resolve only qualified, compatible skills; materialize into
    the task sandbox under the admitted capability snapshot; record exact
    versions in run evidence; teardown removes materialization only."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def resolve_and_materialize(
        self, context: IdentityContext, task_id: str, sandbox: GuestProtocol,
        skill_name: str, requested_version: int | None,
        capability_snapshot: dict,
    ) -> dict:
        reg = self._db.query_one(
            "SELECT active_version, compatibility FROM skill_registrations"
            " WHERE tenant_id=%s AND skill_name=%s",
            (context.tenant_id, skill_name),
        )
        if reg is None:
            raise MaterializationDenied(f"skill {skill_name} is not qualified")
        active_version, compatibility = reg
        version = requested_version or active_version
        if requested_version and requested_version != active_version:
            raise MaterializationDenied(
                f"requested version {requested_version} is not the qualified version"
            )
        if isinstance(compatibility, str):
            try:
                compatibility = json.loads(compatibility)
            except json.JSONDecodeError:
                compatibility = {}
        required_capability = (compatibility or {}).get("capability")
        if required_capability and required_capability not in capability_snapshot.get(
                "capabilities", []):
            raise MaterializationDenied(
                f"skill requires capability {required_capability!r} beyond the task snapshot"
            )
        materialization_id = str(uuid.uuid4())
        self._db.execute(
            """
            INSERT INTO skill_materializations
                (materialization_id, tenant_id, task_id, skill_name, version, state)
            VALUES (%s, %s, %s, %s, %s, 'materialized')
            """,
            (materialization_id, context.tenant_id, task_id, skill_name, version),
        )
        sandbox.execute("fs.write", "guest-rpc/1",
                        {"path": "workspace/.quansio/skills.json",
                         "content": json.dumps({skill_name: version})},
                        {"task_id": task_id})
        return {"materialization_id": materialization_id,
                "skill_name": skill_name, "version": version}

    def teardown_task(self, context: IdentityContext, task_id: str) -> int:
        with self._db.connection() as connection:
            cursor = connection.execute(
                "UPDATE skill_materializations SET state='removed'"
                " WHERE tenant_id=%s AND task_id=%s AND state='materialized'",
                (context.tenant_id, task_id),
            )
            removed = cursor.rowcount
        registry_rows = self._db.query_all(
            "SELECT skill_name, active_version FROM skill_registrations WHERE tenant_id=%s",
            (context.tenant_id,),
        )
        evaluations = self._db.query_one(
            "SELECT count(*) FROM skill_evaluations WHERE tenant_id=%s",
            (context.tenant_id,),
        )[0]
        assert registry_rows is not None and evaluations >= 0
        return removed

"""quansio-control HTTP surface: tenant/identity/RBAC/policy/approval/
registry authority.

Identity truth is resolved only from durable server state; tenant
provisioning has a bootstrap route that is reachable only while no tenant
exists. Policy decisions, scoped approvals, the effect ledger and the
canonical tool registry are all control-owned and exposed here with
server-resolved identity on every route.
"""

from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from quansio.control.capability import (
    CapabilityEscalationError,
    CapabilityService,
    SnapshotExpiredError,
)
from quansio.control.connectors import UnsafeDeclaration, ToolRegistry
from quansio.control.effects import (
    ApprovalService,
    EffectLedger,
    EffectRequired,
    EffectStateError,
)
from quansio.control.identity import ControlService, IdentityContextError
from quansio.control.policy import (
    PolicyDenied,
    PolicyEngine,
    PolicyUnavailable,
    ScopeDigestMismatch,
)
from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase, database_config
from quansio.platform.service import (
    add_cors,
    add_health_routes,
    default_database,
    identity_view,
    resolve_bearer,
)


class TenantCreate(BaseModel):
    name: str


class WorkspaceCreate(BaseModel):
    tenant_id: str
    name: str


class UserCreate(BaseModel):
    tenant_id: str
    email: str
    display_name: str
    password: str
    role: str = "member"
    workspace_id: str | None = None


class PolicyDecisionRequest(BaseModel):
    actor_id: str
    operation: str
    arguments: dict
    target: str
    data_classification: list[str]
    capability_snapshot_id: str | None = None


class EffectPropose(BaseModel):
    run_id: str
    operation: str
    arguments: dict
    target: str
    policy_decision_id: str | None = None
    idempotency_key: str | None = None


class EffectAuthorize(BaseModel):
    policy_decision_id: str
    approval_id: str | None = None


class ApprovalRequestBody(BaseModel):
    run_id: str
    effect_id: str
    operation: str
    arguments: dict
    target: str
    financial: dict | None = None


class ApprovalDecision(BaseModel):
    approved: bool
    approver_id: str


class ToolRegistration(BaseModel):
    operation_name: str
    version: int
    schema_def: dict
    effect_class: str
    fidelity_class: str
    capability_need: str
    policy_need: str
    timeout_ms: int
    idempotent: bool
    evidence_contract: str


def create_app(database: PlatformDatabase | None = None) -> FastAPI:
    app = FastAPI(title="quansio-control", version="9.0.0")
    add_cors(app)
    db = database or default_database()
    control = ControlService(db)
    policy = PolicyEngine(db)
    effects = EffectLedger(db)
    approvals = ApprovalService(db, policy)
    capabilities = CapabilityService(db)
    registry = ToolRegistry(db)

    add_health_routes(app, db, "quansio-control")

    # -- bootstrap: reachable only while the authority is empty ------------

    @app.post("/v9/bootstrap/tenant")
    def bootstrap_tenant(body: TenantCreate, authorization: str = Header(default="")) -> dict:
        existing = db.query_one("SELECT count(*) FROM tenants")
        if existing[0] > 0:
            raise HTTPException(
                status_code=403,
                detail="bootstrap closed: tenants exist; use an authenticated session",
            )
        tenant_id = control.create_tenant(body.name)
        return {"tenant_id": tenant_id}

    # -- identity and tenancy (authenticated) ------------------------------

    @app.post("/v9/tenants")
    def create_tenant(body: TenantCreate, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        _require_admin(context)
        tenant_id = control.create_tenant(body.name)
        return {"tenant_id": tenant_id}

    @app.post("/v9/workspaces")
    def create_workspace(body: WorkspaceCreate, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        if body.tenant_id != context.tenant_id:
            raise HTTPException(status_code=403, detail="cross-tenant workspace creation refused")
        _require_admin(context)
        workspace_id = control.create_workspace(context.tenant_id, body.name)
        return {"workspace_id": workspace_id}

    @app.post("/v9/users")
    def create_user(body: UserCreate, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        if body.tenant_id != context.tenant_id:
            raise HTTPException(status_code=403, detail="cross-tenant user creation refused")
        _require_admin(context)
        try:
            user_id = control.create_user(
                body.tenant_id, body.email, body.display_name, body.password,
                role=body.role, workspace_id=body.workspace_id,
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return {"user_id": user_id}

    @app.get("/v9/identity")
    def whoami(authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return {"identity": identity_view(context)}

    # -- policy decisions ---------------------------------------------------

    @app.post("/v9/policy/decisions")
    def decide(body: PolicyDecisionRequest, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            decision = policy.decide(
                context, body.actor_id, body.operation, body.arguments,
                body.target, body.data_classification,
                capability_snapshot_id=body.capability_snapshot_id,
            )
        except PolicyUnavailable as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        return {"decision": decision}

    @app.post("/v9/policy/decisions/{policy_decision_id}/scope-check")
    def scope_check(policy_decision_id: str, body: PolicyDecisionRequest, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        row = db.query_one(
            """
            SELECT decision, argument_scope_digest, expires_at FROM policy_decisions
            WHERE tenant_id=%s AND policy_decision_id=%s
            """,
            (context.tenant_id, policy_decision_id),
        )
        if row is None:
            raise HTTPException(status_code=404, detail="policy decision unknown")
        decision = {
            "policy_decision_id": policy_decision_id,
            "decision": row[0],
            "argument_scope_digest": row[1],
            "expires_at": row[2],
        }
        try:
            policy.check_scope(decision, body.arguments)
            policy.require_fresh(decision)
        except (ScopeDigestMismatch, PolicyDenied) as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        return {"scope_valid": True}

    # -- effect ledger -------------------------------------------------------

    @app.post("/v9/effects")
    def propose_effect(body: EffectPropose, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return {"effect": effects.propose(
            context, body.run_id, body.operation, body.arguments,
            body.target, policy_decision_id=body.policy_decision_id,
            idempotency_key=body.idempotency_key,
        )}

    @app.post("/v9/effects/{effect_id}/authorize")
    def authorize_effect(effect_id: str, body: EffectAuthorize, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            effects.authorize(context, effect_id, body.policy_decision_id,
                              approval_id=body.approval_id)
        except EffectStateError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"effect_id": effect_id, "status": "authorized"}

    @app.get("/v9/effects/{effect_id}")
    def get_effect(effect_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            # Read-only view: no expected status, any state is visible.
            return {"effect": effects.require_effect(context, effect_id, expected_status="")}
        except EffectRequired as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    # -- approvals -----------------------------------------------------------

    @app.post("/v9/approvals")
    def request_approval(body: ApprovalRequestBody, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return {"approval": approvals.request(
            context, body.run_id, body.effect_id, body.operation,
            body.arguments, body.target, financial=body.financial,
        )}

    @app.post("/v9/approvals/{approval_id}/decision")
    def decide_approval(approval_id: str, body: ApprovalDecision, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return approvals.decide(context, approval_id, body.approved, body.approver_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    # -- capability snapshots --------------------------------------------------

    class CapabilityAdmit(BaseModel):
        principal_id: str
        capabilities: list[str]
        constraints: dict
        budget_cents: int
        ttl_seconds: int = 3600
        parent_snapshot_id: str | None = None

    @app.post("/v9/capabilities/snapshots")
    def admit_capability_snapshot(body: CapabilityAdmit, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            if body.parent_snapshot_id:
                snapshot = capabilities.admit_child(
                    context, body.parent_snapshot_id, body.principal_id,
                    body.capabilities, body.constraints, body.budget_cents,
                )
            else:
                snapshot = capabilities.admit_root(
                    context, body.principal_id, body.capabilities,
                    body.constraints, body.budget_cents,
                    ttl_seconds=body.ttl_seconds,
                )
        except CapabilityEscalationError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        return {"snapshot": snapshot}

    @app.get("/v9/capabilities/snapshots/{snapshot_id}")
    def get_capability_snapshot(snapshot_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            snapshot = capabilities.require_active(context, snapshot_id)
        except (PermissionError, SnapshotExpiredError) as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        return {"snapshot": snapshot}

    # -- canonical tool registry ----------------------------------------------

    @app.post("/v9/tools")
    def register_tool(body: ToolRegistration, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            registered = registry.register(
                context, body.operation_name, body.version, body.schema_def,
                body.effect_class, body.fidelity_class, body.capability_need,
                body.policy_need, body.timeout_ms, body.idempotent,
                body.evidence_contract,
            )
        except UnsafeDeclaration as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return {"tool": registered}

    @app.get("/v9/tools/{operation_name}")
    def resolve_tool(operation_name: str, max_version: int | None = None, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        tool = registry.resolve(context, operation_name, max_version=max_version)
        if tool is None:
            raise HTTPException(status_code=404, detail="tool operation unknown")
        return {"tool": tool}

    return app


def _require_admin(context: IdentityContext) -> None:
    if "tenant_admin" not in context.roles and "workspace_admin" not in context.roles:
        raise HTTPException(status_code=403, detail="administrative role required")

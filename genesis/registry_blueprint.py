"""Deterministic M2 Registry blueprint.

This is a candidate until the choices named in ``material-input.candidate.json``
are ratified.  The generated manifest, never a remembered count, is the source
of its definition count and hashes.
"""

from __future__ import annotations

from collections.abc import Mapping

from kernel.canon import CanonValue, object_hash

type Definition = dict[str, CanonValue]

HASH = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
STRING = {"type": "string"}
BOOLEAN = {"type": "boolean"}


def _array(items: CanonValue, *, minimum: int | None = None) -> Definition:
    schema: Definition = {"type": "array", "items": items}
    if minimum is not None:
        schema["minItems"] = minimum
    return schema


def _nullable(schema: Mapping[str, CanonValue]) -> Definition:
    nullable = dict(schema)
    schema_type = nullable.get("type")
    if not isinstance(schema_type, str):
        raise TypeError("nullable schema requires one explicit type")
    nullable["type"] = [schema_type, "null"]
    return nullable


def _object(
    properties: Mapping[str, CanonValue],
    *,
    required: tuple[str, ...] | None = None,
    additional: bool = False,
) -> Definition:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": dict(properties),
        "required": list(required or properties.keys()),
        "additionalProperties": additional,
    }


def _definition(kind: str, name: str, field: str, value: CanonValue) -> Definition:
    return {"kind": kind, "name": name, "version": 1, field: value}


def _command_definitions(choices: Mapping[str, CanonValue]) -> list[Definition]:
    hashes = _array(HASH)
    nullable_hash = _nullable(HASH)
    specs: dict[str, Definition] = {
        "RegisterDefinition": _object({
            "kind": {"type": "string", "enum": [
                "act_type", "command_type", "context_type", "disclosure_profile",
                "effect_phase", "machinery_class", "mandate", "node_species", "office",
                "projector", "relation_type", "rule",
            ]},
            "name": STRING,
            "version": {"type": "integer", "minimum": 1},
            "constitutional": BOOLEAN,
            "definition_hash": HASH,
            "schema_hash": nullable_hash,
        }),
        "CreateIdentity": _object({
            "identity_kind": {"type": "string", "enum": [
                "agent", "application", "device", "human", "integration", "machine",
                "model", "organization", "reviewer", "scheduler", "service", "workflow",
            ]},
            "public_keys": _array(STRING, minimum=1),
            "attributes_hash": nullable_hash,
        }),
        "RotateKey": _object({
            "identity_hash": HASH,
            "add_keys": _array(STRING),
            "retire_keys": _array(STRING),
            "grace_until_act": nullable_hash,
        }),
        # R-1 is recommended, not ratified.  Keeping this definition makes the
        # source inconsistency visible; a ruling may remove it and change count/hash.
        "SubmitCommand": _object({"command_hash": HASH}),
        "ReviewAuthorization": _object({
            "reviewed_command_hash": HASH,
            "verdict": {"type": "string", "enum": ["approve", "reject"]},
            "reason": STRING,
        }),
        "LinkPrincipal": _object({"issuer": STRING, "subject": STRING, "identity_hash": HASH}),
        "RevokePrincipal": _object({"issuer": STRING, "subject": STRING, "reason": STRING}),
        "AdmitObservation": _object({
            "observed_effect_hash": HASH,
            "observer_identity_hash": HASH,
            "evidence_hashes": _array(HASH, minimum=1),
            "observation_hash": HASH,
            "reported_at": STRING,
        }),
        "GrantAuthority": _object({
            "grantee_identity_hash": HASH,
            "office_hash": HASH,
            "mandate_hash": HASH,
            "on_behalf_of": nullable_hash,
            "powers": _nullable(_array(STRING)),
            "delegation_depth": {"type": "integer", "minimum": 0},
            "expires_at_act": nullable_hash,
            "reason": STRING,
        }),
        "RevokeAuthority": _object({
            "grant_act_hash": HASH,
            "reason": {"type": "string", "enum": [
                "delegation_ended", "expired", "misconduct", "succession", "voluntary",
            ]},
            "effective_immediately": BOOLEAN,
        }),
        "AppointReviewer": _object({
            "reviewer_identity_hash": HASH,
            "remit": hashes,
            "quorum_role": {"type": "string", "enum": ["ordinary", "constitutional"]},
            "expires_at_act": nullable_hash,
        }),
        "NominateDirector": _object({
            "nominee_identity_hash": HASH, "mandate_hash": HASH, "statement": STRING,
        }),
        "ProposeAmendment": _object({
            "target_definition_hash": HASH,
            "replacement_definition_hash": HASH,
            "rationale": STRING,
            "eternity_clause_check": BOOLEAN,
        }),
        "ObjectToAmendment": _object({"proposal_act_hash": HASH, "grounds": STRING}),
        "EnactAmendment": _object({
            "proposal_act_hash": HASH,
            "approval_act_hashes": _array(HASH, minimum=1),
            "delay_satisfied_at_cut": hashes,
        }),
        "ProposeExternalEffect": _object({
            "effect_kind_hash": HASH,
            "on_behalf_of": HASH,
            "subject_hash": HASH,
            "domain": STRING,
            "threshold_value": _nullable(STRING),
            "threshold_unit": _nullable(STRING),
            "counterparty_ref": _nullable(STRING),
            "summary": STRING,
        }),
        "DispatchExternalEffect": _object({
            "effect_request_act_hash": HASH,
            "performed_by_identity_hash": HASH,
            "external_authority_evidence": hashes,
            "dispatched_content_hash": HASH,
        }),
        "ClaimExternalFact": _object({
            "effect_request_act_hash": HASH,
            "observation_act_hashes": _array(HASH, minimum=1),
            "claimed_content_hash": HASH,
            "obligations": hashes,
            "claim_statement": STRING,
        }),
    }
    if choices.get("submit_command") == "drop":
        del specs["SubmitCommand"]
    return [_definition("command_type", name, "payload_schema", schema)
            for name, schema in specs.items()]


def _act_definitions(commands: Mapping[str, Definition]) -> list[Definition]:
    genesis_schema = _object({"config_hash": HASH})
    lifecycle_schema = _object({"command_hash": HASH, "reason": STRING})
    specs: dict[str, Definition] = {}
    for name in (
        "GenesisCreated", "RegistryCreated", "RootIdentityCreated",
        "RootAuthorityGranted", "GenesisClosed",
    ):
        specs[name] = genesis_schema
    for name in (
        "CommandSubmitted", "CommandValidated", "CommandRejected",
        "AuthorizationRequested", "CommandDenied", "ReviewRequested",
        "AuthorizationReviewed", "AuthorizationResolved", "CommandSuperseded",
        "CommandExpired",
    ):
        specs[name] = lifecycle_schema
    mirrors = {
        "DefinitionRegistered": "RegisterDefinition",
        "IdentityCreated": "CreateIdentity",
        "KeyRotated": "RotateKey",
        "PrincipalLinked": "LinkPrincipal",
        "PrincipalRevoked": "RevokePrincipal",
        "ObservationAdmitted": "AdmitObservation",
        "AuthorityGranted": "GrantAuthority",
        "AuthorityRevoked": "RevokeAuthority",
        "ReviewerAppointed": "AppointReviewer",
        "DirectorNominated": "NominateDirector",
        "AmendmentProposed": "ProposeAmendment",
        "AmendmentObjected": "ObjectToAmendment",
        "AmendmentEnacted": "EnactAmendment",
        "ExternalEffectRequested": "ProposeExternalEffect",
        "ExternalEffectDispatched": "DispatchExternalEffect",
        "ExternalFactClaimed": "ClaimExternalFact",
    }
    for act_name, command_name in mirrors.items():
        specs[act_name] = dict(commands[command_name]["payload_schema"])  # type: ignore[arg-type]
    effect_phase = _object({"effect_request_act_hash": HASH, "reason": STRING})
    for name in (
        "ExternalEffectAuthorized", "ExternalEffectDispatchFailed", "ExternalEffectRetried",
    ):
        specs[name] = effect_phase
    definitions = [_definition("act_type", name, "payload_schema", schema)
                   for name, schema in specs.items()]
    companion = {"writer": "principal_bindings", "cardinality": "exactly_one"}
    for definition in definitions:
        if definition["name"] in {"PrincipalLinked", "PrincipalRevoked"}:
            definition["companion"] = companion
    return definitions


def _relation_definitions() -> list[Definition]:
    endpoint_map = {
        "holds_office": ["identity", "office"],
        "represented_by": ["organization", "identity"],
        "delegated_from": ["act", "act"],
        "supersedes": ["object", "object"],
        "evidenced_by": ["act", "object"],
        "stands_behind": ["organization", "object"],
    }
    lineage = {"crafted_from", "delegated_from", "derived_from", "forked_from",
               "simulated_from", "supersedes"}
    names = (
        "caused_by", "authorized_by", "reviewed_by", "derived_from", "forked_from",
        "simulated_from", "crafted_from", "supports", "contradicts", "matched_to",
        "anchored_at", "notarized_by", "holds_office", "represented_by",
        "delegated_from", "supersedes", "evidenced_by", "stands_behind",
    )
    definitions: list[Definition] = []
    for name in names:
        endpoints = endpoint_map.get(name, ["object", "object"])
        definitions.append({
            "kind": "relation_type",
            "name": name,
            "version": 1,
            "payload_schema": _nullable(_object({})),
            "lineage": name in lineage,
            "endpoint_kinds": {"from": endpoints[0], "to": endpoints[1]},
        })
    return definitions


def _context_definitions() -> list[Definition]:
    specs: dict[str, Definition] = {
        "request.origin": _object({"type": STRING, "address": _nullable(STRING)}),
        "request.metadata": _object({}, additional=True),
        "review.acts": _object({"acts": _array(HASH)}),
        "delegation.cut": _object({"cut": _array(HASH)}),
        "time.claimed": _object({"claimed_when": {
            "type": "string",
            "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.+-]+Z?$",
        }}),
        "request.requested_by": _object({"identity_hash": HASH}),
        "request.performed_by": _object({"identity_hash": HASH}),
        "request.requester_kind": _object({"kind": STRING}),
        "request.oauth_client": _object({"client_id": STRING}),
        "authority.grants": _object({"grants": _array(_object({
            "grant_act": HASH, "grantee": HASH, "office": HASH, "mandate": HASH,
            "on_behalf_of": _nullable(HASH), "powers": _nullable(_array(STRING)),
            "depth": {"type": "integer", "minimum": 0},
        }))}),
        "external.authority_evidence": _object({
            "predicate_ref": STRING,
            "evidence": _array(_object({"hash": HASH, "kind": STRING, "described_as": STRING})),
            "satisfied": BOOLEAN,
        }),
        "amendment.state": _object({
            "proposal_act": HASH, "approvals": _array(HASH), "objections": _array(HASH),
            "proposed_at_cut": _array(HASH),
        }),
        "cut.declared": _object({"cut": _array(HASH)}),
        "cut.advance": _object({
            "advanced": BOOLEAN, "delta": _array(HASH), "delta_act_types": _array(HASH),
        }),
    }
    return [_definition("context_type", name, "value_schema", schema)
            for name, schema in specs.items()]


def _rule_definitions(
    commands: Mapping[str, str], contexts: Mapping[str, str], choices: Mapping[str, CanonValue]
) -> list[Definition]:
    all_commands = sorted(commands.values())

    def context_refs(*names: str) -> list[Definition]:
        return [{"name": name, "definition_hash": contexts[name]} for name in names]

    rule_specs: dict[str, tuple[list[Definition], list[str], Definition, Definition]] = {
        "declared-decision-cut": (
            context_refs("cut.declared", "cut.advance"), all_commands,
            {"language": "powerfarm-rule-expr-v1", "if": "cut.advance.advanced == false",
             "then": "VALID", "else": "REAUTHORIZE"},
            {"survival_rungs_admitted": [0], "unconditional_commit_regardless": False,
             "drift_rejection_act_type": "CommandDenied"},
        ),
        "amendment-or-fork": (
            context_refs("authority.grants", "amendment.state"),
            [commands[name] for name in ("ProposeAmendment", "ObjectToAmendment", "EnactAmendment")],
            {"language": "powerfarm-rule-expr-v1",
             "require": ["target_not_eternity_clause", "delay_elapsed", "quorum_satisfied"]},
            {"mode": choices["amendment_mode"], "delay_days": choices["amendment_delay_days"],
             "quorum": choices["constitutional_quorum"],
             "director_role": choices["director_amendment_role"]},
        ),
        "root-mandate": (
            context_refs("authority.grants", "request.performed_by"), all_commands,
            {"language": "powerfarm-rule-expr-v1",
             "allow_only": ["genesis_registration", "initial_identity", "initial_office_holder"],
             "exhausted_at": "GenesisClosed", "external_representation": "never"}, {},
        ),
        "director-mandate-boundary": (
            context_refs("authority.grants", "request.performed_by", "request.requested_by"),
            all_commands,
            {"language": "powerfarm-rule-expr-v1",
             "require": ["active_grant", "power_in_mandate", "not_constitutive_power"]},
            {"delegation_depth_default": choices["delegation_depth_default"]},
        ),
        "director-succession": (
            context_refs("authority.grants", "review.acts"),
            [commands[name] for name in ("NominateDirector", "GrantAuthority", "RevokeAuthority")],
            {"language": "powerfarm-rule-expr-v1",
             "require": ["sitting_director_nomination", "review_quorum", "delay_elapsed",
                         "holder_bounds_preserved"]},
            {"quorum": choices["succession_quorum"],
             "delay_days": choices["succession_delay_days"]},
        ),
        "no-self-extension": (
            context_refs("authority.grants"),
            [commands[name] for name in ("GrantAuthority", "RegisterDefinition", "ProposeAmendment")],
            {"language": "powerfarm-rule-expr-v1",
             "deny_if": ["power_set_grows", "delegation_depth_grows", "self_reviewers_appointed"]}, {},
        ),
        "dual-authority": (
            context_refs("authority.grants", "external.authority_evidence"),
            [commands[name] for name in ("DispatchExternalEffect", "ClaimExternalFact")],
            {"language": "powerfarm-rule-expr-v1",
             "require": ["internal_authority", "external_predicate_satisfied"]}, {},
        ),
        "compass-confers-no-authority": (
            [], [],
            {"language": "powerfarm-rule-expr-v1",
             "deny_if": ["research_compass_used_as_grant", "direction_used_as_authority"]},
            {"scope": "all_rule_evaluations"},
        ),
    }
    return [{
        "kind": "rule", "name": name, "version": 1, "context_keys": context_keys,
        "applicability": applicability, "body": body, "parameters": parameters,
    } for name, (context_keys, applicability, body, parameters) in rule_specs.items()]


def _mandate_definitions(choices: Mapping[str, CanonValue]) -> list[Definition]:
    return [
        {
            "kind": "mandate", "name": "director.mandate.boundary.v1", "version": 1,
            "powers": ["ordinary_registry", "operational_authority", "budgets", "research",
                       "publication", "external_representation"],
            "prohibitions": ["constitutional_enactment", "grant_root", "self_extension",
                             "appoint_own_reviewers"],
            "delegation_depth": choices["delegation_depth_default"],
            "external_predicates_ref": None,
            "boundary_shape": choices["mandate_boundary"],
        },
        {
            "kind": "mandate", "name": "root.mandate.v1", "version": 1,
            "powers": ["genesis_registration", "initial_identity", "initial_office_holder"],
            "prohibitions": ["post_genesis_operation", "external_representation",
                             "director_operation"],
            "delegation_depth": 0,
            "external_predicates_ref": None,
            "exhausted_at": "GenesisClosed",
        },
    ]


def _office_definitions(
    rules: Mapping[str, str], mandates: Mapping[str, str], choices: Mapping[str, CanonValue]
) -> list[Definition]:
    recovery_rule = rules["director-succession"] \
        if choices["recovery_mode"] == "constitutional_quorum" else None
    return [{
        "kind": "office", "name": "powerfarm.director", "version": 1,
        "mandate_kinds": [mandates["director.mandate.boundary.v1"]],
        "min_holders": 1, "max_holders": choices["max_holders"],
        "succession_rule": rules["director-succession"], "recovery_rule": recovery_rule,
    }]


def _projector_definitions(acts: Mapping[str, str]) -> list[Definition]:
    inputs = {
        "causal.topological": sorted(acts.values()),
        "registry.current": [acts["DefinitionRegistered"], acts["AmendmentEnacted"]],
        "identity_keys.at_cut": [acts["IdentityCreated"], acts["KeyRotated"]],
        "trajectory.graph": sorted(acts.values()),
        "authority.active_grants": [acts["AuthorityGranted"], acts["AuthorityRevoked"]],
        "office.holders": [acts["AuthorityGranted"], acts["AuthorityRevoked"]],
        "external.commitments": [acts["ExternalEffectRequested"],
                                  acts["ExternalEffectDispatched"],
                                  acts["ObservationAdmitted"], acts["ExternalFactClaimed"]],
    }
    return [{"kind": "projector", "name": name, "version": 1,
             "inputs": hashes, "deterministic": True} for name, hashes in inputs.items()]


def build_definitions(choices: Mapping[str, CanonValue]) -> list[Definition]:
    """Build all candidate definitions in dependency order, then sort them."""
    commands = _command_definitions(choices)
    command_by_name = {str(item["name"]): item for item in commands}
    acts = _act_definitions(command_by_name)
    relations = _relation_definitions()
    contexts = _context_definitions()

    command_hashes = {str(item["name"]): object_hash("registry", item) for item in commands}
    context_hashes = {str(item["name"]): object_hash("registry", item) for item in contexts}
    rules = _rule_definitions(command_hashes, context_hashes, choices)
    rule_hashes = {str(item["name"]): object_hash("registry", item) for item in rules}
    mandates = _mandate_definitions(choices)
    mandate_hashes = {str(item["name"]): object_hash("registry", item) for item in mandates}
    offices = _office_definitions(rule_hashes, mandate_hashes, choices)
    act_hashes = {str(item["name"]): object_hash("registry", item) for item in acts}
    projectors = _projector_definitions(act_hashes)
    definitions = commands + acts + relations + contexts + rules + mandates + offices + projectors
    return sorted(definitions, key=lambda item: (str(item["kind"]), str(item["name"]), 1))

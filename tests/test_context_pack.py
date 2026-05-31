from pydantic import ValidationError
import pytest

from ultimate_ai_agent.core.contracts import ContextPack, ContextSource, ContextPackScope, AuthorityType, ContentRole, CONTEXT_PACK_SCHEMA_VERSION

def test_minimal_valid_context_pack():
    src = ContextSource(
        source_id="src_1",
        source_type="file",
        path="docs/canonical/09_roadmap.md",
        authority=AuthorityType.canonical,
        summary="Roadmap doc outlining milestones",
        content_role=ContentRole.reference
    )
    pack = ContextPack(
        context_pack_id="cp_test_123",
        contract_id="ec_test_123",
        run_id="run_123",
        workspace_id="ws_1",
        user_id="usr_alice",
        pack_scope=ContextPackScope.run,
        active_goal="Verify context pack implementation",
        canonical_sources=[src],
        token_budget=10000
    )
    assert pack.context_pack_id == "cp_test_123"
    assert len(pack.canonical_sources) == 1
    assert pack.canonical_sources[0].source_id == "src_1"
    assert pack.schema_version == CONTEXT_PACK_SCHEMA_VERSION

def test_context_pack_invalid_id():
    with pytest.raises(ValidationError):
        ContextPack(
            context_pack_id="invalid_id",
            contract_id="ec_test_123",
            run_id="run_123",
            workspace_id="ws_1",
            user_id="usr_alice",
            active_goal="Goal",
            token_budget=10
        )

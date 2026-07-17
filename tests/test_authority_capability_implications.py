from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
)


def _browser_lease(capability: AuthorityCapability) -> AuthorityLease:
    return AuthorityLease(
        lease_ref=f"authority-lease-ref:test-browser-{capability.value}",
        domains={AuthorityDomain.browser: [capability]},
        safe_summary="Test one exact browser authority capability implication.",
    )


def test_admin_authority_is_exact_and_does_not_imply_unrelated_capabilities() -> None:
    lease = _browser_lease(AuthorityCapability.admin)

    for capability in AuthorityCapability:
        assert lease.grants(AuthorityDomain.browser, capability) is (
            capability == AuthorityCapability.admin
        )

    assert not lease.grants(AuthorityDomain.messages, AuthorityCapability.admin)


def test_destructive_authority_is_exact_and_does_not_imply_unrelated_capabilities() -> None:
    lease = _browser_lease(AuthorityCapability.destructive)

    for capability in AuthorityCapability:
        assert lease.grants(AuthorityDomain.browser, capability) is (
            capability == AuthorityCapability.destructive
        )

    assert not lease.grants(
        AuthorityDomain.messages,
        AuthorityCapability.destructive,
    )

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import AuthorityLease
from ultimate_ai_agent.core.extension_catalog import (
    ExtensionInstallDisabledAuthorityState,
    ExtensionInstallDisabledRecordDeleteReceipt,
    ExtensionInstallDisabledRecordReceipt,
    ExtensionInstallDisabledRecordStore,
)


def record_with_live_authority(
    store: ExtensionInstallDisabledRecordStore,
    receipt: ExtensionInstallDisabledRecordReceipt,
    *,
    approval_authority: LocalApprovalAuthority,
    leases: list[AuthorityLease],
) -> ExtensionInstallDisabledRecordReceipt:
    return store.record_receipt(
        receipt,
        authority_state=ExtensionInstallDisabledAuthorityState(
            leases=leases,
            safe_disable_active=False,
        ),
        approval_authority=approval_authority,
    )


def delete_with_live_authority(
    store: ExtensionInstallDisabledRecordStore,
    receipt: ExtensionInstallDisabledRecordDeleteReceipt,
    *,
    approval_authority: LocalApprovalAuthority,
    leases: list[AuthorityLease],
) -> ExtensionInstallDisabledRecordDeleteReceipt:
    return store.delete_record(
        receipt,
        authority_state=ExtensionInstallDisabledAuthorityState(
            leases=leases,
            safe_disable_active=False,
        ),
        approval_authority=approval_authority,
    )

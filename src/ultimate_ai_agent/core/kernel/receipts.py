from ultimate_ai_agent.core.ledger.ledger import EventLedger
from ultimate_ai_agent.core.ledger.receipts import RunReceipt


def generate_kernel_receipt(ledger: EventLedger, run_id: str) -> RunReceipt:
    return ledger.generate_receipt(run_id)

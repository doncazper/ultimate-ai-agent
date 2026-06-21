from scripts.verify_uaa_p1_068_today_product_spine_contract import main


def test_uaa_p1_068_today_product_spine_contract_verifier_passes() -> None:
    assert main() == 0

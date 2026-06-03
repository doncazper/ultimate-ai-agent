import json

from scripts import manual_local_model_call
from ultimate_ai_agent.core.model_runtime import M23_FIXED_LOCAL_MODEL_PROMPT_ID, FakeLocalModelCallTransport


def test_m23_cli_dry_run_succeeds_without_network_or_approval(capsys):
    code = manual_local_model_call.main(
        [
            "--endpoint",
            "http://127.0.0.1:11434/api/generate",
            "--model",
            "local-model-ref",
            "--fixed-prompt-id",
            M23_FIXED_LOCAL_MODEL_PROMPT_ID,
        ],
        transport=FakeLocalModelCallTransport(),
    )

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["transport_result"]["call_performed"] is False
    assert payload["receipt"]["model_output_non_authoritative"] is True
    assert "prompt_text" not in payload


def test_m23_cli_rejects_execute_without_valid_approval(capsys):
    code = manual_local_model_call.main(
        [
            "--endpoint",
            "http://127.0.0.1:11434/api/generate",
            "--model",
            "local-model-ref",
            "--fixed-prompt-id",
            M23_FIXED_LOCAL_MODEL_PROMPT_ID,
            "--execute-local-call",
            "--approval-ref",
            "approval_m23_missing_decision",
        ],
        transport=FakeLocalModelCallTransport(),
    )

    payload = json.loads(capsys.readouterr().out)
    assert code != 0
    assert payload["decision"]["allowed"] is False
    assert "APPROVAL_DECISION_REQUIRED" in payload["decision"]["reason_codes"]


def test_m23_cli_does_not_accept_arbitrary_prompt_or_auth_arguments():
    parser_help = manual_local_model_call.build_parser().format_help()

    for forbidden_arg in [
        "--prompt",
        "--prompt-file",
        "--stdin",
        "--file",
        "--memory",
        "--openwebui",
        "--api-key",
        "--auth",
        "--authorization",
        "--cookie",
        "--output",
        "--output-file",
    ]:
        assert forbidden_arg not in parser_help

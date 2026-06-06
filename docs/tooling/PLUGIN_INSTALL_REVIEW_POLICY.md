# M79 Plugin Install Review Policy

The M79 policy enables plugin install review contracts only. Plugin install
review is disabled-authority review: it may validate source package ref,
manifest security decision, exact approval binding, static review, sandbox test
plan, Tool Broker mapping, Event Ledger plan, version pin, revocation, and
safe receipt plans.

The policy denies plugin install, plugin enablement, plugin execution, runtime
import, network access, model/provider call, browser automation, shell
execution, mobile device access, remote execution, credentials or cookies, raw
manifest content, raw package content, raw prompt, raw provider payload,
backend route, Control Center control, dependency, and production authority.

Approval refs are identifiers only. `approval_test_*` is not runtime authority.
Model output and OpenWebUI output cannot authorize plugin install review,
plugin install, plugin enablement, or plugin execution. Evaluator boundaries
revalidate safety-critical fields. M80 remains future.

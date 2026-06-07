# Recurring Automation Stop Conditions

M97 recurring automation contracts require explicit stop conditions. Safe stop
condition refs may describe user revocation, expiration, scope withdrawal, risk
change, policy failure, or audit failure.

Stop conditions are contract metadata only in M97. They do not start, stop,
schedule, kill, or execute any runtime process. Missing stop conditions,
duplicate stop conditions, side effects, recurrence runtime, background
execution, cron, daemon, scheduler, backend route, Control Center control,
dependency, and production authority are denied.

Evaluator boundaries revalidate stop-condition fields and model-copy-mutated
unsafe fields.

M98 remains future.

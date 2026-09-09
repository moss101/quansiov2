# 25 — Support and qualification selection

Only three support states exist:
- `REQUIRED_GA`
- `DISABLED_UNTIL_QUALIFIED`
- `UNSUPPORTED`

A profile with implementation code but incomplete mapped qualification remains disabled. Support selection binds exact candidate/configuration plus all required suite reports.

Current canonical profiles are machine-readable in `registries/support-matrix.json`; categories include desktop/web/mobile/CLI clients, hosted isolated/persistent/local/private execution targets, managed browser, and primary/secondary model profiles. No unregistered profile may be advertised as supported.

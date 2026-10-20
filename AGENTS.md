# SDR project development
Read project.lock.json and docs/DEVELOPMENT.md before work. Preserve user changes.
Use the pinned HDL source. Stage reference sources and disposable build products under .work; keep the Python environment under .venv.
Use a local disk for active builds. Stage remote inputs once and retain checksums.
Treat generated SDK exports as potentially stale; compare the current source block design with the intended hardware export.
Keep source compatibility, synthesis, routing, constrained timing, IO timing coverage and physical board validation as separate gates.
Do not weaken constraints to obtain a pass. Record unresolved pin assignments, bank voltages and timing requirements.
This development workflow does not authorize board programming, flash writes or RF transmission.
Keep credentials and account configuration outside the repository.
Do not launch additional AI agents unless explicitly requested.

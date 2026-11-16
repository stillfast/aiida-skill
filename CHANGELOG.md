# Changelog

All notable changes to this repository (not to AiiDA itself).

## [Unreleased]

### Added

- `examples/eos-scan/`: the two-layer example — `workflow.py` describes the
  equation-of-state scan (common-workflows interface, code-agnostic), `submit.py`
  submits it, `analyze.py` reads `structures`/`total_energies` and fits
  Birch-Murnaghan.
- `install/config.env.yeesuan.example`: sanitized real-cluster configuration
  (SLURM, ABACUS + VASP + QE, spack `prepend-text`).
- cases `004-vasprun-partial-columns` and `005-abacus-pseudo-family-naming`.
- DSH installation: the repository is symlinked to `$DSH_HOME/skills/aiida`, so
  the `aiida` skill is discovered automatically and reloads on `git pull`.

## [0.4.0] - 2026-11-16

### Changed

- The whole skill is now in **English**: `SKILL.md`, `SUMMARY.md`, `USAGE.md`,
  every `references/*.md`, `troubleshooting/` (cases and the generated exit-code
  table), the benchmark rubrics and `benchmarks/README.md`. `README.md` keeps a
  Chinese section (`中文说明`) as the human entry point.
- `troubleshooting/regen_exit_codes.py` now emits an English header and table,
  so a regenerated `exit-codes.md` stays English.
- Benchmark rubric *names/titles* are English; the `any:` regexes keep Chinese
  alternatives because the recorded transcripts are Chinese (documented in
  `benchmarks/README.md`).

## [0.3.0] - 2026-11-15

### Added

- `references/05-workchain-recipes.md`: writing a WorkChain (define/outline/
  exit_code, submit + ToContext, expose/exposed, batch-in-a-WorkChain, restart,
  `verdi process repair`).
- `references/06-node-queries.md`: status flags, inputs/outputs, upstream and
  downstream links, QueryBuilder by label/extras, retrieved files and
  `copy_tree`, trajectory arrays, 2.x `create_archive` signature, debug logging,
  `%load_ext aiida` + `%verdi` magics.
- `references/02-installation.md`: conda-only PostgreSQL + RabbitMQ path
  (`initdb`, port 5433, SQL, connection-latency test, `activate.d` auto-start,
  timezone).
- `references/verdi-cheatsheet.md`: 1.x → 2.x command table, `verdi process
  repair`, logging config, caching, Jupyter magics.
- cases `006-daemon-not-running`, `007-old-tutorial-commands`.

## [0.2.1] - 2026-11-15

### Added

- `USAGE.md`: how to use the skill day to day (natural language, explicit
  invocation, human reading), and how to know whether it helps.
- `benchmarks/`: rubric-driven A/B harness (`tasks/`, `score.py`,
  `transcripts/`, `results/pilot-2026-11-15.md`). Pilot: no-tools 0.620,
  tools-only 0.887, tools+skill 0.907.

## [0.2.0] - 2026-11-15

### Added

- `examples/eos-scan/`: two-layer example (workflow.py → submit.py / analyze.py).
- `install/config.env.yeesuan.example`.
- cases `004-vasprun-partial-columns`, `005-abacus-pseudo-family-naming`.

## [0.1.0] - 2026-11-15

### Added

- `SUMMARY.md`: one-page mental model of AiiDA (profile/computer/code, node
  lifecycle, workflow vs scripts layers, three-layer troubleshooting).
- `SKILL.md`: agent entry point (probe-the-environment SOP, red lines).
- `references/01-what-is-aiida.md` … `04-troubleshooting.md`: the four parts.
- `install/`: profile / computer / code / pseudo scripts and `06-doctor.py`.
- `examples/si-scf/`: minimal submit + analyse example with `--dry-run`.
- `troubleshooting/exit-codes.md` and structured case studies.
- `versions.yaml` + `.github/workflows/drift.yml` for maintenance.

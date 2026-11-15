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

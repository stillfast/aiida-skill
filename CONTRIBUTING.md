# Contributing / maintenance

This repository rots in two ways: **upstream versions move** and **the prose
drifts away from reality**. Both are handled mechanically where possible.

## 1. Version drift

- The supported combination lives only in [`versions.yaml`](versions.yaml).
- `install/06-doctor.py` classifies the current environment against it
  (`supported` / `newer-than-tested` / `unsupported`).
- `.github/workflows/drift.yml` runs weekly: it looks up the latest releases of
  the tracked packages and opens an issue when something moved.
- Bumping versions = edit `versions.yaml` + `CHANGELOG.md`, then re-run the
  touched references against the new environment.

## 2. Prose drift

- Every reference file carries frontmatter:

  ```yaml
  ---
  verified: 2026-11
  applies_to: "aiida-core>=2.6,<3"
  ---
  ```

  The drift workflow flags files older than 9 months.
- Claims that depend on a version must not be written as facts about "AiiDA";
  write "in aiida-core 2.8 …" or move the number into `versions.yaml`.

## 3. Executable documentation

- Commands inside references must appear in a runnable script under `install/`
  or `examples/`. If a snippet cannot be executed in CI, mark it explicitly:

  ```markdown
  <!-- not executed in CI: needs a SLURM cluster -->
  ```

- `examples/si-scf` must stay runnable with `--dry-run` on a laptop (no cluster).

## 4. Case studies instead of prose

When a real failure is diagnosed, add `troubleshooting/cases/NNN-<slug>.yaml`
(from `_template.yaml`) rather than a new paragraph. Fields `affects`,
`status` (`open` / `fixed-upstream` / `obsolete`) and `evidence` (real pks)
make stale entries one-field edits instead of rewrites.

## 5. Quarterly review checklist

- [ ] read the release notes of aiida-core + the four plugins
- [ ] check `aiida-common-workflows` protocol/interface changes
- [ ] re-run `examples/si-scf` against the current environment
- [ ] re-check the exit-code table (`python troubleshooting/regen_exit_codes.py`)
- [ ] bump `verified:` dates in files whose claims still hold

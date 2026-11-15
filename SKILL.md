---
name: aiida
description: Use when the user wants to install, configure, run, batch-submit or debug
  AiiDA calculations with aiida-core and its plugins (aiida-abacus, aiida-vasp,
  aiida-quantumespresso, aiida-fleur), or wants to extend/fix the workflow layer
  (aiida-common-workflows) and the submission/analysis scripts. Covers profile /
  computer / code setup, WorkChain submission and monitoring, scheduler and plugin
  error diagnosis, and upstream PR fixes.
whenToUse: The task mentions AiiDA, verdi, WorkChain/CalcJob, aiida-abacus,
  aiida-vasp, common workflows, or asks why a submitted calculation failed.
metadata:
  upstream:
    - aiida-core
    - aiida-abacus
    - aiida-vasp
    - aiida-quantumespresso
    - aiida-fleur
    - aiida-common-workflows
---

# AiiDA

## What this skill gives you

A procedure, not a memory. The API surface of AiiDA and its plugins changes;
**always probe the installed environment before answering** and prefer the
values you read over the values written here.

Read `SUMMARY.md` first: it is the one-page mental model (profile/computer/code
→ node graph → workflow layer → scripts layer → three-layer troubleshooting).

## SOP

1. **Probe the environment** (never skip):
   ```bash
   verdi status                       # daemon / broker / storage / profile
   python install/06-doctor.py        # profile, computers, codes, pseudos, versions
   ```
   Compare the reported versions with `versions.yaml`. On
   `newer-than-tested` continue but say so; on `unsupported` stop and point the
   user to the matching git tag.

2. **Identify the layer** the user is working on:

   | Layer | Entry point | Reference |
   |---|---|---|
   | install / configure | `verdi profile/computer/code` | `references/02-installation.md` |
   | workflow | `verdi plugin list aiida.workflows`, `get_builder_from_protocol` | `references/03-usage-workflow.md` |
   | batch submit / analyse | `submit()`, submission controller | `references/03-usage-scripts.md` |
   | failure | `verdi process show/report` | `references/04-troubleshooting.md` |

3. **Never trust ports from memory.** Run `verdi plugin list aiida.workflows <name>`
   (or `verdi plugin list aiida.calculations <name>`) and build inputs from the
   ports that actually exist. Take the protocol via
   `get_builder_from_protocol(...)` rather than hand-constructing inputs.

4. **Dry-run before submit.** Build the builder, validate it
   (`spec().inputs.validate(builder._inputs(prune=True))`), print the resolved
   `metadata.options` (queue, wallclock, resources) and the k-points/ecutwfb
   actually used. Only then `submit()`.

5. **Diagnose in order**: configuration → plugin → DFT code. Use exit codes
   (`troubleshooting/exit-codes.md`) and the case YAMLs
   (`troubleshooting/cases/`) before reading any source code.

## Red lines

- Do not modify a stored node to "fix" a run — submit a new process instead.
- Do not `submit()` to a scheduler computer when the child `metadata.options`
  has no `queue_name`; that produces `sbatch: No partition specified` and five
  failed transport retries. Fail fast and tell the user the options preset did
  not reach the WorkChain.
- Do not restart the daemon without saying so: it interrupts in-flight jobs'
  status polling (not the jobs themselves) and drops any process instance that
  still runs old code.
- Do not present a formation energy / band gap / elastic constant computed from
  a run whose SCF or ionic convergence is not verified.
- When a fix belongs upstream (aiida-core / plugin), write the minimal
  reproduction and open an issue/PR; do not patch site-packages in place
  without telling the user that a reinstall will drop it.

## Files

| Path | Content |
|---|---|
| `SUMMARY.md` | one-page mental model (human) |
| `references/01-what-is-aiida.md` | concepts: nodes, processes, provenance |
| `references/02-installation.md` | env → profile → computer → code → pseudo → daemon |
| `references/03-usage-workflow.md` | plugin WorkChains and common-workflows interfaces |
| `references/03-usage-scripts.md` | batch submission and analysis |
| `references/04-troubleshooting.md` | three-layer diagnosis, exit-code table, upstream PRs |
| `install/` | scripts derived from the references, runnable |
| `examples/` | minimal runnable examples |
| `troubleshooting/` | exit-code table + structured case studies |

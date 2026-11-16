---
verified: 2026-11
applies_to: "aiida-core>=2.6,<3"
---

# 1. What AiiDA Is, and What It Is Used With

## 1.1 Definition

AiiDA is a **workflow engine + provenance database for computational science**. It does not do DFT; what it does is:

| Capability | Traditional approach | AiiDA approach |
|---|---|---|
| Submission | Hand-written sbatch / input files | Describe the inputs; the plugin generates the files and submits |
| Tracing | Dig through directories, look at `history` | Every input/output is a node with a UUID, linked into a graph |
| Retry | Manually spot the failure and start over | Handlers in a WorkChain act on exit codes automatically |
| Batching | Write a shell for loop | Process inputs are data nodes and can be generated programmatically |

Three keywords in the design:

- **Provenance**: any result can answer "which inputs, which code, which run produced it".
- **Reproducibility**: nodes are immutable; changing a parameter = a new node, and the old record is kept.
- **Workflow**: flows such as "SCF → relax → convergence check → restart" are written as re-entrant Processes.

## 1.2 Composition

```
aiida-core           engine (Process interface, Node model, verdi CLI) + storage backend
  ├── PostgreSQL     primary database (node metadata, links) — for production
  ├── SQLite         lightweight backend (single-machine practice)
  ├── RabbitMQ       inter-process communication; the daemon depends on it
  ├── file repository large objects (structures, retrieved files) written to disk; the database stores only hashes
  └── daemon         background worker; the process that actually executes and polls the scheduler
Plugins (entry points)  one per code: CalcJob (input generation + parser) + WorkChain (flow)
  ├── aiida-abacus
  ├── aiida-vasp
  ├── aiida-quantumespresso
  └── aiida-fleur
aiida-common-workflows unified interface across codes (relax / eos / bands … + protocol levels)
Script layer (e.g. acwf-verification-scripts) batch submission + result analysis
```

`verdi` is the command-line entry point; every operation ultimately lands on two kinds of objects, "Process" and "Node".

## 1.3 Data model (just enough)

| Type | Example | Description |
|---|---|---|
| **Data** | `StructureData`, `Dict`, `Int`, `FolderData` | Calculation inputs/outputs; immutable once stored |
| **CalcJob** | `AbacusCalculation`, `VaspCalculation` | One real invocation of an external program; has `retrieved` (local files), `remote_folder` (cluster path), `exit_status` |
| **WorkChain** | `abacus.relax`, `vasp.v2.relax` | Orchestrates multiple CalcJobs; can retry and branch |
| **outputs of ProcessNode** | `output_parameters`, `misc`, `structure` | Read by downstream steps |

Links connect nodes into a graph. `verdi process show <pk>` shows the direct inputs and outputs,
`verdi node graph generate <pk>` (or `Graph()`) can draw the whole graph.

## 1.4 Process states and exit codes

- `ProcessState`: `created → waiting → running → finished` (plus `exited`, `killed`).
- `exit_status`: `0` for success; `None` if not finished yet; the **meaning of a non-zero value is defined by the plugin**, it is not a unified numbering.
  So when troubleshooting, "look at the exit code" must be combined with **which plugin** it comes from (see `04-troubleshooting.md`).
- `verdi process report <pk>` prints the log of that process; `verdi process status <pk>` prints the child process tree.

## 1.5 When not to use AiiDA

- One-off, fixed-parameter single-point calculations: writing sbatch directly is faster.
- Interactive debugging that needs very low latency: AiiDA has daemon polling overhead.
- Nobody on the team is willing to maintain the profile/computer/code configuration.

But as soon as any one of "many structures × many parameters", "provenance is needed" or "failures must be retried automatically" applies,
the benefit of AiiDA far outweighs the configuration cost.

## 1.6 Adjacent tools in the ecosystem

| Tool | Purpose |
|---|---|
| ASE / pymatgen | Structure construction and conversion (`StructureData(ase=atoms)`) |
| aiida-pseudo | Pseudopotential family management (SSSP etc.) |
| aiida-phonopy | Phonon post-processing |
| aiida-common-workflows | Unified interface across codes, for verification/comparison |
| aiida-submission-controller | Batch submission controller (used by `03-usage-scripts.md` in this repository) |

---
verified: 2026-11
applies_to: "aiida-core>=2.6,<3"
---

# 4. Testing and Failure Analysis

Troubleshoot failures in three layers, "from the outside in". **Rule out configuration first, then suspect the plugin, and only last the DFT code**.

```
① Configuration layer (profile / computer / code / metadata.options)
        ↓ rule out
② Plugin layer (aiida-core, aiida-abacus, aiida-vasp …)
        ↓ rule out
③ DFT code layer (ABACUS / VASP / QE and their exit codes)
```

## 4.1 Layer 1: Parameter configuration errors

Typical symptoms: **the job was never submitted at all**, or **it was submitted but every parameter is wrong**.

| Symptom | Where to look | Fix |
|---|---|---|
| `sbatch: No partition specified or system default partition` | no `queue_name` in the child CalcJob's `metadata.options` | Check whether the options really reach the child job; see 4.5 |
| `Pausing after failed transport task: submit_calculation failed 5 times` | the follow-up of the row above: paused after 5 consecutive submission failures | Fix the partition/connection, then `verdi process kill` and **resubmit** (playing a paused process replays the same bad inputs) |
| `Computer test` fails | ssh / work directory / scheduler command | `verdi computer configure`, check permissions of `work-dir` |
| `Code not found` / `command not found` at runtime | the code's path or `prepend-text` | `verdi code show <label>`, run the path once manually on the cluster |
| `Could not determine the current profile` | no `load_profile()` in the script | Explicitly call `load_profile('aiida_profile')` |
| Job runs on 1 core and is extremely slow | `resources` not taking effect | Print `metadata.options['resources']` |

The first steps are always:

```bash
verdi status
verdi process show <pk>
verdi process report <pk>          # the real exception stack is here
verdi computer test <label>
verdi code show <label>
```

### Especially common: metadata.options silently lost

**Symptom**: after resubmitting a WorkChain (`get_builder_restart()`), the child job has no partition.

**Cause**: if scheduler parameters are placed in a **dynamic namespace** (for example
`base.abacus.metadata.options`), AiiDA neither stores them as input links nor writes them into
`metadata_inputs`; `get_builder_restart()` rebuilds only from these two places, so the parameters are lost,
and the child job is submitted with AiiDA defaults (1 core, no queue).

**Fix**: put the options in a **regular input port** (such as an `options` Dict), and let the
WorkChain merge them into the child job's `metadata.options` at `submit` time; add fail-fast:
raise an error when `queue_name` is absent, rather than waiting for sbatch to fail 5 times.

**Verify**:

```python
load_node(orig_pk).get_builder_restart().base['abacus']   # check whether the metadata is still there
```

## 4.2 Layer 2: bugs in upstream repositories

Criterion: a **minimal reproduction** reproduces in a clean environment and has nothing to do with your cluster/parameters.

1. Write a minimal script (one structure, one WorkChain, default protocol);
2. Check on the main branch of `aiida-core` / the plugin repository whether it is already fixed;
3. It is a bug → open an issue (with the minimal script, versions, traceback) → submit a PR (with a regression test);
4. Temporary workaround: change parameters via `overrides`, or switch to another WorkChain; do **not** edit
   `site-packages` directly (lost on reinstall; if you do patch locally, state it in the issue).

Common shapes of upstream problems:

| Shape | Example | Fix |
|---|---|---|
| parser field missing / column count changed | the `<partial>` column count in vasprun changed | switch the parsing path (e.g. DOSCAR), or fix the parser |
| WorkChain port inconsistency | a new plugin version changed the namespace | the adapter layer supports old and new; `verdi plugin list` is authoritative |
| handler does not handle some exit code | killed by wall clock (301) does not trigger the convergence handler | add a handler or raise the wall clock |
| unreasonable default parameter | `mixing_beta=0.8` causes charge sloshing | override it in the protocol/preset and file an upstream issue |

## 4.3 Layer 3: the DFT code itself

The job **really did run**; AiiDA merely records it faithfully. At this point look at the exit code and the raw logs.
The full cross-reference table is in [`troubleshooting/exit-codes.md`](../troubleshooting/exit-codes.md).

Quick checks:

| Symptom | Look at first | Common cause |
|---|---|---|
| ABACUS 301 | `_scheduler-stderr.txt`, end of `running_scf.log` | wall clock kill, OOM, MPI/UCX timeout |
| ABACUS 302 | the DRHO column of `running_scf.log` | SCF charge sloshing (`mixing_beta` too large) |
| ABACUS 303/401 | ionic step count, `relax_nmax` | not enough ionic steps / retries exhausted |
| VASP 700 | `OUTCAR`, `vasp.out` | did not finish (ZBRENT, electronic step failure) |
| `Signal 9` | sacct / stderr | killed for exceeding memory |
| `DUE TO TIME LIMIT` | stderr | insufficient wall clock |

Parameter-tuning experience (from real cases):

- **Charge sloshing**: `mixing_type=broyden, mixing_beta=0.2, mixing_ndim=20~24,
  mixing_gg0=1.5` often lets metallic/5f systems converge;
- **Not enough time**: first measure the cost of one SCF step × the estimated number of steps, then set the wall clock; LCAO is about 100 s/step,
  PW can reach 300–1300 s/step;
- **Ionic steps exhausted**: increase `relax_nmax` / `max_ionic_steps`, or let the WorkChain
  continue from the latest structure (the plugin's handler usually supports this).

## 4.4 Standard diagnostic actions

```bash
verdi process show <pk>            # state / exit_status / inputs and outputs
verdi process report <pk>          # log and handler actions
verdi process status <pk>          # child process tree, to locate which layer failed
verdi calcjob gotocomputer <pk>    # print the remote directory on the cluster
```

```python
node = load_node(pk)
node.outputs.retrieved.open('...') # files retrieved locally
node.base.attributes.all           # the queue/resources/wallclock actually in effect
```

## 4.5 Post-mortem: write the pitfalls down

Write every diagnosed failure as one `troubleshooting/cases/NNN-<slug>.yaml`
(template `_template.yaml`), with fields including: symptom, error signature regex, diagnostic steps, root cause,
fix, affected versions, evidence (a real pk). That way the same log can be matched directly next time,
and after a version upgrade you can change `status` to `fixed-upstream`.

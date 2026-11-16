# How to use this skill day to day

Three ways to use it, ordered by how much you need to get involved.

## 1. Just state what you need (most common)

The skill is already installed into DSH (`$DSH_HOME/skills/aiida` → this repository), and **needs no commands**.
Just describe the task naturally in the conversation and the agent will load it on its own:

| You say | What the agent does |
|---|---|
| "Give this α-U structure an SCF run with ABACUS" | Probe the environment with `verdi status` + `06-doctor.py` → check the actual ports of `abacus.base` → build the builder → print queue/wall time/cores → validate with a dry-run → submit after you confirm |
| "Why did job 564954 fail?" | `verdi process show/report` → see which layer the exit code belongs to → check `troubleshooting/exit-codes.md` and the cases → give a conclusion and next step |
| "Help me resubmit the two stuck defects jobs" | First find the cause of the stall (e.g. `No partition specified`) → fix the inputs → kill → resubmit → verify the child job's `queue_name` |
| "I want to relax 20 structures in a batch" | Suggest getting a single one working first (workflow layer), then provide the scripts-layer SubmissionController template |
| "In AiiDA, how do profile/computer/code relate?" | Answer directly from the mental model in `SUMMARY.md` |

**When stating a request, it helps to include**: `pk`/`uuid`, the full error text, the exit code, and the cluster and queue name.
The agent will use them to look up nodes instead of guessing.

## 2. Naming the skill explicitly

If you want the agent to definitely follow this workflow (for example, you are afraid it will write ports from memory):

> Use the **aiida** skill to do this: ……

Or ask up front:

> Run `install/06-doctor.py` first, then follow the skill's SOP.

## 3. Using it yourself (without the agent)

```bash
cd ~/work/aiida-skill
less SUMMARY.md                 # understand AiiDA in 10 minutes
python install/06-doctor.py     # environment self-check
less references/02-installation.md
```

When setting up a new environment: copy `install/config.env.yeesuan.example` → change paths/queues → run `install/0*.sh` in order.

## How to tell whether it works

`benchmarks/` holds one controlled experiment (the same 5 questions answered under three conditions: no skill, tools only, and with the skill):
pure knowledge 0.62 → allowed to inspect the environment 0.89 → with the skill 0.91. Reproduction steps and limitations are in
[`benchmarks/results/pilot-2026-11-15.md`](benchmarks/results/pilot-2026-11-15.md).

## How it "updates itself"

- the skill directory is a symlink to `~/work/aiida-skill`; after `git pull`, DSH's file watcher re-reads it — **no reinstall, no restart**;
- when the environment changes, run `06-doctor.py` first: if a version is outside the range supported by `versions.yaml` it will tell you explicitly, instead of blindly running from old docs;
- every time you hit a new pitfall, have the agent write it up as `troubleshooting/cases/NNN-*.yaml` and commit it — that is how the repository grows.

## When you don't need it

- purely asking about DFT physics parameters (how to choose `ISMEAR` in INCAR, how large the k-mesh should be) — that is a computational physics question, not an AiiDA question;
- something already running and you just want to see progress: `verdi process list` is enough.

## One reminder

The skill's value is the **process** (probe the environment first → then check the ports → dry-run first → then triage in three layers),
not "memorized answers". That is why it always makes you look at the current environment rather than trusting the old version numbers in the docs.

# Does the skill actually help? A/B protocol

The skill is a set of *procedures* (probe the environment, look up real ports,
dry-run before submit, diagnose in three layers). To check it is worth its
upkeep, run a small paired evaluation: same tasks, same model, one arm with the
skill installed and one without.

## What is measured

| metric | how |
|---|---|
| task score | rubric in `tasks/t*.yaml`: weighted checks (regex over the answer), `must_not` entries cancel the task |
| perfect tasks | score == 1.0 |
| rubric violations | answers that assert something the rubric forbids (e.g. "play the paused job") |
| (optional) cost | turns / tokens / wall time, if the runner records them |

Rubrics are deliberately *fact-based*, not style-based: they check that the
answer names the right mechanism (`metadata.options`, `queue_name`,
`get_builder_restart`, `mixing_beta`, `SubmissionController`) and does not assert
a wrong one (`302 = 墙钟`). This keeps the score reproducible and cheap.

## Results so far

`results/pilot-2026-11-15.md` — 5 tasks, three arms (no tools / tools / tools+skill):
0.620 / 0.887 / 0.907. Read its "limitations" section before quoting the delta.

## Two arms

| arm | setup |
|---|---|
| **baseline** | the skill directory is *not* visible (`mv $DSH_HOME/skills/aiida /tmp/…`), fresh agent session, same model |
| **skill** | skill installed normally (`$DSH_HOME/skills/aiida` → this repository) |

Both arms get the **same prompt**, are allowed the same tools, and are run in a
fresh session per task (no conversation carry-over). The baseline prompt adds
one control sentence: *"仅凭你自己的知识回答，不要读取本地文件或使用预置 skill"*,
so that it cannot simply read this repository.

## Procedure

```bash
# 0) sanity: the two catalogs differ
mv "$DSH_HOME/skills/aiida" /tmp/aiida-skill.link      # baseline arm
#   … run baseline sessions, save each answer as transcripts/baseline/t1.md …
mv /tmp/aiida-skill.link "$DSH_HOME/skills/aiida"      # skill arm
#   … run treatment sessions, save transcripts/skill/t1.md …

# 1) score
python benchmarks/score.py --dir transcripts/baseline
python benchmarks/score.py --dir transcripts/skill

# 2) paired table
python benchmarks/score.py --a transcripts/baseline --b transcripts/skill \
    --label-a baseline --label-b skill --markdown benchmarks/results/pilot-<date>.md
```

Record in the result file: date, model, number of repetitions, and whether the
skill catalog was really absent in the baseline arm (the check in step 0).

## What this cannot tell you

- **Small N**: 5 tasks is a pilot, not a measurement. With N tasks and 1 run each
  a single lucky answer moves the mean by 0.2. Repeat ≥3 times, report the spread.
- **Task selection bias**: the tasks come from the real failure cases the skill
  documents, so they favour the skill. Keep generic tasks (t1, t5) as controls.
- **Judge = regex**: an answer can be right in other words and score low. Inspect
  misses before concluding the skill is bad.
- **Contamination**: if the baseline agent still knows AiiDA from pretraining, the
  delta measures *extra* guidance, not "knows vs does not know AiiDA".

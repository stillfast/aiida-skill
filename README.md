# aiida-skill

An AiiDA handbook: **installation, usage and debugging** — written as a
human-readable guide *and* an agent skill.

- **Just want to understand how AiiDA works?** read [`SUMMARY.md`](SUMMARY.md) (one page, with diagrams)
- **Need to install / configure / run?** start at [`references/02-installation.md`](references/02-installation.md), scripts in `install/`
- **Something failed?** [`references/04-troubleshooting.md`](references/04-troubleshooting.md) + `troubleshooting/exit-codes.md`
- **Using it as an agent skill?** put this directory on the skill search path; entry point is [`SKILL.md`](SKILL.md)
- **Is it actually useful?** see [`benchmarks/results/pilot-2026-11-15.md`](benchmarks/results/pilot-2026-11-15.md)

## Layout

```
.
├── SKILL.md                   # agent entry: when to use, SOP, red lines
├── SUMMARY.md                 # one-page mental model (read this first)
├── USAGE.md                   # how to use the skill day to day
├── references/                # the four parts + two handbooks
│   ├── 01-what-is-aiida.md
│   ├── 02-installation.md
│   ├── 03-usage-workflow.md
│   ├── 03-usage-scripts.md
│   ├── 04-troubleshooting.md
│   ├── 05-workchain-recipes.md     # writing your own WorkChain
│   ├── 06-node-queries.md          # reading results / debugging queries
│   └── verdi-cheatsheet.md
├── install/                   # runnable setup scripts + doctor + upstream checker
│   └── config.env.yeesuan.example  # sanitized real-cluster config (ABACUS+VASP+QE)
├── examples/
│   ├── si-scf/                # minimal: single point (build → validate → submit → analyse)
│   └── eos-scan/              # two layers: workflow.py → submit.py / analyze.py
├── troubleshooting/           # exit-code table (generated) + structured case studies
├── benchmarks/                # skill-effectiveness A/B harness and results
├── versions.yaml              # the version combination this guide was verified against
└── CHANGELOG.md / CONTRIBUTING.md
```

## Quick start

```bash
git clone https://github.com/stillfast/aiida-skill.git
cd aiida-skill

cp install/config.env.example install/config.env   # cluster, account, paths
bash install/01-env.sh                             # conda env + aiida-core + plugins
bash install/02-profile.sh                         # profile
bash install/03-computer.sh                        # computer
bash install/04-code.sh                            # code
bash install/05-pseudo.sh                          # pseudopotentials
python install/06-doctor.py                        # self-check: all green before computing
```

Then run the first example:

```bash
cd examples/si-scf
python submit.py --dry-run     # build and validate only, nothing submitted
python submit.py               # submit
python analyze.py <pk>         # read the result
```

The two-layer example (workflow first, scripts second):

```bash
cd examples/eos-scan
python workflow.py --dry-run                              # describe only
python submit.py --code qe@mycluster --element U          # submit an EOS scan
python analyze.py <pk> --json eos.json                    # read + Birch-Murnaghan fit
```

## Using it as a skill

```bash
ln -sfn "$PWD" "$DSH_HOME/skills/aiida"    # DSH picks it up live
```

Then ask in natural language ("relax this structure with VASP", "why did 574597
fail"); the agent runs `install/06-doctor.py` first and follows the SOP in
`SKILL.md`. `git pull` is enough to update it — no reinstall, no restart.

## Maintenance

See [`CONTRIBUTING.md`](CONTRIBUTING.md): the version matrix, the weekly drift
workflow, executable documentation, and turning every real failure into a case
YAML.

## Chinese quick note / 中文说明

这个仓库是 AiiDA 的安装与使用手册，同时也是 DSH/Claude 可加载的 skill。
正文（`SKILL.md`、`SUMMARY.md`、`USAGE.md`、`references/`、`troubleshooting/`）为英文；
本 README 保留中文说明。

- 只想快速理解 AiiDA：读 `SUMMARY.md`（一页，带图）
- 装环境：抄 `install/config.env.yeesuan.example`，改路径/队列，依次跑 `install/0*.sh`
- 用的时候不用敲命令：把目录链接进 `$DSH_HOME/skills/aiida`，在对话里直接说需求
- 它到底有没有用：见 `benchmarks/results/pilot-2026-11-15.md`（分三组对照，含局限）
- 更新：`cd ~/work/aiida-skill && git pull`

## License

MIT

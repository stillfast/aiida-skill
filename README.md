# aiida-skill

AiiDA 的安装与使用说明，写成「人读的教程 + agent 可加载的 skill」两种形态。

- **只想快速理解 AiiDA 怎么用** → 读 [`SUMMARY.md`](SUMMARY.md)（一页，含图）
- **要装/配/跑** → 从 [`references/02-installation.md`](references/02-installation.md) 开始，脚本在 `install/`
- **出错了** → [`references/04-troubleshooting.md`](references/04-troubleshooting.md) + `troubleshooting/exit-codes.md`
- **让 agent 用** → 把本目录放进 skill 搜索路径，入口是 [`SKILL.md`](SKILL.md)

## 仓库结构

```
.
├── SUMMARY.md                 # 人能看懂的一页总结（建议先读）
├── SKILL.md                   # agent 入口：触发条件 + SOP + 红线
├── references/                # 四部分正文
│   ├── 01-what-is-aiida.md
│   ├── 02-installation.md
│   ├── 03-usage-workflow.md
│   ├── 03-usage-scripts.md
│   ├── 04-troubleshooting.md
│   └── verdi-cheatsheet.md
├── install/                   # 可执行安装脚本（profile/computer/code/pseudo/doctor）
│   └── config.env.yeesuan.example  # 真实集群（ABACUS+VASP+QE）的脱敏配置
├── examples/
│   ├── si-scf/                # 最小例子：单点 SCF（构建 → 校验 → 提交 → 分析）
│   └── eos-scan/              # 两层例子：workflow.py（描述）→ submit.py / analyze.py
├── troubleshooting/           # exit code 表 + 结构化案例
├── benchmarks/                # skill 有效性 A/B 评测（rubric + 打分器 + 结果）
│   └── results/pilot-2026-11-15.md
├── versions.yaml              # 这套流程验证过的版本组合
└── CHANGELOG.md / CONTRIBUTING.md
```

## 快速开始

```bash
git clone https://github.com/stillfast/aiida-skill.git
cd aiida-skill

cp install/config.env.example install/config.env   # 填集群/账号/路径
bash install/01-env.sh                            # conda env + aiida-core + 插件
bash install/02-profile.sh                        # profile
bash install/03-computer.sh                       # computer
bash install/04-code.sh                           # code
bash install/05-pseudo.sh                         # 赝势/轨道
python install/06-doctor.py                       # 自检，全绿再开始算
```

然后跑第一个例子：

```bash
cd examples/si-scf
python submit.py --dry-run     # 只构建并校验输入，不提交
python submit.py               # 提交
python analyze.py <pk>         # 读结果
```

完整的两层例子（先 workflow 再 scripts）：

```bash
cd examples/eos-scan
python workflow.py --dry-run                              # 只描述计算，不提交
python submit.py --code qe@mycluster --element U          # 提交 EOS 扫描
python analyze.py <pk> --json eos.json                    # 读结果 + Birch-Murnaghan 拟合
```

## 这个 skill 到底有没有用

`benchmarks/` 里有一套可复现的 A/B 评测（5 个任务、三组对照、rubric 打分）。
最近一次 pilot：纯知识 0.62 / 允许查环境 0.89 / 加 skill 0.91——结论和局限都写在
[`benchmarks/results/pilot-2026-11-15.md`](benchmarks/results/pilot-2026-11-15.md)。

```bash
python benchmarks/score.py --dir benchmarks/transcripts/skill
python benchmarks/score.py --a benchmarks/transcripts/baseline_tools \
    --b benchmarks/transcripts/skill --label-a tools --label-b skill
```

## 维护

见 [`CONTRIBUTING.md`](CONTRIBUTING.md)：版本矩阵、CI 漂移检测、把真实故障写成 case YAML。

## 许可

MIT

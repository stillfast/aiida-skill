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
├── examples/si-scf/           # 最小可跑例子：提交 + 分析
├── troubleshooting/           # exit code 表 + 结构化案例
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

## 维护

见 [`CONTRIBUTING.md`](CONTRIBUTING.md)：版本矩阵、CI 漂移检测、把真实故障写成 case YAML。

## 许可

MIT

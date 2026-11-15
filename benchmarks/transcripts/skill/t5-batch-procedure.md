=== 实测环境（已 probe，非记忆）===
- profile `aiida_profile`，daemon 运行中；aiida-core 2.8.0.post0，aiida-vasp 5.1.0
- VASP code：vaspstd@yeesuan / vaspstd@xinghe / vaspstd@guangzhou
- POTCAR 家族：PBE(327)、LDA(295)；协议默认要 PBE.54，本机不存在，不显式 overrides 会 InputValidationError
- relax 协议：vasp.v2.relax 只有 balanced / fast（precise→stringent 本版本 KeyError）
- dry-run 实测 balanced：ENCUT=550、kpoints_spacing=0.05、steps=60、force_cutoff=0.03、ISIF=3
- 可复用：aiida-uranium-workflow 已有 relax 调度 + VaspRelaxAdapter；aiida-batch 只有 vasp.base.batch / vasp.band.batch，没有 relax
- common_workflows.relax.vasp 没有 get_builder_from_protocol，需 get_input_generator()

=== 方案要点 ===
1) 三层组织：数据层（StructureData + SHA256 幂等入库）、参数层（scf_vasp.yml / relax.yml / resources.yml）、编排层（一个结构 = 一个独立 WorkChain，禁止塞进同一个 WorkChain 里 for 循环）
2) 目录：data/structures/*.vasp、config/*.yml、01_import.py / 02_submit.py / 03_monitor.py / 04_collect.py、runs/<date>/output.json
3) 六步流程 + 闸门：入库→建参数→validate→限流提交（aiida-submission-controller 0.1.2，MAX_CONCURRENT≈8）→按退出码巡检→汇总验收
4) 骨架代码：哈希幂等 get_or_make、get_builder_from_protocol + validate + 打印 ENCUT/queue、SubmissionController 子类、状态矩阵与汇总
5) 七个坑：PBE.54 家族名、协议名只有 balanced/fast、ISIF=7 Brent 在噪声 E(V) 上 ZBRENT 崩（改 ISIF=3）、nsw:0 被 incar 命名空间覆盖导致弛豫变静态、wallclock 按 60 步预算、节点不可回改只能重提、并发别开满（20×56=1120 核）
6) 验收：dry-run 参数透传一致；20/20 exit_status==0；力/体积收敛达标；三者全绿才可用晶格常数

=== 待确认问题 ===
Q1 交付形态：只要流程+骨架，还是落地成可运行脚本文件？
Q2 20 个结构来源：本地 20 个 POSCAR/CIF 目录 / AiiDA 已有 pk 列表 / 应变或相枚举生成？
Q3 路径与机器：复用 aiida-uranium-workflow 的 relax+VaspRelaxAdapter / 裸脚本 / 给 aiida-batch 加 vasp.relax.batch；跑 yeesuan 还是 xinghe/guangzhou？

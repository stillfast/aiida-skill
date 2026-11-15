【AiiDA 批量 VASP 弛豫 20 结构：组织方案（纯知识回答，未读文件/未跑命令/未用 skill）】

一、总体结论
20 个结构属中小规模，最稳做法：一个 Group 放 20 个 StructureData + 一个脚本循环 submit(VaspRelaxWorkChain) + 另一个 Group 放 20 个流程节点 + 独立汇总脚本。不建议一上来自己写"大 BatchWorkChain 包 20 个弛豫"。需要"一个根节点"时再用 AiiDA 2.x WorkGraph 或薄封装 WorkChain。

流程：POSCAR×20 → 02_import.py → StructureData×20（extras: material_id）→ Group bcc-u-structures → 03_submit.py 构造 inputs + 幂等过滤 → VaspRelaxWorkChain×20 → VaspCalculation×N → SLURM/本地 → 04_monitor.py（QueryBuilder）→ 05_collect.py 汇总 CSV/JSON。

二、一次性准备
verdi setup/quicksetup；Computer；verdi code create core.code.installed 注册 vasp_std；verdi data vasp-potcar uploadfamily -P <目录> -N PBE；verdi daemon start 4（并发按队列额度定）；verdi group create ...

三、脚本结构
vasp-relax-batch/
├── config/settings.yaml
├── config/overrides.yaml
├── config/structures/
├── src/common.py
├── src/01_setup_check.py
├── src/02_import.py
├── src/03_submit.py
├── src/04_monitor.py
├── src/05_collect.py
├── workchains/batch_relax.py
├── tests/smoke_one.py
└── README.md

四、关键代码骨架
03_submit.py（幂等）：
    sgroup = orm.load_group('bcc-u-structures'); pgroup = orm.load_group('bcc-u-processes')
    done = {p.extras.get('material_id') for p in pgroup.nodes if p.is_finished_ok}
    for s in sgroup.nodes:
        mid = s.extras['material_id']
        if mid in done: continue
        node = engine.submit(VaspRelaxWorkChain, **build_relax_inputs(...))
        node.set_extra('material_id', mid); pgroup.add_nodes(node)

监控：QueryBuilder；失败看 verdi process report <PK>。
收集：p.outputs.output_structure、p.outputs.output_parameters.get_dict()['final_energy']、pandas 写 CSV。

五、关键坑
赝势 mapping、POTCAR 顺序；kpoints_spacing 优于固定 mesh；金属 ISMEAR=1/2；EDIFFG<0 是力判据；ISIF=3；磁性 MAGMOM；NCORE/KPAR 与 MPI；20 个同时提交会挤爆队列；max_wallclock_seconds；aiida-vasp BaseRestartWorkChain handler；LWAVE/LCHARG=false；提交前查 group 做幂等；verdi archive create。

六、运行顺序
verdi daemon start 4 → 01_setup_check → 02_import → tests/smoke_one.py（先 1 个跑通）→ 03_submit → 04_monitor → 05_collect。先估总机时再提交。

注：VaspRelaxWorkChain 端口名随版本有差异，落地前用 verdi plugin list 核对。

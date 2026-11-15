已完成：diamond Si（a=5.43 Å）单点 SCF 的 aiida-abacus builder（只构建、不提交），代码在本机 aiida 环境实跑验证（aiida-core 2.8.0 / aiida-abacus 0.3.3 / profile aiida_profile），并用插件自己的 prepare_for_submission 生成了 INPUT/STRU/KPT 核对。

关键 API 事实（从已安装插件 spec 读出来的）：
- entry point `abacus.abacus` → AbacusCalculation，输入端口：structure、kpoints、pseudos（命名空间，{kind: UpfData}）、parameters、settings、dynamics、extra_files、metadata.options。code 用 `load_code(...).get_builder()`。
- parameters 是两段 Dict：`{"input": {...}}` → INPUT；`{"stru": {...}}` → STRU 关键字。插件自动补 suffix/pseudo_dir/orbital_dir。
- 单位：StructureData 用 Å；插件默认写 LATTICE_CONSTANT 1.889726125457828（bohr）。ecutwfc/scf_thr 用 Ry。
- 注意：把 stru_settings 赋给 builder.settings 是过时写法；STRU 关键字要放 parameters["stru"]。

核心代码：
```python
import numpy as np
from aiida import load_profile, orm
load_profile()
A_SI = 5.43
CODE_LABEL = "abacus_lts@yeesuan"
PSEUDO_FAMILY = "SSSP/1.3/PBE/efficiency"

def diamond_si(a=A_SI):
    fcc = np.array([[0.,1.,1.],[1.,0.,1.],[1.,1.,0.]])
    cell = 0.5 * a * fcc
    s = orm.StructureData(cell=cell)
    s.append_atom(position=(0.,0.,0.), symbols="Si")
    s.append_atom(position=tuple(0.25*cell.sum(axis=0)), symbols="Si")
    return s

def build_si_scf_builder(code_label=CODE_LABEL, a=A_SI, kpoints_mesh=(6,6,6),
                         ecutwfc=60.0, num_mpiprocs_per_machine=8,
                         max_wallclock_seconds=3600, queue_name=None):
    structure = diamond_si(a)
    parameters = {"input": {"calculation": "scf", "basis_type": "pw", "ecutwfc": ecutwfc,
        "scf_thr": 1e-7, "scf_nmax": 100, "ks_solver": "dav_subspace",
        "symmetry": 1, "device": "cpu", "precision": "double"}}
    builder = orm.load_code(code_label).get_builder()
    builder.structure = structure
    kp = orm.KpointsData(); kp.set_kpoints_mesh(list(kpoints_mesh), offset=[0.,0.,0.])
    builder.kpoints = kp
    builder.pseudos = orm.load_group(PSEUDO_FAMILY).get_pseudos(structure=structure)
    builder.parameters = parameters
    options = {"resources": {"num_machines": 1, "num_mpiprocs_per_machine": num_mpiprocs_per_machine},
               "max_wallclock_seconds": max_wallclock_seconds, "withmpi": True}
    if queue_name: options["queue_name"] = queue_name   # slurm 必填
    builder.metadata.options = options
    return builder
```

实际生成（截断）：INPUT device cpu / ecutwfc 60.0 / suffix aiida / pseudo_dir ./pseudo/；STRU ATOMIC_SPECIES Si … Si.pbe-n-rrkjus_psl.1.0.0.UPF、LATTICE_CONSTANT 1.8897、ATOMIC_POSITIONS Cartesian；KPT Gamma 6 6 6。

“不提交也要看打包结果”：instantiate_process + prepare_for_submission(SandboxFolder())，已跑通。

必要说明：赝势必须 UPF；Si 半导体不需要 smearing；slurm 漏 queue_name 会得到 “sbatch: No partition specified” + 5 次重试；6×6×6 已收敛到 meV/atom 量级但仍应做 k/ecut 收敛；要 relax 用 WorkflowFactory('abacus.base')，输入塞进 abacus 命名空间；不建议把 stru_settings 传给 builder.settings。

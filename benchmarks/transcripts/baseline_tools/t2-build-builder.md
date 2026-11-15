已完成（未提交任何计算，只做了构建 + 干跑渲染校验）。脚本：/home/liguozhou/abacus/calculations/si_diamond_scf/si_diamond_scf_builder.py

## 代码（可直接跑，默认 LCAO，最后一行才是提交入口，默认不执行）

```python
from aiida import load_profile, orm
from aiida.plugins import CalculationFactory
from ase.build import bulk

load_profile()
AbacusCalculation = CalculationFactory("abacus.abacus")   # entry point 叫 abacus.abacus

DEFAULT_CODE = "abacus_lts@yeesuan"
PSEUDO_FAMILIES = {
    "lcao": "sg15_si_dzp",       # AtomicOrbitalFamily
    "pw":   "SSSP/1.3/PBE/efficiency",
}

def diamond_si(a=5.43):
    return orm.StructureData(ase=bulk("Si", "diamond", a=a, cubic=True))

def scf_parameters(basis="lcao", ecutwfc=60.0):
    return {"input": {"calculation": "scf", "basis_type": basis,
        "ecutwfc": ecutwfc, "scf_thr": 1e-7, "scf_nmax": 100,
        "ks_solver": "genelpa" if basis == "lcao" else "dav",
        "nbands": 24, "smearing_method": "gauss", "smearing_sigma": 0.01}}

def build_scf_builder(code_label=DEFAULT_CODE, basis="lcao", a=5.43,
                      mesh=(8, 8, 8), num_mpiprocs=8, max_wallclock_seconds=3600):
    structure = diamond_si(a=a)
    kpoints = orm.KpointsData()
    kpoints.set_kpoints_mesh(list(mesh))
    builder = AbacusCalculation.get_builder()
    builder.code = orm.load_code(code_label)
    builder.structure = structure
    builder.kpoints = kpoints
    builder.parameters = orm.Dict(scf_parameters(basis))
    family = orm.load_group(PSEUDO_FAMILIES[basis])
    builder.pseudos = family.get_pseudos(structure=structure)
    builder.metadata.options.resources = {"num_machines": 1, "num_mpiprocs_per_machine": num_mpiprocs}
    builder.metadata.options.max_wallclock_seconds = max_wallclock_seconds
    builder.metadata.options.withmpi = True
    return builder
```

## 实测结果（本机 aiida 2.8.0 + aiida-abacus 0.3.3，只构建不提交）

python si_diamond_scf_builder.py --preview：Si8 / 8 原子 / a=b=c=5.430 Å，pseudos {'Si': 323635}；渲染出 INPUT（calculation scf、basis_type lcao、ecutwfc 60.0、scf_thr 1e-07、ks_solver genelpa、nbands 24，插件补 suffix/pseudo_dir/orbital_dir）、KPT（Gamma 8 8 8 0 0 0）、STRU（ATOMIC_SPECIES/Si_ONCV_PBE-1.0.upf、NUMERICAL_ORBITAL Si_gga_7au_100Ry_2s2p1d.orb、LATTICE_CONSTANT 1.889726）。--basis pw 也验证通过。

## 必要说明（关键坑）

1. builder 来源：CalculationFactory('abacus.abacus').get_builder()；code 是普通输入端口。
2. pseudos 必须自己给：命名空间端口，{元素符号: 伪势节点}。PW 只接受 UpfData；LCAO 必须 AtomicOrbitalData。
3. parameters 是两层 dict：{"input": {...}, "stru": {...}}；suffix/pseudo_dir/orbital_dir 不要手写。
4. 基组与求解器配套：PW→dav，LCAO→genelpa。
5. 结构：bulk('Si','diamond',a=5.43,cubic=True) 是 8 原子常规胞；2 原子原胞去掉 cubic=True。
6. 不提交：脚本里没有任何 submit/run；preview_inputs() 用内部 API 校验输入生成。
7. 生产建议换 workchain：WorkflowFactory('abacus.base').get_builder_from_protocol(code=..., structure=..., protocol='balanced', overrides={'pseudo_family': 'sg15_si_dzp', 'abacus': {...}})。注意 pseudo_family 只能经 overrides 传（直接当 kwarg 会被 **_ 吞掉，报 "required pseudo family None is not installed"）。

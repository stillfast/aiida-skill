# aiida-abacus：diamond Si 单点 SCF builder（不提交）

```python
#!/usr/bin/env python
"""Build (but do NOT submit) a single-point SCF calculation for diamond Si
with the aiida-abacus plugin."""

import numpy as np

from aiida import orm, load_profile
from aiida.plugins import CalculationFactory, DataFactory

load_profile()

AbacusCalculation = CalculationFactory("abacus")      # CalcJob
AbacusStruData   = DataFactory("abacus.stru")         # data node that writes STRU
KpointsData      = DataFactory("array.kpoints")

A_SI = 5.43
NN_SI = np.sqrt(3.0) * A_SI / 4.0

def diamond_si_structure(a: float = A_SI) -> orm.StructureData:
    cell = (a / 2.0) * np.array(
        [[0.0, 1.0, 1.0],
         [1.0, 0.0, 1.0],
         [1.0, 1.0, 0.0]]
    )
    structure = orm.StructureData(cell=cell)
    structure.append_atom(position=(0.0, 0.0, 0.0), symbols="Si")
    structure.append_atom(position=(a / 4.0, a / 4.0, a / 4.0), symbols="Si")
    structure.label = f"diamond-Si-a{a:.2f}"
    return structure

def build_diamond_si_scf(code_label: str, pseudo_si, orbital_si=None,
                         basis_type: str = "lcao", ecutwfc: float = 60.0,
                         kmesh=(8, 8, 8), nbands: int = 8):
    structure = diamond_si_structure(A_SI)
    stru = AbacusStruData(structure=structure)
    parameters = orm.Dict(dict={
        "calculation": "scf", "ntype": 1,
        "basis_type": basis_type, "ecutwfc": ecutwfc, "nbands": nbands,
        "scf_thr": 1.0e-8, "scf_nmax": 100,
        "ks_solver": "genelpa" if basis_type == "lcao" else "cg",
        "smearing_method": "gaussian", "smearing_sigma": 0.01,
        "symmetry": 1, "nspin": 1, "dft_functional": "pbe",
    })
    kpoints = KpointsData()
    kpoints.set_kpoints_mesh(list(kmesh), offset=[0.0, 0.0, 0.0])

    builder = AbacusCalculation.get_builder()
    builder.code       = orm.load_code(code_label)
    builder.structure  = stru
    builder.parameters = parameters
    builder.kpoints    = kpoints
    builder.pseudos = {"Si": pseudo_si}
    if basis_type == "lcao":
        builder.orbitals = {"Si": orbital_si}
    builder.metadata.label = "diamond_Si_scf"
    builder.metadata.options.resources = {"num_machines": 1, "num_mpiprocs_per_machine": 8}
    builder.metadata.options.withmpi = True
    builder.metadata.options.max_wallclock_seconds = 3600
    return builder

if __name__ == "__main__":
    pseudo  = orm.load_node(0)   # <-- replace with the real pk
    orbital = orm.load_node(0)   # <-- replace with the real pk
    builder = build_diamond_si_scf("abacus@localhost", pseudo, orbital)
    print(builder)
```

## 必要说明

1. **结构**：diamond Si 用 2 原子原胞（FCC 原胞 + 双原子基元）。
2. **单点 SCF**：`calculation=scf`。
3. **基组选择**：`basis_type="lcao"` 需要 `.orb` 并 `ks_solver=genelpa`；只赝势则 `basis_type="pw"`。
4. **关键参数**：Si 4e/atom，`nbands=8`；`ecutwfc=60 Ry`；`scf_thr=1e-8`；`symmetry=1`；`dft_functional` 与赝势一致。
5. **k 点**：Γ 中心 `8×8×8`。
6. **单位**：StructureData 用 Å，插件负责 Å→Bohr。
7. **伪势/轨道**：`builder.pseudos = {"Si": <UpfData>}`、`builder.orbitals = {"Si": <OrbitalData>}`；"部分版本可能要求 orm.Dict 传 UUID"。
8. **不提交**：没有 submit/run。
9. **版本差异提示**：`AbacusStruData` 构造关键字可能不同；`builder.kpoints` 若不支持用 parameters；"计算器入口点通常是 `abacus`"。

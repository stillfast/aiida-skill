【VASP 20 结构批量弛豫的组织方案】

结论：用「一个批次目录 + 20 个独立 vasp.relax WorkChain + AiiDA Group 打标」组织。本机已铺好：aiida-vasp 5.1.0（vasp.relax = VaspRelaxWorkChain）和 aiida-uranium-workflow 0.2.0（input_builders/relax/vasp.py 已把 VASP relax 接进 JSON 驱动），20 个结构在 AiiDA 侧只是 input.json 里 20 个 structure 引用。

一、三种组织方式
A 手写 for + submit()（~80 行）；B aiida-uranium run（推荐，只写 input.json）；C 自写 BatchRelaxWorkChain（只有需要批次整体退出码才值得）。建议 B 打底 + A 的 collect.py 补 CSV。

二、目录
relax20/parameters/{relax.yml, vasp/scf.yml}、static/{structure.yml, metadata.yml}、runs/relax20/{structures/, 01_ingest.py, input.json, output.json, preview/, reports/, collect.py}

三、流程（每步都做过 dry-run）
1) 入库：POSCAR → StructureData，label="relax20/<名>"，extras 指纹，收进 Group。
2) 写 input.json（preset 名已确认存在：parameters/relax.yml 的 standard、parameters/vasp/scf.yml 的 relax、static/metadata.yml 的 yeesuan_ys_24h）。
3) dry-run：aiida-uranium check -i input.json -o preview —— 实测 2 结构时输出 plan: 1 preset(s) x 1 protocol preset(s) x 2 structure(s) -> 2 WorkChain(s)，每结构一份 YAML。
4) 提交：aiida-uranium run -i input.json（daemon 需在跑）。
5) 监控：aiida-uranium check -i output.json、verdi process list -a、verdi process report <PK>。
6) 汇总：aiida-uranium report -i output.json --method relax + collect.py 出 CSV；archive 归档。

四、脱离 aiida-uranium 的最小 4 文件
RELAX = WorkflowFactory("vasp.v2.relax")；inputs = dict(structure=sd, vasp=dict(code=..., parameters=Dict({"incar": ...}), potential_family=Str(...), potential_mapping=Dict(...), kpoints_spacing=Float(...), calc={"metadata": {"options": cfg["options"]}}), relax_settings=Dict(...), metadata={"label": ...})；node = submit(RELAX, **inputs) 循环 20 次。03_collect.py 用 QueryBuilder 取 outputs.relax.structure、outputs.misc['total_energies']['energy_extrapolated']、exit_status、walltime，写 CSV。

五、批量最容易踩的 8 个点
1. relax_type 决定 ISIF：volume(7)/shape(5)/cell(6) 走 VASP 一维 Brent，金属 E(V) 噪声会 ZBRENT，每步换新作业重放。已有 relax.yml 用 positions_cell(ISIF=3)，别改回 volume。
2. convergence_volume 会被绝对化（volume_convergence × V0）；大超胞批次把 volume_convergence 调到 1e-3 或让 force_cutoff 主导。
3. INCAR 里不能有 nsw/ibrion/isif/ediffg。
4. 调度器选项在 vasp.calc.metadata.options（不是顶层）。
5. 20 次提交 ≠ 20 个并跑：并发 = daemon workers 与队列上限；20×56=1120 核，先确认 d2_ys 吃得下，或用 verdi config set daemon.workers N 限流。
6. 幂等：入库用结构指纹 + extras，提交前查 Group，避免重复烧机时。
7. 可读性：metadata.label = "relax20/<结构名>"。
8. 汇总字段：用 Group 查，不要靠 output.json 手抄；report --method relax 已能出晶格常数/体积/能量。

六、上线检查清单
check -o preview/ 出 20 份 YAML 逐份核对；先跑 1 个 smoke test（exit 0 且最大力 < EDIFFG）；再放 20 个；output.json 全部 exit 0；collect CSV 20 行无离群；archive + reports 存档。

七、没定的三件事
1. 20 个结构来源（散落 POSCAR/CIF 还是已在 AiiDA）；2. 要不要单棵 BatchRelaxWorkChain（默认不用）；3. 队列/核数上限（默认 yeesuan_ys_24h：56 核 / d2_ys / 24 h）。

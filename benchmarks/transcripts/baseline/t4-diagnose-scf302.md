【ABACUS SCF 跑满 50 步不收敛、DRHO 在 0.03–0.45 振荡、CalcJob exit 302 的原因与调参方案】

## 0. 先定性：这不是崩溃，是"电子步没收敛"被 AiiDA 判失败
- ABACUS 每步打印 ITER / ETOT(eV) / EDIFF(eV) / DRHO，收敛判据是 DRHO 降到 scf_thr 以下。
- 跑满上限仍不达标时，ABACUS 打印 `CONVERGENCE HAS NOT BEEN ACHIEVED` 后正常结束。
- aiida-abacus 的 parser 读到该标志，给 CalcJob 设 exit code 302（电子步未收敛）。
- retrieved 完整，可诊断、可续算。"正好 50 步"：scf_nmax 默认 50（PW 默认 100）。

## 1. DRHO 振荡说明什么
正常应收敛为单调指数下降；本例在 0.03 与 0.45 间来回、振幅比初值还大 → 典型 charge sloshing，或两个近简并电子态在跳。0.03 与 1e-6 差 4–5 个量级，不是阈值太严。

## 2. 根因分层
A) 混合参数（最常见）：mixing_type=plain + mixing_beta 偏大；mixing_ndim 太小；nspin=2 时磁混合不匹配。
B) 金属占据：smearing_method=fixed；smearing_sigma 太小；nbands 不够。
C) bcc U 的 5f/磁性：初始磁矩不当，SCF 在不同磁构型间跳。
D) 数值/物理：ecutwfc 太低、赝势不匹配、k 点太稀。
E) 双解竞争（bistability）。

## 3. 调参方案（代价从低到高）
第 0 步：scf_nmax 50 → 150；mixing_type → broyden；mixing_beta → 0.2；mixing_ndim 8 → 16。
第 1 步：kerker + mixing_gg0（1.0–2.0）。
第 2 步：smearing_method=gaussian/mp/fd，smearing_sigma=0.02 Ry，nbands +20–30%。
第 3 步：先 nspin=1 对照；必须 nspin=2 时降 mixing_beta_mag。
第 4 步：ecutwfc 提高 20–50%；加密 k 点；核对晶格常数；DFT+U 先关。
第 5 步：init_chg=file 续算；clean_workdir=False；先松后紧。
第 6 步：给 AbacusBaseWorkChain 的 302 挂 handler（beta×0.5、切 broyden、加 scf_nmax）。

## 4. 诊断清单
1) 数 DRHO 周期；2) ETOT 是否同步振；3) 费米能/占据数是否跳变；4) 每步耗时；5) nspin=1 对照；6) ecut/k 敏感性。

## 5. 结论
50 步打满 + DRHO 大幅振荡 = 电荷密度混合过冲导致的 SCF 极限环。exit 302 只是 AiiDA 对"未收敛"的标记，作业本身跑完、可续算。首选处方：scf_nmax=150 + broyden + mixing_beta=0.2 + mixing_ndim=16。

（注：ABACUS 与 aiida-abacus 的具体默认值和 exit code 编号随版本略有差异；302 的语义以 verdi process show 的 exit message 为准。）

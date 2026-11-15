## 结论
不是崩溃，也不是赝势/轨道/ecut 的问题。CalcJob exit 302 是 aiida-abacus 解析器把 ABACUS 结尾的 "!! CONVERGENCE HAS NOT BEEN ACHIEVED !!" 映射成 ERROR_ELECTRONIC_NOT_CONVERGED。根因是：默认 Broyden 混合（β=0.8、ndim=8、gg0=1.0）在这个 63 原子 U 空位胞上过冲，DRHO 在 0.028–0.484 之间来回摆，scf_nmax=50 用尽时仍在发散。只加步数没用，必须动混合参数。

## 1. 这条作业的实况（已从 AiiDA 库核对）
- pk 574597（AbacusBaseWorkChain 574519，父 workflow 574493，label defects_defect_diag4-2-2），ABACUS v3.10.0。
- 63 个 U，LCAO 4s2p2d2f1g-12au，ecutwfc 125 Ry，36 k-points，nspin=1，smearing mp 0.015 Ry，scf_thr 1e-7，scf_nmax=50。
- mixing 一个都没显式给：INPUT 里是默认 broyden / mixing_beta 0.8 / mixing_ndim 8 / mixing_gg0 1.0 / gg0_min 0.1。
- DRHO：GE1 0.1675 → GE4 0.4843 → GE11 0.0284 → GE12 0.2402 → GE22 0.2166 → GE30 0.1330 → GE37 0.3463 → GE44 0.4371 → GE50 0.2762。EDIFF 在 GE2 +1760 eV、GE44 +375 eV、GE45 −356 eV 间跳。
- 同批 host_diag4-2-2（64 原子，pk 574515）用同一套默认参数 23 步就收敛；所以是空位胞的缺陷态让默认混合器失稳。

## 2. 为什么会摆（charge sloshing + Broyden 过冲）
1. β=0.8 对金属大胞偏大；2. ndim=8 太短；3. Kerker 只压 q>q0，β_eff(q→0)=gg0_min；4. scf_nmax=50 只是把失败截断在 67 min。

## 3. 调参方案
A. 首选（同项目 U63 已验证，pk 574455 用这套 40 步到 6.6e-7）：
mixing_type broyden / mixing_beta 0.5 / mixing_ndim 24 / mixing_gg0 1.5 / mixing_gg0_min 0.1 / scf_nmax 150 / scf_thr 1e-7；可选 scf_os_stop 1 + scf_os_ndim 8。
B. 若仍摆：β 0.4、ndim 32、gg0 2.0；mixing_restart 3e-2；pulay；两段式 1e-5 → init_chg file；有同缺陷胞已收敛 CHG 用 restart_folder。
C. 不要做：只把 scf_nmax 加到 150；mixing_beta ≤0.1（静默关掉 Kerker）；gg0=3；smearing_sigma 0.03；依赖 BaseWorkChain 的 302 handler（max_iterations=0 时直接 401）。
D. 工作流层：在对应 cell 的 scf overrides 里加 mixing 键；defects 的 max_iterations 从 0 提到 ≥3；host 腿 23 步就收敛，可只对 defect 腿加。
E. 物理上：nspin=1 的 U 空位，若非磁解不是基态，再试 nspin=2 + 初始磁矩。

## 4. 验收
DRHO 包络单调下降（允许小反弹）最终 <1e-7；相邻两步能量差 <1 meV/atom；与 1e-6 的结果差 <1 meV/atom（确认不是收敛到错态）。

一句话：50 步不是"差一点"，而是默认 Broyden 在缺陷胞上过冲；把 mixing_beta 0.5 + mixing_ndim 24 + mixing_gg0 1.5 + scf_nmax 150 写进 parameters 即可。

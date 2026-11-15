【ABACUS SCF 50 步不收敛 / CalcJob 302 诊断，已在库中复现】

复现对象：AiiDA pk 574597（2026-11-15 16:12，1h07m，abacus_lts / ABACUS v3.10.0），结构 U63 缺陷胞（defects_defect_diag4-2-2，5×5×6 MP mesh，LCAO，ecutwfc 125 Ry，NBANDS 530）。参数：nspin=1，mp smearing σ=0.015 Ry，scf_thr=1e-7，scf_nmax=50，mixing 全部默认（broyden / beta 0.8 / ndim 8 / gg0 1.0 / gg0_min 0.1）。父 WorkChain 574519 以 max_iterations=0 提交，302 之后无重试预算 → 直接 401。

一、302 是什么
parser 在 OUT.aiida/abacus_output 读到 "!! CONVERGENCE HAS NOT BEEN ACHIEVED !!" 就返回 302 ERROR_ELECTRONIC_NOT_CONVERGED。不是崩溃，是 SCF 在 50 步内没把 DRHO 压到 scf_thr。

二、DRHO 是极限环，不是"收敛慢"
GE1 0.167 → GE2 0.325 → GE3 0.438 → GE4 0.484；GE11 最低 0.028，随后 GE12 0.240、GE22 0.217、GE37 0.346、GE44 0.437 —— 每 8–10 步爆一次，包络不衰减。同步 ETOT 单步跳几百 eV（GE44 跳 375 eV），E_Fermi 在 1.55–1.85 Ry 摆动。典型 charge sloshing。

三、原因
1) β=0.8 对金属太大：χ(q→0) 发散，Kerker 只压 |q|>gg0_min=0.1 的分量；
2) ndim=8 历史太短；
3) 体系难：63 原子低对称金属缺陷胞 + LCAO + U 5f，σ=0.015 Ry 偏小；
4) nspin=1：U 缺陷胞很可能有局域磁矩；
5) scf_thr=1e-7 比默认 1e-6 严 10 倍。

四、调参阶梯（一次只动一档）
第1档：mixing_beta 0.2 / mixing_ndim 16 / scf_nmax 100
第2档：mixing_gg0 1.5、mixing_gg0_min 0.05、β 0.15、ndim 20
第3档：mixing_type plain + mixing_beta 0.05（β≤0.1 时 Kerker 自动关闭）
第4档：nspin=2 + 初始磁矩（显式给 mixing_beta_mag）；σ→0.02；DFT+U 则 mixing_dmr 1 + mixing_restart 1e-3
第5档：scf_thr 放宽到 1e-5~1e-6 跑通再收紧；U–U 仅 2.718 Å，若未弛豫应先松判据弛豫

五、AiiDA 侧
max_iterations 设 4–5，让 BaseWorkChain 阶梯自动跑，否则每次手工重投；50 步 × 80 s = 67 min 全浪费，可开 scf_stop_os 1 + scf_stop_ndim 提前止损。

六、验收
DRHO 包络单调下降=方向对；单调但慢=只加 scf_nmax；ETOT 只抖 ~1e-3 eV 而 DRHO 卡 1e-5=放宽 scf_thr；磁矩跳=走第 4 档。

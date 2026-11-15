---
generated: true
generated_by: troubleshooting/regen_exit_codes.py
---

# Exit code 速查

> 本文件的「代码 / 名称 / 消息」列由 `regen_exit_codes.py` 从已安装插件源码生成，
> 「典型原因 / 处置」列来自人工维护的 `exit-codes.notes.yaml`。
> 升级插件后运行 `python troubleshooting/regen_exit_codes.py` 重新生成。

排查顺序：先 `verdi process show <pk>` 看是哪一层（CalcJob 还是 WorkChain）的 exit code，
再回到本表；**同一个数字在不同插件里含义不同**（例如 700 在 VASP CalcJob 与 VASP WorkChain 里不一样）。


## ABACUS CalcJob

| code | name | message | 典型原因 / 处置 |
| --- | --- | --- | --- |
| 1 | `ERROR_UNSPECIFIED` | The process has failed with an unspecified error. | — |
| 2 | `ERROR_LEGACY_FAILURE` | The process failed with legacy failure mode. | — |
| 10 | `ERROR_INVALID_OUTPUT` | The process returned an invalid output. | — |
| 11 | `ERROR_MISSING_OUTPUT` | The process did not register a required output. | — |
| 100 | `ERROR_NO_RETRIEVED_FOLDER` | The process did not have the required `retrieved` output. | — |
| 110 | `ERROR_SCHEDULER_OUT_OF_MEMORY` | The job ran out of memory. | — |
| 120 | `ERROR_SCHEDULER_OUT_OF_WALLTIME` | The job ran out of walltime. | — |
| 131 | `ERROR_SCHEDULER_INVALID_ACCOUNT` | The specified account is invalid. | — |
| 140 | `ERROR_SCHEDULER_NODE_FAILURE` | The node running the job failed. | — |
| 150 | `STOPPED_BY_MONITOR` | {message} | — |
| 160 | `ERROR_STASHING_FAILED` | {message} | — |
| 300 | `ERROR_MISSING_OUTPUT_FILES` | Calculation did not produce all expected output files. | 缺输出文件；看 retrieved 里少了哪个文件，通常是作业在写结果前就死了 |
| 301 | `ERROR_CALCULATION_INCOMPLETE` | Calculation did not complete successfully - 'Total Time' not found at end of running log. | 'Total Time' 缺失 = 作业没跑完就被杀（墙钟、OOM、MPI/UCX 超时）；先看 _scheduler-stderr.txt 与 sacct；调大 max_wallclock_seconds、降并行度或改混合参数 |
| 302 | `ERROR_ELECTRONIC_NOT_CONVERGED` | SCF did not reach self-consistency. | SCF 未收敛（跑满 scf_nmax）；看 running_scf.log 的 DRHO 列；金属/5f 体系用 broyden + mixing_beta 0.2 + mixing_ndim 20~24 + mixing_gg0 1.5 |
| 303 | `ERROR_IONIC_NOT_CONVERGED` | Ionic relaxation did not converge within the maximum number of steps. | 离子步未收敛（跑满 relax_nmax）；调大 max_ionic_steps；或让 WorkChain 从最新结构续算 |
| 410 | `ERROR_SCF_NOT_CONVERGED` | SCF calculation did not converge within the specified electronic minimization steps. | SCF 未在限定步数内收敛；同 302 |
| 501 | `ERROR_IONIC_CONVERGED_BUT_SCF_FAILED` | Ionic minimization converged but final SCF calculation did not converge. | 离子步收敛但最后一步 SCF 未收敛；收紧 scf_thr 或改用更稳的混合；检查弛豫末步的电子步 |

## ABACUS base WorkChain

| code | name | message | 典型原因 / 处置 |
| --- | --- | --- | --- |
| 1 | `ERROR_UNSPECIFIED` | The process has failed with an unspecified error. | — |
| 2 | `ERROR_LEGACY_FAILURE` | The process failed with legacy failure mode. | — |
| 10 | `ERROR_INVALID_OUTPUT` | The process returned an invalid output. | — |
| 11 | `ERROR_MISSING_OUTPUT` | The process did not register a required output. | — |
| 201 | `ERROR_INVALID_INPUT_PSEUDO_POTENTIALS` | The explicit `pseudos` or `pseudo_family` could not be used to get the necessary pseudos. | 未指定 `abacus.structure`；补结构输入 |
| 202 | `ERROR_INVALID_INPUT_KPOINTS` | Neither the `kpoints` nor the `kpoints_distance` input was specified. | 既没有 kpoints 也没有 kpoints_distance；给其中任意一个（常用 kpoints_distance，单位 1/Å） |
| 203 | `ERROR_INVALID_INPUT_RESOURCES` | Neither the `options` nor `automatic_parallelization` input was specified. This exit status has been deprecated as the check it corresponded to was incorrect. | — |
| 204 | `ERROR_INVALID_INPUT_RESOURCES_UNDERSPECIFIED` | The `metadata.options` did not specify both `resources.num_machines` and `max_wallclock_seconds`. This exit status has been deprecated as the check it corresponded to was incorrect. | — |
| 300 | `ERROR_UNRECOVERABLE_FAILURE` | The calculation failed with an unidentified unrecoverable error. | 子作业失败且未能自动处理；往上翻日志看真正的子作业 exit code |
| 301 | `ERROR_SUB_PROCESS_EXCEPTED` | The sub process excepted. | — |
| 302 | `ERROR_SUB_PROCESS_KILLED` | The sub process was killed. | — |
| 310 | `ERROR_KNOWN_UNRECOVERABLE_FAILURE` | The calculation failed with a known unrecoverable error. | 已知的不可恢复错误；看 report 里的 handler 消息 |
| 320 | `ERROR_INITIALIZATION_CALCULATION_FAILED` | The initialization calculation failed. | — |
| 401 | `ERROR_MAXIMUM_ITERATIONS_EXCEEDED` | The maximum number of iterations was exceeded. | — |
| 402 | `ERROR_UNHANDLED_FAILURE` | The process failed with an unhandled failure. | — |
| 501 | `ERROR_IONIC_CONVERGENCE_REACHED_EXCEPT_IN_FINAL_SCF` | Then ionic minimization cycle converged but the thresholds are exceeded in the final SCF. | 离子收敛但 final SCF 超阈值；同 CalcJob 501 |
| 710 | `WARNING_ELECTRONIC_CONVERGENCE_NOT_REACHED` | The electronic minimization cycle did not reach self-consistency, but `scf_must_converge` is `False` and/or `electron_maxstep` is 0. | 电子步未收敛但 `scf_must_converge=False`（仅警告）；确认是否接受未收敛的能量 |

## ABACUS relax WorkChain

| code | name | message | 典型原因 / 处置 |
| --- | --- | --- | --- |
| 1 | `ERROR_UNSPECIFIED` | The process has failed with an unspecified error. | — |
| 2 | `ERROR_LEGACY_FAILURE` | The process failed with legacy failure mode. | — |
| 10 | `ERROR_INVALID_OUTPUT` | The process returned an invalid output. | — |
| 11 | `ERROR_MISSING_OUTPUT` | The process did not register a required output. | — |
| 401 | `ERROR_SUB_PROCESS_FAILED_RELAX` | the relax AbacusBaseWorkChain sub process failed | relax 子流程失败；看子 base WorkChain 的 exit code |
| 402 | `ERROR_SUB_PROCESS_FAILED_FINAL_SCF` | the final scf AbacusBaseWorkChain sub process failed | final SCF 子流程失败；通常是 final SCF 的 SCF 不收敛 / 被墙钟杀 |

## ABACUS band WorkChain

| code | name | message | 典型原因 / 处置 |
| --- | --- | --- | --- |
| 1 | `ERROR_UNSPECIFIED` | The process has failed with an unspecified error. | — |
| 2 | `ERROR_LEGACY_FAILURE` | The process failed with legacy failure mode. | — |
| 10 | `ERROR_INVALID_OUTPUT` | The process returned an invalid output. | — |
| 11 | `ERROR_MISSING_OUTPUT` | The process did not register a required output. | — |
| 601 | `ERROR_SUB_PROC_BANDS_FAILED` | The band structure calculation failed. | bands 子流程失败；看 bands CalcJob 的 exit code 与检索文件 |
| 602 | `ERROR_SUB_PROC_DOS_FAILED` | The density of states calculation failed. | DOS 子流程失败；同 601 |
| 603 | `ERROR_SCF_PROCESS_FAILED` | The SCF calculation failed. | SCF 失败；同 601 |
| 604 | `ERROR_RELAX_PROCESS_FAILED` | The relaxation calculation failed. | relax 失败；同 601 |

## VASP CalcJob

| code | name | message | 典型原因 / 处置 |
| --- | --- | --- | --- |
| 0 | `NO_ERROR` | the sun is shining | — |
| 1 | `ERROR_UNSPECIFIED` | The process has failed with an unspecified error. | — |
| 2 | `ERROR_LEGACY_FAILURE` | The process failed with legacy failure mode. | — |
| 10 | `ERROR_INVALID_OUTPUT` | The process returned an invalid output. | — |
| 11 | `ERROR_MISSING_OUTPUT` | The process did not register a required output. | — |
| 110 | `ERROR_SCHEDULER_OUT_OF_MEMORY` | The job ran out of memory. | — |
| 120 | `ERROR_SCHEDULER_OUT_OF_WALLTIME` | The job ran out of walltime. | — |
| 131 | `ERROR_SCHEDULER_INVALID_ACCOUNT` | The specified account is invalid. | — |
| 140 | `ERROR_SCHEDULER_NODE_FAILURE` | The node running the job failed. | — |
| 150 | `STOPPED_BY_MONITOR` | {message} | — |
| 160 | `ERROR_STASHING_FAILED` | {message} | — |
| 333 | `ERROR_VASP_DID_NOT_EXECUTE` | VASP did not produce any output and did likely not execute properly. | VASP 没真正执行（无任何输出）；检查 code 路径、prepend-text 的 module/spack、`srun` 与 MPI |
| 350 | `ERROR_NO_RETRIEVED_FOLDER` | the retrieved folder data node could not be accessed. | 取回文件夹缺失；看 scheduler 日志；通常是作业被杀或 retrieve 列表配置错误 |
| 351 | `ERROR_NO_RETRIEVED_TEMPORARY_FOLDER` | the retrieved_temporary folder data node could not be accessed. | — |
| 352 | `ERROR_CRITICAL_MISSING_OBJECT` | an object that is marked by the parser as critical is missing. | — |
| 700 | `ERROR_DID_NOT_FINISH` | Calculation did not reach the end of execution. | 计算没有跑到结束（ZBRENT、电子步失败、被杀）；看 OUTCAR 末尾与 vasp.out；ISIF=5/6/7 的 Brent 在噪声 E(V) 上容易失败，改用 ISIF=3 |
| 701 | `ERROR_ELECTRONIC_NOT_CONVERGED` | The electronic structure is not converged. | 电子结构未收敛；调 NELM/ALGO/混合；金属用 ISMEAR=1/-5 |
| 702 | `ERROR_IONIC_NOT_CONVERGED` | The ionic relaxation is not converged. | 离子弛豫未收敛；调大 NSW，或检查力判据 EDIFFG |
| 703 | `ERROR_VASP_CRITICAL_ERROR` | VASP calculation encountered a critical error: {error_message}. | VASP 报出 critical error；按 message 查 VASP 文档（常见：NaN、ZBRENT、内存不足） |
| 704 | `ERROR_DIAGNOSIS_OUTPUTS_MISSING` | Outputs for diagnosis are missing, please make sure `run_status` and `notifications` quantities are requested for parsing. | 诊断输出缺失（未解析 run_status/notifications）；在 parser_settings 里打开相应输出 |
| 1002 | `ERROR_NOT_ABLE_TO_PARSE_QUANTITY` | the parser is not able to parse the {quantity} quantity which is marked as required | — |
| 1004 | `ERROR_NOT_ABLE_TO_CREATE_NODE` | the parser is not able to compose one or more output nodes: {nodes} | — |
| 1005 | `ERROR_OVERFLOW_IN_XML` | Overflow detected in XML while parsing. | — |

## VASP v2 WorkChain

| code | name | message | 典型原因 / 处置 |
| --- | --- | --- | --- |
| 0 | `NO_ERROR` | the sun is shining | — |
| 1 | `ERROR_UNSPECIFIED` | The process has failed with an unspecified error. | — |
| 2 | `ERROR_LEGACY_FAILURE` | The process failed with legacy failure mode. | — |
| 10 | `ERROR_INVALID_OUTPUT` | The process returned an invalid output. | — |
| 11 | `ERROR_MISSING_OUTPUT` | The process did not register a required output. | — |
| 300 | `ERROR_MISSING_REQUIRED_OUTPUT` | the calculation is missing at least one required output in the restart workchain | restart 循环里缺必需输出；看子 CalcJob 的状态与 parser_settings |
| 301 | `ERROR_SUB_PROCESS_EXCEPTED` | The sub process excepted. | — |
| 302 | `ERROR_SUB_PROCESS_KILLED` | The sub process was killed. | — |
| 400 | `ERROR_ITERATION_RETURNED_NO_CALCULATION` | the run_calculation step did not successfully add a calculation node to the context | — |
| 401 | `ERROR_MAXIMUM_ITERATIONS_EXCEEDED` | the maximum number of iterations was exceeded | 超过最大迭代次数（重试耗尽）；看 report 里最后一次失败原因；必要时提高 max_iterations |
| 402 | `ERROR_UNHANDLED_FAILURE` | The process failed with an unhandled failure. | — |
| 402 | `ERROR_UNEXPECTED_CALCULATION_STATE` | the calculation finished with an unexpected calculation state | — |
| 403 | `ERROR_UNEXPECTED_CALCULATION_FAILURE` | the calculation experienced and unexpected failure | — |
| 404 | `ERROR_SECOND_CONSECUTIVE_SUBMISSION_FAILURE` | the calculation failed to submit, twice in a row | 连续两次提交失败；几乎总是配置问题（分区、code、ssh），先 `verdi computer test` |
| 405 | `ERROR_SECOND_CONSECUTIVE_UNHANDLED_FAILURE` | the calculation failed for an unknown reason, twice in a row | — |
| 500 | `ERROR_MISSING_CRITICAL_OUTPUT` | Missing critical output for inspecting the status of the calculation. | 缺关键输出，无法判断状态；检查 retrieve 列表 |
| 501 | `ERROR_OTHER_INTERVENTION_NEEDED` | Cannot handle the error - inputs are likely need to be revised manually. Message: {message} | 需要人工改输入；按 message 调整 INCAR/POSCAR |
| 502 | `ERROR_CALCULATION_NOT_FINISHED` | Cannot handle the error - the last calculation did not reach the end of execution. | 上一次计算没有跑到结束；同 CalcJob 700 |
| 503 | `ERROR_ELECTRONIC_STRUCTURE_NOT_CONVERGED` | Cannot handle the error - the last calculation did not reach electronic convergence. | 电子结构未收敛；同 CalcJob 701 |
| 504 | `ERROR_IONIC_RELAXATION_NOT_CONVERGED` | The ionic relaxation is not converged. | 离子弛豫未收敛；调大 NSW 或放宽 EDIFFG |
| 505 | `ERROR_UNCONVERGED_ELECTRONIC_STRUCTURE_IN_RELAX` | At least one of the ionic steps during the relaxation has did not have converged electronic structure. | 弛豫过程中某一步电子步未收敛；先解决电子步收敛，再谈离子步 |
| 700 | `ERROR_NO_POTENTIAL_FAMILY_NAME` | the user did not supply a potential family name | 没给 potential_family；补 `potential_family` 输入 |
| 701 | `ERROR_POTENTIAL_VALUE_ERROR` | ValueError was returned from get_potcars_from_structure | — |
| 702 | `ERROR_POTENTIAL_DO_NOT_EXIST` | the potential does not exist | 赝势不存在；检查 `potential_mapping` 与已安装家族 |
| 703 | `ERROR_IN_PARAMETER_MASSAGER` | the exception: {exception} was thrown while massaging the parameters | — |

## VASP v2 relax WorkChain

| code | name | message | 典型原因 / 处置 |
| --- | --- | --- | --- |
| 0 | `NO_ERROR` | the sun is shining | — |
| 1 | `ERROR_UNSPECIFIED` | The process has failed with an unspecified error. | — |
| 2 | `ERROR_LEGACY_FAILURE` | The process failed with legacy failure mode. | — |
| 10 | `ERROR_INVALID_OUTPUT` | The process returned an invalid output. | — |
| 11 | `ERROR_MISSING_OUTPUT` | The process did not register a required output. | — |
| 300 | `ERROR_MISSING_REQUIRED_OUTPUT` | the called workchain does not contain the necessary relaxed output structure | — |
| 420 | `ERROR_NO_CALLED_WORKCHAIN` | no called workchain detected | — |
| 500 | `ERROR_UNKNOWN` | unknown error detected in the relax workchain | — |
| 502 | `ERROR_OVERRIDE_PARAMETERS` | there was an error overriding the parameters | — |
| 600 | `ERROR_RELAX_NOT_CONVERGED` | Ionic relaxation was not converged after the maximum number of iterations has been spent | 弛豫在最大迭代次数内未收敛；调大 max_iterations / NSW；或换更稳的 ISIF |
| 601 | `ERROR_FINAL_SCF_HAS_RESIDUAL_FORCE` | The final singlepoint calculation has increased residual forces. This may be caused by electronic solver converging to a different solution. Care should be taken to investigate the results. | 最终单点残余力上升（可能收敛到不同电子解）；属于警告：检查最终结构/能量是否可用，必要时重跑单点 |

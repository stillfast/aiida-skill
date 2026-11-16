---
generated: true
generated_by: troubleshooting/regen_exit_codes.py
---

# Exit-code reference

> The "code / name / message" columns are generated from the installed plugin
> sources; the "typical cause / fix" column comes from the hand-written
> `exit-codes.notes.yaml`. Re-run `python troubleshooting/regen_exit_codes.py`
> after upgrading a plugin.

Read the exit code together with `verdi process show <pk>`: the same number means
different things in different plugins (e.g. 700 in the VASP CalcJob vs the VASP
WorkChain), and a WorkChain exit code usually just points at a failed child.


## ABACUS CalcJob

| code | name | message | typical cause / fix |
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
| 300 | `ERROR_MISSING_OUTPUT_FILES` | Calculation did not produce all expected output files. | missing output files；check which file is absent from retrieved; usually the job died before writing results |
| 301 | `ERROR_CALCULATION_INCOMPLETE` | Calculation did not complete successfully - 'Total Time' not found at end of running log. | 'Total Time' missing = the job did not finish (wall clock, OOM, MPI/UCX failure)；read _scheduler-stderr.txt and sacct; raise max_wallclock_seconds, lower the process count, or fix the mixing |
| 302 | `ERROR_ELECTRONIC_NOT_CONVERGED` | SCF did not reach self-consistency. | SCF did not converge within scf_nmax；look at the DRHO column; for metals / 5f systems use broyden + mixing_beta 0.2 + mixing_ndim 20-24 + mixing_gg0 1.5 |
| 303 | `ERROR_IONIC_NOT_CONVERGED` | Ionic relaxation did not converge within the maximum number of steps. | ionic relaxation ran out of steps；raise max_ionic_steps, or let the WorkChain restart from the latest structure |
| 410 | `ERROR_SCF_NOT_CONVERGED` | SCF calculation did not converge within the specified electronic minimization steps. | SCF did not converge within the allowed number of steps；same as 302 |
| 501 | `ERROR_IONIC_CONVERGED_BUT_SCF_FAILED` | Ionic minimization converged but final SCF calculation did not converge. | ionic loop converged but the final SCF did not；tighten the mixing or the final SCF settings; inspect the last electronic loop |

## ABACUS base WorkChain

| code | name | message | typical cause / fix |
| --- | --- | --- | --- |
| 1 | `ERROR_UNSPECIFIED` | The process has failed with an unspecified error. | — |
| 2 | `ERROR_LEGACY_FAILURE` | The process failed with legacy failure mode. | — |
| 10 | `ERROR_INVALID_OUTPUT` | The process returned an invalid output. | — |
| 11 | `ERROR_MISSING_OUTPUT` | The process did not register a required output. | — |
| 201 | `ERROR_INVALID_INPUT_PSEUDO_POTENTIALS` | The explicit `pseudos` or `pseudo_family` could not be used to get the necessary pseudos. | no `abacus.structure` input；provide the structure |
| 202 | `ERROR_INVALID_INPUT_KPOINTS` | Neither the `kpoints` nor the `kpoints_distance` input was specified. | neither kpoints nor kpoints_distance given；provide one of them (kpoints_distance is in 1/Angstrom) |
| 203 | `ERROR_INVALID_INPUT_RESOURCES` | Neither the `options` nor `automatic_parallelization` input was specified. This exit status has been deprecated as the check it corresponded to was incorrect. | — |
| 204 | `ERROR_INVALID_INPUT_RESOURCES_UNDERSPECIFIED` | The `metadata.options` did not specify both `resources.num_machines` and `max_wallclock_seconds`. This exit status has been deprecated as the check it corresponded to was incorrect. | — |
| 300 | `ERROR_UNRECOVERABLE_FAILURE` | The calculation failed with an unidentified unrecoverable error. | child calculation failed and no handler recovered；look further down the log for the real child exit code |
| 301 | `ERROR_SUB_PROCESS_EXCEPTED` | The sub process excepted. | — |
| 302 | `ERROR_SUB_PROCESS_KILLED` | The sub process was killed. | — |
| 310 | `ERROR_KNOWN_UNRECOVERABLE_FAILURE` | The calculation failed with a known unrecoverable error. | known unrecoverable error；read the handler message in `verdi process report` |
| 320 | `ERROR_INITIALIZATION_CALCULATION_FAILED` | The initialization calculation failed. | — |
| 401 | `ERROR_MAXIMUM_ITERATIONS_EXCEEDED` | The maximum number of iterations was exceeded. | — |
| 402 | `ERROR_UNHANDLED_FAILURE` | The process failed with an unhandled failure. | — |
| 501 | `ERROR_IONIC_CONVERGENCE_REACHED_EXCEPT_IN_FINAL_SCF` | Then ionic minimization cycle converged but the thresholds are exceeded in the final SCF. | ionic convergence reached but the final SCF exceeded thresholds；same as CalcJob 501 |
| 710 | `WARNING_ELECTRONIC_CONVERGENCE_NOT_REACHED` | The electronic minimization cycle did not reach self-consistency, but `scf_must_converge` is `False` and/or `electron_maxstep` is 0. | electronic loop not converged but `scf_must_converge=False` (warning only)；decide whether an unconverged energy is acceptable |

## ABACUS relax WorkChain

| code | name | message | typical cause / fix |
| --- | --- | --- | --- |
| 1 | `ERROR_UNSPECIFIED` | The process has failed with an unspecified error. | — |
| 2 | `ERROR_LEGACY_FAILURE` | The process failed with legacy failure mode. | — |
| 10 | `ERROR_INVALID_OUTPUT` | The process returned an invalid output. | — |
| 11 | `ERROR_MISSING_OUTPUT` | The process did not register a required output. | — |
| 401 | `ERROR_SUB_PROCESS_FAILED_RELAX` | the relax AbacusBaseWorkChain sub process failed | the relax sub-workflow failed；check the child base WorkChain exit code |
| 402 | `ERROR_SUB_PROCESS_FAILED_FINAL_SCF` | the final scf AbacusBaseWorkChain sub process failed | the final SCF sub-workflow failed；usually SCF non-convergence or a wall-clock kill in the final SCF |

## ABACUS band WorkChain

| code | name | message | typical cause / fix |
| --- | --- | --- | --- |
| 1 | `ERROR_UNSPECIFIED` | The process has failed with an unspecified error. | — |
| 2 | `ERROR_LEGACY_FAILURE` | The process failed with legacy failure mode. | — |
| 10 | `ERROR_INVALID_OUTPUT` | The process returned an invalid output. | — |
| 11 | `ERROR_MISSING_OUTPUT` | The process did not register a required output. | — |
| 601 | `ERROR_SUB_PROC_BANDS_FAILED` | The band structure calculation failed. | the bands sub-workflow failed；check the bands CalcJob exit code and its retrieved files |
| 602 | `ERROR_SUB_PROC_DOS_FAILED` | The density of states calculation failed. | the DOS sub-workflow failed；same as 601 |
| 603 | `ERROR_SCF_PROCESS_FAILED` | The SCF calculation failed. | the SCF failed；same as 601 |
| 604 | `ERROR_RELAX_PROCESS_FAILED` | The relaxation calculation failed. | the relax failed；same as 601 |

## VASP CalcJob

| code | name | message | typical cause / fix |
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
| 333 | `ERROR_VASP_DID_NOT_EXECUTE` | VASP did not produce any output and did likely not execute properly. | VASP produced no output at all (it probably never ran)；check the code path, the module/spack lines in prepend-text, and srun/MPI |
| 350 | `ERROR_NO_RETRIEVED_FOLDER` | the retrieved folder data node could not be accessed. | retrieved folder missing；check the scheduler log; usually the job was killed or the retrieve list is wrong |
| 351 | `ERROR_NO_RETRIEVED_TEMPORARY_FOLDER` | the retrieved_temporary folder data node could not be accessed. | — |
| 352 | `ERROR_CRITICAL_MISSING_OBJECT` | an object that is marked by the parser as critical is missing. | — |
| 700 | `ERROR_DID_NOT_FINISH` | Calculation did not reach the end of execution. | calculation did not reach the end (ZBRENT, electronic failure, killed)；read the end of OUTCAR and vasp.out; ISIF=5/6/7 Brent line search is fragile on noisy E(V) - switch to ISIF=3 |
| 701 | `ERROR_ELECTRONIC_NOT_CONVERGED` | The electronic structure is not converged. | electronic structure not converged；adjust NELM/ALGO/mixing; metals need ISMEAR=1 or -5 |
| 702 | `ERROR_IONIC_NOT_CONVERGED` | The ionic relaxation is not converged. | ionic relaxation not converged；raise NSW or check the force criterion EDIFFG |
| 703 | `ERROR_VASP_CRITICAL_ERROR` | VASP calculation encountered a critical error: {error_message}. | VASP reported a critical error；follow the message (common: NaN, ZBRENT, out of memory) |
| 704 | `ERROR_DIAGNOSIS_OUTPUTS_MISSING` | Outputs for diagnosis are missing, please make sure `run_status` and `notifications` quantities are requested for parsing. | diagnosis outputs missing (run_status / notifications not parsed)；request them in parser_settings |
| 1002 | `ERROR_NOT_ABLE_TO_PARSE_QUANTITY` | the parser is not able to parse the {quantity} quantity which is marked as required | — |
| 1004 | `ERROR_NOT_ABLE_TO_CREATE_NODE` | the parser is not able to compose one or more output nodes: {nodes} | — |
| 1005 | `ERROR_OVERFLOW_IN_XML` | Overflow detected in XML while parsing. | — |

## VASP v2 WorkChain

| code | name | message | typical cause / fix |
| --- | --- | --- | --- |
| 0 | `NO_ERROR` | the sun is shining | — |
| 1 | `ERROR_UNSPECIFIED` | The process has failed with an unspecified error. | — |
| 2 | `ERROR_LEGACY_FAILURE` | The process failed with legacy failure mode. | — |
| 10 | `ERROR_INVALID_OUTPUT` | The process returned an invalid output. | — |
| 11 | `ERROR_MISSING_OUTPUT` | The process did not register a required output. | — |
| 300 | `ERROR_MISSING_REQUIRED_OUTPUT` | the calculation is missing at least one required output in the restart workchain | required output missing inside the restart loop；check the child CalcJob state and parser_settings |
| 301 | `ERROR_SUB_PROCESS_EXCEPTED` | The sub process excepted. | — |
| 302 | `ERROR_SUB_PROCESS_KILLED` | The sub process was killed. | — |
| 400 | `ERROR_ITERATION_RETURNED_NO_CALCULATION` | the run_calculation step did not successfully add a calculation node to the context | — |
| 401 | `ERROR_MAXIMUM_ITERATIONS_EXCEEDED` | the maximum number of iterations was exceeded | maximum number of iterations exceeded (retries exhausted)；read the last failure in the report; raise max_iterations if appropriate |
| 402 | `ERROR_UNHANDLED_FAILURE` | The process failed with an unhandled failure. | — |
| 402 | `ERROR_UNEXPECTED_CALCULATION_STATE` | the calculation finished with an unexpected calculation state | — |
| 403 | `ERROR_UNEXPECTED_CALCULATION_FAILURE` | the calculation experienced and unexpected failure | — |
| 404 | `ERROR_SECOND_CONSECUTIVE_SUBMISSION_FAILURE` | the calculation failed to submit, twice in a row | two consecutive submission failures；almost always configuration (partition, code, ssh); run `verdi computer test` first |
| 405 | `ERROR_SECOND_CONSECUTIVE_UNHANDLED_FAILURE` | the calculation failed for an unknown reason, twice in a row | — |
| 500 | `ERROR_MISSING_CRITICAL_OUTPUT` | Missing critical output for inspecting the status of the calculation. | critical output missing, state cannot be judged；check the retrieve list |
| 501 | `ERROR_OTHER_INTERVENTION_NEEDED` | Cannot handle the error - inputs are likely need to be revised manually. Message: {message} | manual input change needed；adjust INCAR/POSCAR as the message says |
| 502 | `ERROR_CALCULATION_NOT_FINISHED` | Cannot handle the error - the last calculation did not reach the end of execution. | the last calculation did not reach the end；same as CalcJob 700 |
| 503 | `ERROR_ELECTRONIC_STRUCTURE_NOT_CONVERGED` | Cannot handle the error - the last calculation did not reach electronic convergence. | electronic structure not converged；same as CalcJob 701 |
| 504 | `ERROR_IONIC_RELAXATION_NOT_CONVERGED` | The ionic relaxation is not converged. | ionic relaxation not converged；raise NSW or loosen EDIFFG |
| 505 | `ERROR_UNCONVERGED_ELECTRONIC_STRUCTURE_IN_RELAX` | At least one of the ionic steps during the relaxation has did not have converged electronic structure. | at least one electronic step during the relaxation did not converge；fix electronic convergence before worrying about the ions |
| 700 | `ERROR_NO_POTENTIAL_FAMILY_NAME` | the user did not supply a potential family name | no potential_family given；supply `potential_family` |
| 701 | `ERROR_POTENTIAL_VALUE_ERROR` | ValueError was returned from get_potcars_from_structure | — |
| 702 | `ERROR_POTENTIAL_DO_NOT_EXIST` | the potential does not exist | potential does not exist；check `potential_mapping` against the installed families |
| 703 | `ERROR_IN_PARAMETER_MASSAGER` | the exception: {exception} was thrown while massaging the parameters | — |

## VASP v2 relax WorkChain

| code | name | message | typical cause / fix |
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
| 600 | `ERROR_RELAX_NOT_CONVERGED` | Ionic relaxation was not converged after the maximum number of iterations has been spent | relaxation did not converge within max_iterations；raise max_iterations / NSW, or use a more robust ISIF |
| 601 | `ERROR_FINAL_SCF_HAS_RESIDUAL_FORCE` | The final singlepoint calculation has increased residual forces. This may be caused by electronic solver converging to a different solution. Care should be taken to investigate the results. | final single point has increased residual forces (may have converged to a different electronic solution)；warning only: check the final structure/energy, rerun the single point if needed |

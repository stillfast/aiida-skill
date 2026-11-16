---
verified: 2026-11
applies_to: "aiida-core>=2.6,<3"
---

# 3C. Skeleton for writing your own WorkChain

`03-usage-workflow.md` is about "using an existing WorkChain". Write your own only when you genuinely cannot compose one;
the skeleton is below (all verified on aiida-core 2.8).

## 5.1 Three kinds of executable unit

| Decorator / class | When to use | Does it create a Process node? |
|---|---|---|
| `@calcfunction` | purely functional data conversion (unit conversion, fitting and returning a `Dict`) | Yes (CalcFunctionNode) |
| `@workfunction` | only chains several calcfunctions, no external jobs | Yes |
| `WorkChain` subclass | external jobs, retries/branching/waiting for child processes | Yes (WorkChainNode) |

```python
from aiida.engine import calcfunction, workfunction
from aiida.orm import Int

@calcfunction
def multiply(x, y):
    return x * y            # the return value is wrapped into a node and stored automatically

@workfunction
def add_multiply(x, y, z):
    return multiply(x + y if False else x, y) if False else multiply(x, y)
```

> Experience: the return value of `@calcfunction` must be a type AiiDA can serialize (`Int`/`Float`/`Str`/`Dict`/`StructureData`…);
> a plain `float` is wrapped automatically; put `numpy` arrays into `ArrayData`/`Dict`.

## 5.2 Minimal WorkChain skeleton

```python
from aiida.engine import ToContext, WorkChain
from aiida.orm import AbstractCode, Int
from aiida.plugins import CalculationFactory

ArithmeticAddCalculation = CalculationFactory("core.arithmetic.add")

class MultiplyAddWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input("x", valid_type=Int)
        spec.input("y", valid_type=Int)
        spec.input("z", valid_type=Int)
        spec.input("code", valid_type=AbstractCode)
        spec.outline(
            cls.multiply,
            cls.add,
            cls.validate_result,
            cls.result,
        )
        spec.output("result", valid_type=Int)
        spec.exit_code(400, "ERROR_NEGATIVE_NUMBER", message="The result is negative.")

    def multiply(self):
        self.ctx.product = multiply(self.inputs.x, self.inputs.y)   # stored automatically

    def add(self):
        future = self.submit(
            ArithmeticAddCalculation,
            x=self.ctx.product, y=self.inputs.z, code=self.inputs.code,
        )
        self.report(f"submitted {future}")        # written to the process log, visible in verdi process report
        return ToContext(addition=future)          # wait for it to finish, assign to ctx.addition

    def validate_result(self):
        if self.ctx.addition.outputs.sum.value < 0:
            return self.exit_codes.ERROR_NEGATIVE_NUMBER

    def result(self):
        self.out("result", self.ctx.addition.outputs.sum)
```

Key points:

- In `define()`, `spec.input/output/exit_code/outline` are the entire contract; **every step of the outline must be idempotent and re-entrant** (the process may resume from a checkpoint).
- `self.submit(...)` must be paired with `return ToContext(...)` (or `self.to_context(...)`), otherwise the WorkChain will not wait for the child process.
- `self.ctx` is the process-level context; do not put large objects other than nodes into it.
- Express failures with `exit_code` and recovery strategies with `@process_handler`; do not swallow them with `try/except`.
- Child process fails → the parent's `exit_status` is determined by the exit code you return; `verdi process status <pk>` shows the whole tree.

## 5.3 Reusing someone else's inputs and outputs: expose / exposed

```python
class BetterMultiplyAddWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.expose_inputs(MultiplyAddWorkChain, namespace="multiply_add")
        spec.outline(cls.run_child, cls.finish)
        spec.expose_outputs(MultiplyAddWorkChain)          # forward the child chain's output ports directly

    def run_child(self):
        future = self.submit(
            MultiplyAddWorkChain,
            **self.exposed_inputs(MultiplyAddWorkChain, "multiply_add"),
        )
        return ToContext(child=future)

    def finish(self):
        self.out_many(self.exposed_outputs(self.ctx.child, MultiplyAddWorkChain))
```

`include=[...]` exposes only part of the ports, and `namespace=` decides the nesting location; when the child chain adds ports in an upgrade, the parent chain needs no change.

## 5.4 Batching: one WorkChain wrapping N child jobs

**Use this only when you need "a single batch-level exit code / one summary"**; otherwise use a loop at the `scripts` layer or
`SubmissionController` (see `03-usage-scripts.md`), which isolates failures better.

```python
from aiida.engine import WorkChain, append_
from aiida import orm

class BatchSubmitWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.expose_inputs(ChildWorkChain, include=["abacus", "clean_workdir", "kpoints_distance"])
        spec.input("cases", valid_type=orm.List)          # [case1, case2, ...]
        spec.outline(cls.setup, cls.submit_children, cls.gather_results)
        spec.output("results", valid_type=orm.Dict)

    def setup(self):
        self.ctx.children = []

    def submit_children(self):
        base = self.exposed_inputs(ChildWorkChain, agglomerate=True)
        for case in self.inputs.cases.get_list():
            inputs = dict(base)
            inputs["abacus"] = dict(base["abacus"])
            inputs["abacus"]["metadata"] = {
                **(base["abacus"].get("metadata") or {}),
                "label": f"batch_{case}",
            }
            self.ctx.children.append(self.submit(ChildWorkChain, **inputs))
        self.to_context(children=append_(*self.ctx.children))

    def gather_results(self):
        rows = [
            {"case": case, "pk": node.pk, "exit_code": node.exit_status,
             "ok": node.is_finished_ok}
            for case, node in zip(self.inputs.cases.get_list(), self.ctx.children)
        ]
        self.out("results", orm.Dict(dict={"rows": rows}))
```

> Pitfall: `append_()` accepts **one** argument only (or appends several at once), and the signature differs between versions;
> the most robust form is a separate `self.to_context(children=append_(node))` for each child job, or, as above,
> collecting them first and then calling `append_(*nodes)` in one go (works on 2.8).

## 5.5 Continuation and resubmission

```python
# 1) Restart from an existing node (reusing input and output ports)
old = orm.load_node(pk)
builder = old.get_builder_restart()

# 2) Continue from the remote directory (e.g. read the previous step's WAVECAR/charge density)
builder.remote_workdir = old.outputs.remote_folder

# 3) Change just one input and resubmit (typically: tighten scf_thr)
builder.abacus.parameters = orm.Dict(dict={...})
submit(builder)
```

> `get_builder_restart()` rebuilds only **what can be stored**: input links + `metadata_inputs`.
> A plain dict placed in a dynamic namespace (such as `base.abacus.metadata.options`) is lost —
> see `troubleshooting/cases/001-scheduler-options-lost.yaml`.

## 5.6 Checking your own WorkChain

```bash
verdi plugin list aiida.workflows <entry_point>    # whether the spec was registered successfully
verdi process status <pk>                          # which outline step has been reached
verdi process report <pk>                          # output of self.report()
verdi process repair                               # zombie processes (stop the daemon first)
```

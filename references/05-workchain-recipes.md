---
verified: 2026-11
applies_to: "aiida-core>=2.6,<3"
---

# 3C. 自己写 WorkChain 的骨架

`03-usage-workflow.md` 讲的是"用现成的 WorkChain"。只有确实组合不起来时才自己写，
骨架如下（全部在 aiida-core 2.8 上验证过）。

## 5.1 三种可执行单元

| 装饰器 / 类 | 什么时候用 | 是否产生 Process 节点 |
|---|---|---|
| `@calcfunction` | 纯函数式的数据转换（做单位换算、拟合并返回 `Dict`） | 是（CalcFunctionNode） |
| `@workfunction` | 只把多个 calcfunction 串起来，无外部作业 | 是 |
| `WorkChain` 子类 | 有外部作业、要重试/分支/等待子进程 | 是（WorkChainNode） |

```python
from aiida.engine import calcfunction, workfunction
from aiida.orm import Int

@calcfunction
def multiply(x, y):
    return x * y            # 返回值自动包成节点并入库

@workfunction
def add_multiply(x, y, z):
    return multiply(x + y if False else x, y) if False else multiply(x, y)
```

> 经验：`@calcfunction` 的返回值必须是可被 AiiDA 序列化的类型（`Int`/`Float`/`Str`/`Dict`/`StructureData`…），
> 普通 `float` 会被自动包装；`numpy` 数组请放进 `ArrayData`/`Dict`。

## 5.2 WorkChain 的最小骨架

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
        self.ctx.product = multiply(self.inputs.x, self.inputs.y)   # 自动入库

    def add(self):
        future = self.submit(
            ArithmeticAddCalculation,
            x=self.ctx.product, y=self.inputs.z, code=self.inputs.code,
        )
        self.report(f"submitted {future}")        # 写进 process 日志，verdi process report 可见
        return ToContext(addition=future)          # 等它结束，赋给 ctx.addition

    def validate_result(self):
        if self.ctx.addition.outputs.sum.value < 0:
            return self.exit_codes.ERROR_NEGATIVE_NUMBER

    def result(self):
        self.out("result", self.ctx.addition.outputs.sum)
```

要点：

- `define()` 里 `spec.input/output/exit_code/outline` 就是全部契约；**outline 的每一步都必须是幂等可重入的**（进程可能从 checkpoint 恢复）。
- `self.submit(...)` 必须 `return ToContext(...)`（或 `self.to_context(...)`），否则 WorkChain 不会等子进程。
- `self.ctx` 是进程级上下文；不要往里塞节点以外的大对象。
- 失败用 `exit_code` 表达，用 `@process_handler` 做恢复策略，别用 `try/except` 吞掉。
- 子进程失败 → 父进程 `exit_status` 由你 return 的 exit code 决定；`verdi process status <pk>` 能看整棵树。

## 5.3 复用别人的输入输出：expose / exposed

```python
class BetterMultiplyAddWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.expose_inputs(MultiplyAddWorkChain, namespace="multiply_add")
        spec.outline(cls.run_child, cls.finish)
        spec.expose_outputs(MultiplyAddWorkChain)          # 直接转发子链的输出端口

    def run_child(self):
        future = self.submit(
            MultiplyAddWorkChain,
            **self.exposed_inputs(MultiplyAddWorkChain, "multiply_add"),
        )
        return ToContext(child=future)

    def finish(self):
        self.out_many(self.exposed_outputs(self.ctx.child, MultiplyAddWorkChain))
```

`include=[...]` 只暴露部分端口，`namespace=` 决定嵌套位置；子链升级加端口时，父链不用改。

## 5.4 批量：一个 WorkChain 包 N 个子作业

**只在需要"一个批次级退出码/一份汇总"时才用**；否则用 `scripts` 层的循环或
`SubmissionController`（见 `03-usage-scripts.md`），失败隔离更好。

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

> 坑：`append_()` 只接受**一个**参数（或一次追加多个），不同版本签名不同；
> 最稳的写法是每个子作业单独 `self.to_context(children=append_(node))`，或者像上面
> 这样先收集再一次性 `append_(*nodes)`（2.8 可用）。

## 5.5 续算与重提

```python
# 1) 从已有节点重启（复用输入与输出端口）
old = orm.load_node(pk)
builder = old.get_builder_restart()

# 2) 从 remote 目录续算（例如读上一步的 WAVECAR/charge density）
builder.remote_workdir = old.outputs.remote_folder

# 3) 只换一个输入再提交（典型：收紧 scf_thr）
builder.abacus.parameters = orm.Dict(dict={...})
submit(builder)
```

> `get_builder_restart()` 只重建**存得住的东西**：input link + `metadata_inputs`。
> 放在 dynamic 命名空间里的普通 dict（如 `base.abacus.metadata.options`）会丢——
> 见 `troubleshooting/cases/001-scheduler-options-lost.yaml`。

## 5.6 检查自己的 WorkChain

```bash
verdi plugin list aiida.workflows <entry_point>    # spec 是否注册成功
verdi process status <pk>                          # outline 走到哪一步
verdi process report <pk>                          # self.report() 的输出
verdi process repair                               # 僵尸进程（需先停 daemon）
```

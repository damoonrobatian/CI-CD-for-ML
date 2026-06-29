# Makefile — Brief Guide

**Doc index:** [README.md](./README.md) · **Full tutorial:** [makefile-tutorial.md](./makefile-tutorial.md)

**Short version.** For the full beginner tutorial, see [makefile-tutorial.md](./makefile-tutorial.md).

---

## In One Sentence

A **`Makefile`** is a text file (no extension) that defines named shortcuts; the **`make`** program runs one shortcut at a time — e.g. `make train` runs the shell commands listed under the `train` rule.

---

## The Mental Model

```text
python train.py   →  python reads train.py
make train        →  make reads Makefile, runs the "train" block
```

You never execute `./Makefile`. You always run **`make <target>`**.

---

## One Rule

```makefile
target-name:
	shell command    ← must start with Tab, not spaces
```

---

## Who Uses It Here?

| Who | How |
|-----|-----|
| **You** | `make train` from project root |
| **GitHub Actions** | `run: make install`, `make train`, `make eval` in workflow YAML |

The workflow picks **order**; the Makefile defines **what each step runs**.

---

## Our Targets

| Command | Does |
|---------|------|
| `make install` | `pip install` from `requirements.txt` |
| `make format` | `black *.py` |
| `make train` | `python train.py` → writes `results/`, `model/` |
| `make eval` | Builds `report.md`, posts via CML — **run after `train`** |

---

## CI Flow

```text
push → make install → make train → make eval
```

---

## Rules Worth Remembering

1. **Tab, not spaces** before recipe lines — or `make` errors with `missing separator`.
2. **`.PHONY: install format train eval`** — marks targets as commands, not filenames (avoids weird skips if a file named `train` exists).
3. **`&&` and `\`** — chain commands in one shell; stop if a step fails (`install` target).
4. **`$(VAR)`** — pass values from CLI: `make deploy HF=hf_xxx` (used later for secrets).
5. **Not a linear script** — `make eval` does not auto-run `train` unless you add `eval: train` or CI calls both.

---

## Makefile Vs Bash Script

| Makefile | Bash script |
|----------|-------------|
| Menu: `make train` runs one block | Linear: runs top to bottom |
| Common in CI tutorials | Also fine for CI |
| ML logic stays in `train.py` | Same |

---

## Common Mistakes

- Spaces instead of Tab → `missing separator`
- `make eval` before `make train` → empty/missing metrics
- Typo: `make trai` → `No rule to make target`

---

## Try It

```bash
make --version
make train
make eval
```

---

**Full tutorial:** [makefile-tutorial.md](./makefile-tutorial.md)

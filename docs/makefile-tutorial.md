# Makefile Tutorial (For Complete Beginners)

**Prefer a short summary?** See [makefile-tutorial-brief.md](./makefile-tutorial-brief.md).

This guide explains what a `Makefile` is, how the `make` program uses it, and how our CI/CD project relies on one. No prior experience with `make` is assumed.

If you already know bash or Python scripts, the main mental shift is: **a Makefile is not a script you run directly**. It is a **menu of named commands** read by a separate program called **`make`**.

---

## 1. The Two Pieces: `make` And `Makefile`

| Piece | What it is |
|-------|------------|
| **`make`** | A program installed on your system (like `python` or `bash`) |
| **`Makefile`** | A text file that tells `make` what commands to run |

**File name:** usually `Makefile` — capital M, **no extension** (not `Makefile.sh`, not `Makefile.txt`). `makefile` (lowercase) also works.

**How you use it:**

```bash
make train
```

That does **not** execute the Makefile as a program. It tells **`make`** to:

1. Open the file `Makefile` in the current directory
2. Find the rule whose name is `train`
3. Run the shell commands listed under that rule

Same pattern you already know:

```bash
python train.py    # python = program, train.py = input file
make train         # make   = program, Makefile = input file (rule name = train)
```

The word `make` does not appear inside the Makefile for the same reason `python` does not appear inside `train.py`.

---

## 2. Who Runs The Makefile?

Three common cases:

### You, Locally

From the project root:

```bash
make install   # install dependencies
make train     # run train.py
make eval      # build CML report (after train)
```

### GitHub Actions (CI)

The workflow file (`.github/workflows/ci.yml`) will contain steps like:

```yaml
- run: make install
- run: make train
- run: make eval
```

Each step invokes **one** target from the Makefile. The workflow decides **order**; the Makefile defines **what each step does**.

### Nobody Runs The File Itself

These are **wrong**:

```bash
./Makefile
bash Makefile
python Makefile
```

---

## 3. How A Makefile Differs From A Normal Script

### A Bash Script (Linear)

```bash
#!/bin/bash
pip install -r requirements.txt
python train.py
echo "done"
```

Run once, top to bottom: `./script.sh`.

### A Makefile (Menu)

```makefile
install:
	pip install -r requirements.txt

train:
	python train.py
```

Run **one item** from the menu: `make train` runs only the `train` block.

| | Bash script | Makefile |
|---|-------------|----------|
| Structure | One flow, start to finish | Named targets, pick one |
| Typical run | `./ci.sh` | `make train` |
| Best for | “Do all of this in order” | “Same commands in CI and locally, split into steps” |

Our project uses a Makefile so CI can call `make install`, then `make train`, then `make eval` without duplicating long shell blocks in YAML. You could achieve the same with a bash script; Make is a **common convention** in CI tutorials, not a technical requirement.

---

## 4. Anatomy Of One Rule

Every useful part of a Makefile is a **rule**:

```makefile
target-name:
	shell command 1
	shell command 2
```

| Part | Name | Meaning |
|------|------|---------|
| `target-name` | **target** | The name you pass to `make` (`make target-name`) |
| `:` | separator | Ends the target line; optional **prerequisites** can follow |
| Indented lines | **recipe** | Shell commands `make` executes |

Example from this repo:

```makefile
train:
	python train.py
```

When you run `make train`, `make` runs the equivalent of:

```bash
python train.py
```

---

## 5. The Tab Rule (Important)

Recipe lines **must** be indented with a **Tab character**, not spaces.

**Correct:**

```makefile
train:
	python train.py
```
(The line above `python` starts with Tab.)

**Wrong:**

```makefile
train:
    python train.py
```
(spaces — `make` will error: `missing separator`.)

This is an old format requirement, not a stylistic choice.

---

## 6. Multiple Commands In One Target

Each recipe line runs in a **new shell** by default.

```makefile
eval:
	echo "## Model Metrics" > report.md
	cat ./results/metrics.json >> report.md
```

Line 1 creates `report.md`. Line 2 runs in a **new** shell but still works because `report.md` was written to disk.

To run commands in the **same** shell and stop if the first fails, use `&&` and `\`:

```makefile
install:
	pip install --upgrade pip && \
	pip install -r requirements.txt
```

- `&&` — run the next command only if the previous succeeded  
- `\` — line continuation (one logical line)

This is exactly what our `install` target does.

---

## 7. Prerequisites (Optional)

Full rule form:

```makefile
target: prerequisite1 prerequisite2
	recipe...
```

Meaning: before running the recipe, `make` ensures prerequisites are satisfied (originally: build files if they are out of date).

Example (not in our Makefile yet, but useful):

```makefile
eval: train
	echo "## Model Metrics" > report.md
	...
```

Then `make eval` would run the `train` target first, then the `eval` recipe.

Our CI does **not** rely on this — it calls `make train` and `make eval` as separate workflow steps in order.

---

## 8. What `.PHONY` Means (Concrete Example)

`make` was designed to **build files** from other files:

```makefile
app: main.o
	gcc -o app main.o
```

Here `app` is a **filename**. If `app` already exists and is up to date, `make` skips the recipe.

Our targets are **actions**, not filenames:

```makefile
train:
	python train.py
```

There is no output file called `train`.

**Problem:** If someone adds a file named `train` to the repo:

```bash
touch train    # empty file
make train     # make may think "train is up to date" and run NOTHING
```

**Fix:** declare phony (command-only) targets:

```makefile
.PHONY: install format train eval

install:
	...
```

`.PHONY: train` tells `make`: **always run the recipe when I say `make train`**, never treat `train` as a file on disk.

Recommended for every target in this project that is a command, not a build artifact.

---

## 9. Variables

Make can substitute variables in recipes:

```makefile
deploy:
	huggingface-cli login --token $(HF)
```

Usage:

```bash
make deploy HF=hf_xxxxxxxx
```

`$(HF)` is replaced with the value you pass on the command line. The tutorial uses this for GitHub Secrets (`HF`, `USER_NAME`, `USER_EMAIL`) so tokens never live in the Makefile itself.

---

## 10. Our Project’s Makefile, Line By Line

Current file at the repo root:

```makefile
install:
	pip install --upgrade pip && \
	pip install -r requirements.txt

format:
	black *.py

train:
	python train.py

eval:
	echo "## Model Metrics" > report.md
	cat ./results/metrics.json >> report.md

	echo "## Confusion Matrix Plot" >> report.md
	echo "![Confusion Matrix](./results/confusion_matrix.png)" >> report.md

	cml comment create report.md
```

### `install`

Installs Python packages from `requirements.txt`. Used in CI before training.

### `format`

Runs `black` on `*.py`. Optional style check in CI.

### `train`

Runs `train.py` — the real ML work (fit pipeline, save metrics, confusion matrix, model). **This is where learning happens**; the Makefile only wraps one shell command.

### `eval`

Builds `report.md` for **CML** (Continuous Machine Learning):

1. Write a markdown heading  
2. Append contents of `results/metrics.json`  
3. Append a markdown image link to `results/confusion_matrix.png`  
4. Run `cml comment create report.md` to post the report on the commit/PR  

**Must run after `train`**, because `train.py` creates the files in `results/`.

---

## 11. How This Fits In CI (Big Picture)

```text
You push to GitHub
        │
        ▼
GitHub Actions workflow starts
        │
        ├── make install   → pip install deps
        ├── make format    → black (optional)
        ├── make train     → python train.py → results/, model/
        └── make eval      → report.md → CML comment on commit
```

The Makefile is the **shared command list** used by both your laptop and the CI runner. The ML logic stays in `train.py`; the workflow stays in YAML; the Makefile sits in the middle as short, reusable shell wrappers.

---

## 12. Try It Yourself

From the project root, with your conda env activated:

```bash
# See whether make is installed
make --version

# Run one step
make train

# Run another (needs results/ from train)
make eval
```

If `make` is missing on Linux:

```bash
sudo apt install make
```

---

## 13. Common Errors

| Error | Cause |
|-------|--------|
| `missing separator. Stop.` | Used spaces instead of Tab before a recipe line |
| `No rule to make target 'trai'.` | Typo in target name |
| `make: *** [train] Error 1` | Recipe command failed (e.g. `python train.py` crashed) |
| `make train` does nothing | A file named `train` exists; add `.PHONY: train` |
| `make eval` shows empty metrics | Ran `eval` before `train` |

---

## 14. Quick Reference

```text
Makefile     = text file, no extension, read by `make`
make TARGET  = run the recipe for TARGET
target:      = start of a rule
<Tab>cmd     = shell command (Tab required)
.PHONY:      = target is a command, not a filename
$(VAR)       = variable substituted from command line or environment
A && B       = run B only if A succeeds
line \         = continue recipe on next line
```

---

## 15. Further Reading

- GNU Make manual (official, dense): https://www.gnu.org/software/make/manual/
- Our CI setup notes: [setup-notes.md](./setup-notes.md)

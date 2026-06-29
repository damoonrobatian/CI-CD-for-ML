# GitHub Actions Workflow: `ci.yml` Deep Dive

**Doc index:** [README.md](./README.md)

This document explains [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) line by line: what triggers CI, what each YAML block does, how it connects to the Makefile, and what to check when a run fails.

**Shorter paths:** [tutorial.md §8](./tutorial.md) (walkthrough while building) · [github-actions-and-cml.md](./github-actions-and-cml.md) (runners, CML comments, comment vs commit)

---

## What This File Does (One Paragraph)

When you push to `main`, open a pull request targeting `main`, or manually start the workflow, GitHub spins up a temporary Linux VM, copies your repo onto it, installs Python and CML, then runs the same three Makefile targets you use locally: `make install`, `make train`, and `make eval`. Training writes metrics and a model under `results/` and `model/` on that VM (those files are **not** pushed back to GitHub). `make eval` builds a markdown report and CML posts it as a **comment** on the commit or PR. When the job finishes, the VM is deleted.

---

## Where The File Lives

```text
.github/
└── workflows/
    └── ci.yml    ← workflow definition (YAML)
```

GitHub only runs workflows stored under `.github/workflows/` with a `.yml` or `.yaml` extension.

---

## Full File (Reference)

```yaml
name: Continuous Integration

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pull-requests: write

jobs:
  train-and-report:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Set up CML
        uses: iterative/setup-cml@v3

      - name: Install dependencies
        run: make install

      - name: Train model
        run: make train

      - name: Publish metrics report
        env:
          REPO_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: make eval
```

---

## Top-Level Keys

### `name: Continuous Integration`

Human-readable label shown in the GitHub **Actions** tab. Does not affect behavior.

### `on:` (Triggers)

| Trigger | When it runs |
|---------|----------------|
| `push` to `main` | Every commit pushed to the `main` branch |
| `pull_request` to `main` | When someone opens or updates a PR whose base branch is `main` |
| `workflow_dispatch` | Manual run from Actions → workflow → **Run workflow** |

**Why both push and pull_request?** Pushes on `main` give you a report on every merge. PRs give you a report **before** merge so you can see metrics on the proposed change.

**What is not triggered:** Pushes to other branches (e.g. a feature branch) do not run this workflow unless you open a PR to `main` or add more `on:` rules.

### `permissions:`

```yaml
permissions:
  contents: read
  pull-requests: write
```

GitHub Actions jobs get a token (`GITHUB_TOKEN`). The `permissions` block limits what that token can do (principle of least privilege).

| Permission | Why we need it |
|------------|----------------|
| `contents: read` | Checkout the repo (read files) |
| `pull-requests: write` | CML posts comments on commits and PRs |

The DataCamp tutorial often uses `permissions: write-all`, which grants broad write access. This repo uses **narrow** permissions: enough for CML comments, not full repo write.

### `jobs:`

A workflow can define multiple jobs (e.g. lint in parallel with train). This project uses **one job**: `train-and-report`.

| Key | Value | Meaning |
|-----|-------|---------|
| `train-and-report` | Job id | Name you choose; appears in the Actions UI |
| `runs-on: ubuntu-latest` | Runner image | Fresh Ubuntu Linux VM in GitHub's cloud |

---

## Steps (In Order)

Each `- name:` block is one step. Steps run **sequentially**; if one fails, later steps are skipped and the job is marked failed.

### 1. Checkout

```yaml
- name: Checkout
  uses: actions/checkout@v4
```

**Action:** `actions/checkout@v4` (official GitHub action, version pinned with `@v4`).

**Effect:** Clones your repository into the runner's working directory (usually `/home/runner/work/CI-CD-for-ML/CI-CD-for-ML`). Without this, `make train` would not see `train.py` or `data/drug.csv`.

### 2. Set up Python

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.13"
```

**Action:** Installs Python on the runner and puts it on `PATH`.

**Why pin 3.13?** Matches the tutorial's conda recommendation. CI and local dev should use the same major/minor version when possible to avoid "works on my machine" sklearn or pip issues.

### 3. Set up CML

```yaml
- name: Set up CML
  uses: iterative/setup-cml@v3
```

**Action:** Installs the [CML](https://cml.dev/) CLI on the runner so `make eval` can run `cml comment create`.

CML is **not** installed by `make install` / `requirements.txt` in this repo; it comes from this dedicated step. That keeps local `pip install` minimal while CI still gets CML.

### 4. Install dependencies

```yaml
- name: Install dependencies
  run: make install
```

**Shell command** on the runner (not a reusable action). Runs the `install` target from the [Makefile](../Makefile):

```makefile
install:
	pip install --upgrade pip && \
	pip install -r requirements.txt
```

Installs pandas, scikit-learn, skops, black, cml (listed in requirements), etc. **only on the runner** for this job.

### 5. Train model

```yaml
- name: Train model
  run: make train
```

Runs `python train.py`, which:

- Loads `data/drug.csv`
- Fits the sklearn pipeline
- Writes `results/metrics.json`, `results/confusion_matrix.png`, `model/model.skops`

These artifacts exist on the runner filesystem for the next step. They are **not** automatically committed to git.

### 6. Publish metrics report

```yaml
- name: Publish metrics report
  env:
    REPO_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: make eval
```

**Environment variable:** `REPO_TOKEN` is what CML expects. It is set to GitHub's automatic `GITHUB_TOKEN` for this workflow run.

**`make eval`** (from Makefile):

1. Builds `report.md` from metrics JSON and a markdown image link to the confusion matrix PNG
2. Runs `cml comment create report.md`, which posts that content as a GitHub **comment**

This is **not** `git commit`. The report does not become part of the repo unless you commit it yourself.

---

## End-To-End Flow

```text
Trigger (push / PR / manual)
        │
        ▼
GitHub allocates ubuntu-latest runner
        │
        ├── checkout@v4          → repo files on disk
        ├── setup-python@v5      → Python 3.13
        ├── setup-cml@v3         → cml CLI
        ├── make install         → pip deps
        ├── make train           → results/, model/ on runner
        └── make eval            → CML comment on GitHub
        │
        ▼
Runner destroyed (artifacts on disk gone unless uploaded elsewhere)
```

---

## How This Relates To The Makefile

| CI step | Makefile target | Main effect |
|---------|-----------------|-------------|
| Install dependencies | `install` | `pip install -r requirements.txt` |
| Train model | `train` | `python train.py` |
| Publish metrics report | `eval` | `report.md` + `cml comment create` |

**Design choice:** CI does not call `python train.py` directly. It calls `make train` so local commands and CI stay identical. Change training once in the Makefile; both environments pick it up.

**Not in CI (yet):** `make format` (black). Omitted so formatting does not block early CI learning. You can add a separate job later.

---

## Tokens And Secrets

| Name | Source | Purpose |
|------|--------|---------|
| `GITHUB_TOKEN` | Created automatically per workflow run | API access scoped by `permissions` |
| `REPO_TOKEN` | Set in `env:` to `${{ secrets.GITHUB_TOKEN }}` | CML reads this name to authenticate |

You do **not** need to create a Personal Access Token in repo Settings for basic CML comments on the same repo, as long as `pull-requests: write` is granted.

For pushing to Hugging Face or other services, you would add **repository secrets** (e.g. `HF_TOKEN`) in a future CD workflow, not in this CI file.

---

## Viewing Results

1. GitHub repo → **Actions** tab → click **Continuous Integration** → open a run
2. Expand steps to read logs (`Train model`, `Publish metrics report`, etc.)
3. On success: open the commit or PR page and look for a **bot comment** with metrics and the confusion matrix image

Green check = job succeeded. Red X = a step failed; open the failed step for the error message.

---

## Common Failures

| Symptom | Likely cause |
|---------|----------------|
| Failed at `make install` | Bad `requirements.txt`, network/pip error |
| Failed at `make train` | Missing `data/drug.csv`, Python/sklearn error in `train.py` |
| Failed at `make eval` | CML not installed, missing `REPO_TOKEN`, or insufficient `permissions` |
| Workflow does not start | Push was not to `main`, or `.github/workflows/ci.yml` not on the branch |
| No comment on PR | Check `pull-requests: write`; check eval step logs for CML errors |
| `make eval` works in CI but not locally | Local machine needs `pip install cml` and a token if you want local CML posts |

---

## What This Workflow Does **Not** Do

- **No CD:** Does not deploy to Hugging Face Spaces (that would be a separate `cd.yml` or job)
- **No git push of artifacts:** Metrics PNG and model stay on the runner unless you add upload/commit steps
- **No lint gate:** `make format` is not run
- **No matrix builds:** Single OS, single Python version (not testing 3.11 and 3.13 in parallel)
- **No caching:** Every run reinstalls pip packages (fine for teaching; optimize later with `actions/cache`)

---

## Tweaks You Might Add Later

```yaml
# Example: run black in a separate job
lint:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.13"
    - run: make install && make format
```

```yaml
# Example: cache pip between runs
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

---

## YAML Syntax Reminders

- **Indentation matters** (spaces, not tabs). `steps` must be indented under the job; each step under `steps`.
- **`uses:`** = run a published action (reusable unit).
- **`run:`** = run a shell command (bash on `ubuntu-latest`).
- **`with:`** = inputs to an action.
- **`env:`** = environment variables for that step only (unless set at job level).

---

## Related Docs

- [tutorial.md §8](./tutorial.md): build CI as part of the main walkthrough
- [github-actions-and-cml.md](./github-actions-and-cml.md): runners, "install in CI", CML vs git commit
- [makefile-tutorial-brief.md](./makefile-tutorial-brief.md): what `install`, `train`, `eval` do
- [Makefile](../Makefile): commands CI invokes

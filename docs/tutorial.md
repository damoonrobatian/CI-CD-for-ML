# CI/CD For Machine Learning (Student Tutorial)

This tutorial teaches **CI/CD for machine learning** using a small scikit-learn project in this repo. You will learn what each tool does, why teams use it, and how the pieces connect. The sample CSV and classifier are only a **workload** so you have something real to train and deploy; the learning goal is automation, not drug classification.

We improve on the [DataCamp CI/CD tutorial](https://www.datacamp.com/tr/tutorial/ci-cd-for-machine-learning) where it is unclear or wrong.

**How to use this doc:** read each section in order. Do the hands-on steps as you go. Appendix files ([docs/README.md](./README.md)) go deeper on one topic if you want extra reading; you should not need them to understand the core ideas.

---

## 0. What You Will Learn And Build

### Concepts You Will Understand By The End

| Topic | You will be able to explain |
|-------|-----------------------------|
| **CI (Continuous Integration)** | Automated integration build + validation on push/PR (here: install, train, report metrics on a clean runner) |
| **CD (Continuous Deployment)** | Automated publish to a user-facing demo environment after checks pass (here: Hugging Face Space) |
| **Makefile / targets** | Named commands (`install`, `train`, `eval`) shared by you and CI |
| **GitHub Actions** | YAML workflow that runs on a temporary cloud VM |
| **CML** | Posts training results as a **GitHub comment**, not a git commit |
| **sklearn Pipeline** | One object that preprocesses and predicts so train and app stay aligned |
| **Hugging Face Space** | Public host for a Gradio demo (not the same as production AWS/GCP) |

### What You Will Build

```text
You push code to GitHub
        │
        ▼
GitHub Actions (temporary Linux VM)
        ├── install Python deps     (make install)
        ├── train model             (make train → train.py)
        └── post metrics + plot     (make eval → CML comment)
        │
        ▼ (later)
Hugging Face Space runs your Gradio app with the trained model
```

| Piece | Role |
|-------|------|
| **GitHub repo** | Stores source code, small data, workflow files |
| **Makefile** | Same commands for your laptop and for CI |
| **GitHub Actions** | Runs those commands on every push/PR to `main` |
| **CML** | Publishes metrics where reviewers see them (commit/PR page) |
| **Hugging Face Space** | Live demo UI for stakeholders |

---

## 1. CI/CD In Plain Language

Read this section carefully before you touch `ci.yml`. Most confusion about GitHub Actions comes from mixing up **where code runs** and **what "CI" means**.

### 1.1 Three Machines, Three Jobs

Training and `pip install` do **not** happen only on the runner. They happen in **three separate places**, each with a different purpose:

| Machine | Who uses it | What runs there in this project |
|---------|-------------|----------------------------------|
| **Your laptop** | You while developing | `pip install`, `make train`, [experiments.ipynb](../experiments.ipynb) |
| **GitHub Actions runner** | Automation on push/PR | Same Makefile targets again, on a **clean temporary VM** |
| **Hugging Face Space** (later) | End users of the demo | Gradio app loads the model and **predicts**; it does not retrain on every git push |

The runner does **not** replace your laptop or production/demo. You still develop locally. The Space still serves the app. The runner adds an **automatic check** when code reaches GitHub.

```text
Local:     you develop and train
Runner:    auto-check that the repo trains cleanly (Section 8)
HF Space:  demo / inference after you deploy (Section 10)
```

### 1.2 What "CI" And "CD" Mean (Vocabulary Matters)

Tutorials (including DataCamp) often say "CI" loosely. Three ideas are worth separating:

**Classical Continuous Integration:** developers merge into a shared mainline **often**. Each merge triggers an **integration build**: combine the latest code, build/package it, run tests. "Integration" means *does the combined codebase still work together?* It is **not** the same as shipping to users.

**What many people call "CI" today:** any workflow on push/PR that runs `install` + tests. In ML repos that often includes **retraining** and metric reports. That is closer to **automated verification** or a **CI pipeline**, even when the label on GitHub still says "Continuous Integration."

**Continuous Delivery / Deployment (CD):** automating promotion of a good build into an **environment users see** (staging, demo URL, production). Integrating changes **into the user-facing system** is CD territory, not what `ci.yml` does today.

**What this repo's `ci.yml` honestly is:**

| Step in workflow | Category |
|------------------|----------|
| Checkout repo at this commit | Integration build (test the integrated tree) |
| `make install`, `make train` | Validation / reproducibility on a clean machine |
| `make eval` (CML comment) | Reporting for reviewers (not a git commit, not deploy) |
| Upload to Hugging Face Space | **Not in `ci.yml`**; that is Section 10 (CD) |

So when we say "CI" in this course, we mean: **on every push/PR to `main`, automatically verify that the repo still installs, trains, and produces metrics**, without using your laptop and **without** updating the live demo.

### 1.3 Why GitHub Needs A Runner At All

**GitHub stores your repo; it does not execute your Python code** when you push. Files on github.com are storage and a website (PRs, comments, Actions UI). Something else must run `pip install` and `python train.py` for automation. That something is the **runner**: a real Linux VM GitHub starts for one job, then deletes.

**Why checkout (copy) the repo onto the runner?** The VM starts empty. It does not have your `train.py`, `Makefile`, or `data/drug.csv` until `actions/checkout` clones the repo at **that commit** onto the runner's disk. Then `make train` works the same way as on your laptop: commands run inside a project folder.

**Why run the same commands again if you already ran them locally?** Because CI answers a different question:

| Question | Answered by |
|----------|-------------|
| Does it work on **my** machine right now? | Local `make train` |
| Does the **repo** work on a **clean** machine when anyone pushes? | Runner `make train` |
| Can **users** try the model in a browser? | Hugging Face Space (after CD) |

Local environments hide problems: forgotten pip packages, old conda state, "works on my machine." The runner reruns your Makefile on a fresh OS so the **repository** is tested, not just your personal setup.

**What the runner is not doing:** it is not deploying to users, and it is not the only place training ever happens. Artifacts on the runner (`results/`, `model/`) live on that disk for minutes; they are **not** committed to GitHub. Reviewers see metrics via a **CML comment**, not new files in the repo.

You **could** skip GitHub Actions for a solo hobby project and only use local runs plus manual deploy. Teams add CI so nobody has to remember to rerun checks and so merges are verified the same way for everyone.

### 1.4 Without vs With Automation

**Without CI/CD:** you change code, train on your laptop, hope nothing broke, and manually tell teammates or paste metrics.

**With CI (this repo):** every push/PR to `main` can automatically reinstall dependencies, retrain on a clean runner, and post metrics as a GitHub comment. Broken code is caught before or right after merge.

**With CD (later):** after CI succeeds, a workflow can upload the app and model to Hugging Face Space so others can use the demo without cloning the repo.

### 1.5 Names To Keep Straight

| Name | One-line role |
|------|----------------|
| **GitHub repo** | Code, data, workflow YAML; does not run training by itself |
| **Actions runner** | Temporary computer that runs `make install` / `train` / `eval` for CI |
| **CML** | Posts training results as a **comment** on the commit/PR page |
| **Hugging Face Space** | Public demo URL (portfolio/teaching; real products often use AWS/GCP instead) |

---

## 2. Prerequisites

You need:

- A **GitHub account** and this repo (fork or clone)
- **Python 3.13** (conda recommended):

```bash
conda create -n ci-cd-for-ml python=3.13 -y
conda activate ci-cd-for-ml
```

- A **Kaggle account** to download the sample dataset (Section 4)
- Later: a **Hugging Face account** for deployment (Section 9)

---

## 3. Project Layout

Repositories are easier to navigate when folders have stable roles. This project uses **lowercase** names (Linux paths are case-sensitive).

```text
CI-CD-for-ML/
├── .github/workflows/ci.yml   # CI workflow (Section 8)
├── app/                       # Gradio app + Space card config (Section 9)
├── data/drug.csv              # small training CSV (Section 4)
├── docs/                      # documentation (you are here)
├── experiments.ipynb          # optional local experiments (not run in CI)
├── model/                     # saved pipeline after training (generated)
├── results/                   # metrics JSON + plots (generated)
├── Makefile                   # named commands for you and CI (Section 5)
├── requirements.txt           # Python packages (Section 6)
├── train.py                   # training script CI runs (Section 4)
└── README.md
```

**Generated folders** (`model/`, `results/`) appear after `make train` on your laptop. In CI, the same files are created on the **runner's disk** during the job. They are not committed to GitHub automatically; CML shows metrics in a PR/commit comment instead. When the job ends, the runner is removed and those files are gone.

---

## 4. The Training Workload

CI will run your training script on a fresh machine. If training fails on your laptop, it will fail in CI. Always verify locally first.

### 4.1 Get The Data

Dataset: [Drug Classification on Kaggle](https://www.kaggle.com/datasets/prathamtripathi/drug-classification) (file `drug200.csv`).

```bash
pip install kaggle
# Kaggle → Settings → API → Create New Token → save as ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json

kaggle datasets download -d prathamtripathi/drug-classification -p data --unzip
mv data/drug200.csv data/drug.csv
```

**Why is the CSV in git?** For this small teaching dataset, committing `data/drug.csv` keeps CI simple. For large or licensed data, teams download in CI or use DVC/LFS instead ([data-in-git-dvc-lfs.md](./data-in-git-dvc-lfs.md)).

### 4.2 What `train.py` does

[train.py](../train.py) is the **canonical** training entry point. It:

1. Loads `data/drug.csv`
2. Builds a sklearn **Pipeline** (preprocessing + `RandomForestClassifier`)
3. Trains on a train split, evaluates on a held-out test split
4. Writes artifacts CI and CML use later:
   - `results/metrics.json` (accuracy, F1)
   - `results/confusion_matrix.png`
   - `model/model.skops` (full pipeline for the Gradio app)

Run it once:

```bash
pip install -r requirements.txt
python train.py
```

Or, after Section 5: `make install` then `make train`.

### 4.3 Preprocessing: Concepts You Must Understand

Machine learning code often fails in production because **training preprocessing** and **app preprocessing** diverge. This project avoids that by saving one **Pipeline** object that includes both preprocessing and the model.

#### sklearn `Pipeline`

A `Pipeline` chains steps. Calling `pipe.fit(X, y)` runs preprocessing then fits the model. Calling `pipe.predict(X_new)` applies the **same** preprocessing then predicts. The Gradio app only needs `load → predict`.

#### `ColumnTransformer`

Different columns need different transforms (encode categories, scale numbers). `ColumnTransformer` applies several transformers and concatenates the results into one matrix for the model.

**Common mistake (in the DataCamp tutorial):** listing imputer and scaler as **two separate** `ColumnTransformer` entries on the same numeric columns. Those entries run **in parallel** on the **original** columns, not one after another. You get duplicate numeric columns and the scaler never scales imputed values.

**Correct pattern:** nest imputer and scaler inside a small `Pipeline`, then attach that pipeline to numeric columns:

```python
Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])
```

#### Encoders: Not Every Categorical Column Is The Same

| Column | Type | Encoder in this repo |
|--------|------|----------------------|
| `Sex` | Nominal (no natural order) | `OneHotEncoder` |
| `BP` | Ordinal (LOW < NORMAL < HIGH) | `OrdinalEncoder` with explicit `categories=` |
| `Cholesterol` | Ordered levels | `OrdinalEncoder` with explicit `categories=` |

Using `OrdinalEncoder()` on everything (DataCamp shortcut) assigns arbitrary numeric order to `Sex` and uses **alphabetical** order for ordinals unless you pass `categories=`. Random Forest may still score well on this tiny dataset, but the pattern is wrong for learning and for linear models.

> [!WARNING]
> Do not copy the DataCamp preprocessing code blindly. Use [train.py](../train.py) as the reference implementation.

More encoder detail: [ml-preprocessing-and-models.md](./ml-preprocessing-and-models.md).

### 4.4 `experiments.ipynb` vs `train.py`

| File | Purpose |
|------|---------|
| [experiments.ipynb](../experiments.ipynb) | **Local scratchpad:** explore data, plot, try encoders, demo the ColumnTransformer mistake |
| [train.py](../train.py) | **Source of truth:** what `make train` and GitHub Actions run |

Notebooks are great for experiments but are poor as CI entry points (hidden state, run order). When your pipeline is right in the notebook, **copy the final logic into `train.py`**.

---

## 5. Makefiles: One Command Menu For You And CI

### 5.1 Why A Makefile?

Without a Makefile, your CI workflow might say:

```yaml
run: pip install -r requirements.txt && python train.py && ...
```

That duplicates shell commands in YAML and on your laptop. A **Makefile** centralizes them: you run `make train` locally; CI runs the same `make train` in the cloud.

### 5.2 Vocabulary

In [Makefile](../Makefile), each rule looks like:

```makefile
train:
	python train.py
```

| Term | Meaning | Example |
|------|---------|---------|
| **Target** | Name of the rule (left of `:`) | `train`, `install`, `eval` |
| **Recipe** | Shell commands under the target (indented with **Tab**) | `python train.py` |
| **Command you type** | `make` + target | `make train` |

You never execute `./Makefile`. You run **`make <target>`**.

### 5.3 Our Targets

| Target | What it runs | When you use it |
|--------|--------------|-----------------|
| `install` | `pip install -r requirements.txt` | Once per environment, or first CI step |
| `train` | `python train.py` | After code or data changes |
| `eval` | Builds `report.md`, runs `cml comment create` | After `train` (needs metrics files) |
| `format` | `black *.py` | Optional local cleanup (not in CI yet) |

**Order matters:** `eval` reads files created by `train`. The Makefile does not auto-run `train` before `eval`; CI calls them as separate steps in order.

Try locally:

```bash
make install
make train
make eval    # may fail locally without CML token; Section 8 explains
```

Makefile quirks (tabs, `.PHONY`): [makefile-tutorial-brief.md](./makefile-tutorial-brief.md).

---

## 6. Python Dependencies (`requirements.txt`)

[requirements.txt](../requirements.txt) lists packages `make install` installs:

```text
pandas
matplotlib
scikit-learn
black
skops
cml
```

| Package | Role in this project |
|---------|----------------------|
| **pandas** | Load CSV in `train.py` |
| **matplotlib** | Confusion matrix plot |
| **scikit-learn** | Pipeline, model, metrics |
| **black** | Optional formatting (`make format`) |
| **skops** | Save/load full pipeline for the app (safer than raw pickle for shared models) |
| **cml** | Local `make eval` if configured; CI also installs CML via a GitHub Action |

Pinning versions in production teams reduces "works on my machine" drift. This repo uses simple unpinned names for teaching; CI always reinstalls from this file on a clean runner.

---

## 7. Git And GitHub Before Automation

CI runs on code **in GitHub**. You need correct git habits first.

### 7.1 Tracked Vs Untracked Files

Git only commits files it **tracks**. A new file you create is **untracked** until you `git add` it.

### 7.2 First Commit (New Project)

**Do not** rely on `git commit -am` alone for the first push. The `-a` flag stages changes only to **already tracked** files; it skips new files.

```bash
git add .
git status          # review what will be committed
git commit -m "Add training pipeline, Makefile, and data"
git push origin main
```

### 7.3 Later Edits

When you change **existing tracked** files only, `git commit -am "message"` is a convenient shortcut.

### 7.4 Git Commit Vs GitHub Comment (Preview)

| | **Git commit** | **GitHub comment (CML)** |
|---|----------------|---------------------------|
| Stores | Files in the repo | Markdown on the commit/PR page |
| Created by | `git commit` | `cml comment create` |
| Example output | `train.py`, `ci.yml` | Metrics table, confusion matrix image |

Section 8 returns to this distinction.

### 7.5 Branches, Pull Requests, And `main`

On GitHub, **`main`** is usually the shared branch everyone trusts. Day-to-day work often happens on a **feature branch**, then you propose merging it into `main` with a **pull request (PR)**.

```text
feature/fix-encoder  --PR-->  main
     (your branch)            (base / target)
```

**Targeting `main`** means the PR’s **base** branch is `main`. GitHub shows the diff that would land on `main` if the PR is merged. Reviewers (or you, on a solo project) can read that diff and see CI results before merge.

Typical team flow:

```bash
git checkout -b feature/my-change
# edit, commit
git push origin feature/my-change
# open PR on GitHub: base = main, compare = feature/my-change
# wait for CI green, then merge
```

**Do you always need a PR?** Your `ci.yml` does **not** require it. It runs CI on **both**:

| Event | When CI runs | Code on `main` yet? |
|-------|----------------|---------------------|
| `pull_request` → `main` | PR opened or updated | No (proposed change only) |
| `push` → `main` | Commits pushed or merged onto `main` | Yes |

Direct `git push origin main` still triggers CI, but **after** the code is already on `main`. PR CI runs **before** merge, which is why teams prefer branches + PRs: training and metrics are checked on the proposed change first.

For this course alone, pushing straight to `main` is fine while you learn. For team-style practice, use a branch and PR. To **enforce** PR-only merges on GitHub, enable **branch protection** on `main` (repo Settings); that is separate from the workflow file.

More git detail: [github-and-git-basics.md](./github-and-git-basics.md).

---

## 8. Continuous Integration With GitHub Actions

### 8.1 What CI Does In This Repo

Section 1 explains **why** a runner exists and what "CI" means in this course. Here is **what happens** when CI runs.

When you push to `main` or open a pull request targeting `main`, GitHub:

1. Starts a **runner** (temporary Ubuntu VM)
2. Clones your repo onto it
3. Runs `make install`, `make train`, `make eval`
4. Destroys the VM

This is **validation and reporting on a clean machine**, not deployment to users (Section 10). Software installed during the job lives **only on that runner**. Training outputs are not committed to the repo; CML shows metrics in a comment instead.

See Section 7.5 for what “pull request targeting `main`” means and when to use a PR vs a direct push.

### 8.2 Push Vs Pull Request (Two CI Entry Points)

The `on:` block in `ci.yml` lists **triggers**. Both are intentional:

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

| Trigger | Plain meaning | Typical use |
|---------|---------------|-------------|
| `push` to `main` | CI runs on commits already on `main` | After merge, or solo direct push |
| `pull_request` to `main` | CI runs on the **proposed** merge (PR branch vs `main`) | Review before merge |

Neither trigger blocks the other. Having both means:

- **PR workflow:** open PR → CI runs → merge if green → `push` to `main` runs CI again on the merged result
- **Direct push workflow:** `git push origin main` → CI runs once on whatever you pushed

The workflow file does not force PRs. Requiring PRs before updates to `main` is a **repository policy** (branch protection), not something `ci.yml` alone enforces.

### 8.3 The Workflow File

Workflows live in `.github/workflows/`. Ours is [ci.yml](../.github/workflows/ci.yml):

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

### 8.4 Read The YAML As A Student

| Block | What it teaches |
|-------|-----------------|
| `on: push / pull_request` | **Triggers:** CI on direct pushes to `main` and on PRs whose base is `main` (Section 8.2) |
| `workflow_dispatch` | Manual "Run workflow" button in GitHub UI |
| `permissions` | Limits what the job token may do (`pull-requests: write` lets CML post comments; we avoid broad `write-all`) |
| `runs-on: ubuntu-latest` | **Runner OS:** clean Linux each time |
| `actions/checkout@v4` | Copy repo files onto the runner |
| `setup-python@v5` | Install Python 3.13 (match your local env) |
| `iterative/setup-cml@v3` | Install `cml` CLI on the runner |
| `run: make …` | Same Makefile targets you use locally |
| `REPO_TOKEN: ${{ secrets.GITHUB_TOKEN }}` | Token CML uses to post the report |

Line-by-line reference: [github-actions-ci-yml.md](./github-actions-ci-yml.md).

### 8.5 What CML Does (`make eval`)

The `eval` target in [Makefile](../Makefile):

1. Writes `report.md` from `results/metrics.json` and embeds the confusion matrix image path
2. Runs `cml comment create report.md`

That command posts the report as a **comment** on the commit or pull request. It is **not** `git commit`. `report.md` does not enter the repo unless you commit it yourself.

CML uploads/displays the plot **inside the comment** on GitHub's website. Reviewers see metrics without opening Actions logs.

More on runners and CML: [github-actions-and-cml.md](./github-actions-and-cml.md).

### 8.6 Push The Workflow And Verify

```bash
git add .github/workflows/ci.yml
git commit -m "Add CI workflow"
git push origin main
```

Then open **GitHub → Actions → Continuous Integration → latest run**.

- **Green:** open the commit or PR; look for a bot **comment** with metrics and the plot
- **Red:** open the failed step log (missing deps, missing `data/drug.csv`, training error, or CML permissions)

We omit `make format` from CI initially so formatting does not block learning CI. Add a separate lint job later if you want.

---

## 9. Hugging Face Space (Deployment Target)

After CI proves training works, you expose a **demo** for others to try inputs and see predictions.

| Platform | Purpose in this course |
|----------|------------------------|
| **GitHub** | Source code + CI |
| **Hugging Face Space** | Hosted Gradio UI + model files for public demo |

Steps when you are ready:

1. Create a Space at [huggingface.co/spaces](https://huggingface.co/spaces), SDK: **Gradio**
2. Configure [app/README.md](../app/README.md) (YAML front matter: `app_file`, `sdk_version`, etc.)
3. Implement [app/drug_app.py](../app/drug_app.py) to load `model/model.skops` and call `pipe.predict()`

`colorFrom` / `colorTo` in `app/README.md` style the **Space card** on huggingface.co, not the Gradio widgets inside the app.

No S3-style bucket mount is required here; you upload files into the Space repo with the Hugging Face CLI.

Setup Q&A: [setup-notes.md](./setup-notes.md).

---

## 10. Continuous Deployment (Phase 2)

Do CD **only after** CI is green and the Gradio app works locally.

### 10.1 Idea

```text
CI succeeds on main
        │
        ▼
CD workflow runs
        ├── checkout
        ├── huggingface-cli login (HF token secret)
        └── upload app/ + model/ to your Space
```

CD automates what you would otherwise do manually: log in to Hugging Face and upload the app and model.

### 10.2 Secrets

GitHub repo → **Settings → Secrets and variables → Actions**:

| Secret | Purpose |
|--------|---------|
| `HF` | Hugging Face write token for upload |
| `USER_NAME`, `USER_EMAIL` | Only if a workflow commits back to git |

Never commit tokens in `ci.yml` or the Makefile; reference `${{ secrets.HF }}`.

### 10.3 Makefile Deploy Targets (Add When Ready)

```makefile
hf-login:
	pip install -U "huggingface_hub[cli]"
	huggingface-cli login --token $(HF) --add-to-git-credential

push-hub:
	huggingface-cli upload YOUR_USER/YOUR_SPACE ./app --repo-type=space
	huggingface-cli upload YOUR_USER/YOUR_SPACE ./model /model --repo-type=space
	huggingface-cli upload YOUR_USER/YOUR_SPACE ./results /metrics --repo-type=space

deploy: hf-login push-hub
```

Replace `YOUR_USER/YOUR_SPACE` with your Space id. Run as `make deploy HF=hf_xxx`.

### 10.4 CD Workflow Sketch

Create `.github/workflows/cd.yml` triggered after CI succeeds:

```yaml
name: Continuous Deployment

on:
  workflow_run:
    workflows: [Continuous Integration]
    types: [completed]
  workflow_dispatch:

jobs:
  deploy:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: make train
      - name: Deploy to Hugging Face
        env:
          HF: ${{ secrets.HF }}
        run: make deploy HF=$HF
```

This example retrains in CD for simplicity. A production team might pass **artifacts** from CI instead of training twice; that is optional for this course.

---

## 11. How This Repo Differs From DataCamp

| DataCamp | This tutorial |
|----------|---------------|
| `git commit -am` on first push | `git add .` then commit (tracks new files) |
| `permissions: write-all` | Minimal permissions for CML comments |
| No explicit `setup-python` | Python 3.13 pinned on the runner |
| Separate imputer + scaler in `ColumnTransformer` | Nested `Pipeline` (correct order) |
| `OrdinalEncoder` on all categoricals | One-hot + explicit ordinal categories |
| Vague Space README step | Configure `app/README.md`, upload via CLI |
| HF framed as "production" | HF = demo; AWS/GCP for real production |
| CI/CD ordering unclear | CI first, CD second |

---

## 12. Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| CI: module not found | Missing entry in [requirements.txt](../requirements.txt) |
| CI: `data/drug.csv` missing | File not committed or not downloaded in workflow |
| CI: `cml` not found | Missing `iterative/setup-cml` step |
| No comment on GitHub | Check `REPO_TOKEN`, `permissions`, `make eval` logs |
| `make eval` fails locally | Expected without GitHub token/context; CI is the main environment for CML |
| `make` says `missing separator` | Recipe lines must start with **Tab**, not spaces |

---

## 13. Next Steps

- Finish [app/drug_app.py](../app/drug_app.py) and test locally
- Add CD workflow + `HF` secret (Section 10)
- Optional: CI job for `make format`
- Optional: DVC for data at scale ([data-in-git-dvc-lfs.md](./data-in-git-dvc-lfs.md))

---

## Quick Reference

```bash
# local
make install && make train && make eval   # eval needs CML + token locally

# git
git add .
git commit -m "message"
git push origin main

# watch CI
# GitHub → Actions → latest run
```

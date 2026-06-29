# CI/CD For Machine Learning (Student Tutorial)

A step-by-step guide to build a drug-classification pipeline with **GitHub Actions** (CI) and **Hugging Face Spaces** (demo deployment). Written for this repo; fixes unclear or incorrect parts of the [DataCamp tutorial](https://www.datacamp.com/tr/tutorial/ci-cd-for-machine-learning).

**How to use this doc:** work through the sections **in order**. Do not skip to GitHub Actions until `make train` works locally.

**Appendix docs** (optional deep dives): [docs/README.md](./README.md)

---

## 0. What You Will Build

```text
You push code to GitHub
        │
        ▼
GitHub Actions (temporary Linux VM)
        ├── install Python deps
        ├── train model (train.py)
        └── post metrics + confusion matrix as a GitHub COMMENT (CML)
        │
        ▼ (later section)
Hugging Face Space runs your Gradio app with the trained model
```


| Piece                  | Role                                            |
| ---------------------- | ----------------------------------------------- |
| **GitHub repo**        | Stores code, data (small CSV), workflows        |
| **GitHub Actions**     | Runs training on every push/PR                  |
| **CML**                | Publishes results as a comment on the commit/PR |
| **Hugging Face Space** | Public demo UI (not production AWS/GCP)         |


---

## 1. Prerequisites

- GitHub account and a new empty repo (or this fork)
- Python 3.13 (conda recommended): `conda create -n ci-cd-for-ml python=3.13 -y`
- Kaggle account (for the dataset)
- Later: Hugging Face account (for deployment)

---

## 2. Project Layout

Use **lowercase** folder names (Linux paths are case-sensitive):

```text
CI-CD-for-ML/
├── .github/workflows/ci.yml   # CI workflow (Section 8)
├── app/                       # Gradio app + Space README (Section 10)
├── data/drug.csv              # training data (Section 3)
├── docs/                      # student documentation
├── model/                     # trained pipeline (generated, gitignored or on update branch)
├── results/                   # metrics + plots (generated)
├── Makefile                   # commands for you and for CI
├── requirements.txt           # Python deps for training + CML
├── train.py                   # training script (Section 5)
└── README.md
```

---

## 3. Get The Data

Dataset: [Drug Classification on Kaggle](https://www.kaggle.com/datasets/prathamtripathi/drug-classification) (`drug200.csv`).

```bash
pip install kaggle
# Kaggle → Settings → API → Create New Token → save as ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json

kaggle datasets download -d prathamtripathi/drug-classification -p data --unzip
mv data/drug200.csv data/drug.csv
```

**Small demo data:** committing `data/drug.csv` to GitHub is acceptable here. For large or licensed data, use download-in-CI or DVC; see [data-in-git-dvc-lfs.md](./data-in-git-dvc-lfs.md).

---

## 4. Train Locally First

CI will fail if training fails locally. Run:

```bash
conda activate ci-cd-for-ml
pip install -r requirements.txt
python train.py
```

Expected outputs:

- `results/metrics.json`
- `results/confusion_matrix.png`
- `model/model.skops`

### Preprocessing (Do Not Copy DataCamp Blindly)

Use a single sklearn **Pipeline** (preprocessing + model). Save the **whole pipeline** with skops so the app only calls `pipe.predict()`.

Correct patterns used in [train.py](../train.py):

- **One-hot** for nominal columns (`Sex`)
- **Ordinal** with explicit `categories=` for `BP`, `Cholesterol`
- **Imputer → scaler** in a nested `Pipeline` for numeric columns (not separate ColumnTransformer steps)

Details: [ml-preprocessing-and-models.md](./ml-preprocessing-and-models.md)

---

## 5. Makefile: Command Menu For You And CI

A Makefile is **not** a script you run directly. You run `**make <target>`**; `make` reads [Makefile](../Makefile) and executes shell commands.


| Target         | Purpose                           |
| -------------- | --------------------------------- |
| `make install` | `pip install -r requirements.txt` |
| `make train`   | `python train.py`                 |
| `make eval`    | Build `report.md`, post via CML   |


Optional locally: `make format` (needs `black` in requirements).

Intro: [makefile-tutorial-brief.md](./makefile-tutorial-brief.md)

---

## 6. requirements.txt

Training and CI need pinned dependencies. This repo uses:

```text
pandas
matplotlib
scikit-learn
black
skops
cml
```

- **skops**: save/load full pipeline for the Gradio app
- **cml**: can be installed via pip *or* by the `setup-cml` Action (we use both approaches: Action installs CLI; pip keeps local runs consistent)

---

## 7. First Git Commit (Correct Way)

**Do not** use `git commit -am` alone for the first push with new files. `-a` only stages **changes to already tracked files**, not new files.

```bash
git add .
git status          # review what will be committed
git commit -m "Add training pipeline, Makefile, and data"
git push origin main
```

Later, when editing **existing** tracked files only: `git commit -am "message"` is fine.

Explanation: [github-and-git-basics.md](./github-and-git-basics.md)

---

## 8. GitHub Actions: Continuous Integration

### 8.1 What Is Happening?

On push/PR, GitHub starts a **temporary virtual machine** (runner), copies your repo, runs your Makefile steps, then deletes the VM.

Installing tools “in CI” means installing on **that VM for one job**, not into your repo files.

### 8.2 Create The Workflow File

Create `[.github/workflows/ci.yml](../.github/workflows/ci.yml)` with this content (already in this repo if you cloned latest):

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

### 8.3 Walkthrough: Each Part


| Section                                   | Purpose                                                                          |
| ----------------------------------------- | -------------------------------------------------------------------------------- |
| `on: push / pull_request`                 | When to run CI                                                                   |
| `permissions`                             | CML needs `pull-requests: write` to post comments. Avoid tutorial’s `write-all`. |
| `runs-on: ubuntu-latest`                  | Linux runner VM                                                                  |
| `actions/checkout@v4`                     | Clone repo onto runner                                                           |
| `setup-python@v5`                         | Install Python 3.13 explicitly                                                   |
| `iterative/setup-cml@v3`                  | Install `cml` CLI on runner                                                      |
| `make install / train / eval`             | Same commands you run locally                                                    |
| `REPO_TOKEN: ${{ secrets.GITHUB_TOKEN }}` | Lets CML post the report to GitHub                                               |


### 8.4 What `make eval` / CML Does

1. Builds `report.md` from `results/metrics.json` and the confusion matrix image.
2. Runs `cml comment create report.md` → posts a **GitHub comment** on the commit/PR.

This is **not** a git commit. The report is not added to the repo unless you commit it yourself.

### 8.5 Push And Verify

```bash
git add .github/workflows/ci.yml
git commit -m "Add CI workflow"
git push origin main
```

Then: GitHub → **Actions** tab → open the workflow run.

- Green: open the commit → look for a **comment** with metrics and plot.
- Red: read the failed step log (usually missing deps, missing `data/drug.csv`, or train error).

We **omit `make format` from CI** initially so formatting does not block learning CI. Add it as a separate job later if you want.

---

## 9. Hugging Face Space (Deployment Target)

GitHub = code + automation. Hugging Face Space = **live demo** (Gradio UI).

1. Create a Space at [huggingface.co/spaces](https://huggingface.co/spaces), SDK: **Gradio**.
2. Configure [app/README.md](../app/README.md) (YAML front matter: `app_file`, `sdk_version`, etc.).
3. Implement [app/drug_app.py](../app/drug_app.py) to load `model/model.skops` and expose `predict`.

`colorFrom` / `colorTo` in `app/README.md` only style the **Space card** on huggingface.co, not the app UI.

No bucket mount required for this project; files are uploaded into the Space repo.

Setup Q&A: [setup-notes.md](./setup-notes.md)

---

## 10. Continuous Deployment (Phase 2)

Do this **only after CI is green** and the Gradio app works locally.

### 10.1 Pattern

```text
CI completes on main
        │
        ▼
CD workflow runs
        ├── checkout (optionally branch with model artifacts)
        ├── huggingface-cli login (HF token secret)
        └── upload app/ + model/ to your Space
```

### 10.2 Secrets

GitHub repo → **Settings → Secrets and variables → Actions**:


| Secret                    | Purpose                                |
| ------------------------- | -------------------------------------- |
| `HF`                      | Hugging Face write token               |
| `USER_NAME`, `USER_EMAIL` | Only if a workflow commits back to git |


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

Replace `YOUR_USER/YOUR_SPACE` with your Space id.

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

This example retrains in CD for simplicity. A cleaner production pattern is to pass **artifacts** from CI to CD; that is optional for this course.

---

## 11. What We Do Differently From DataCamp


| DataCamp                                       | This tutorial                                   |
| ---------------------------------------------- | ----------------------------------------------- |
| `git commit -am` on first push                 | `git add .` then commit                         |
| `permissions: write-all`                       | Minimal permissions for CML                     |
| No `setup-python`                              | Explicit Python 3.13                            |
| Separate imputer + scaler in ColumnTransformer | Nested Pipeline (correct order)                 |
| OrdinalEncoder on all categoricals             | One-hot + explicit ordinal categories           |
| Vague Space README step                        | Configure local `app/README.md`, upload via CLI |
| HF = “real world deployment”                   | HF = demo; AWS/GCP for production               |
| `update` branch without clear git story        | CI first; CD second; artifacts optional         |


---

## 12. Troubleshooting


| Symptom                                 | Fix                                                                            |
| --------------------------------------- | ------------------------------------------------------------------------------ |
| CI: module not found                    | Check [requirements.txt](../requirements.txt)                                  |
| CI: `data/drug.csv` missing             | Commit data or download in workflow                                            |
| CI: `cml` not found                     | Ensure `iterative/setup-cml` step exists                                       |
| No comment on GitHub                    | Check `REPO_TOKEN`, permissions, eval step logs                                |
| `make eval` works locally but not in CI | CML needs token + GitHub context; local eval may fail without token (expected) |


---

## 13. Next Steps

- Finish `app/drug_app.py` and test locally
- Add CD workflow + `HF` secret
- Optional: add `make format` as a separate CI job
- Optional: DVC for data ([data-in-git-dvc-lfs.md](./data-in-git-dvc-lfs.md))

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


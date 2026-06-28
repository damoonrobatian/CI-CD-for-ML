# Data In Git, Git LFS, And DVC

How to handle datasets and model files in ML projects — and why the DataCamp tutorial commits a small CSV to GitHub.

---

## Why The Tutorial Puts Data In The Repo

The beginner tutorial uses **only GitHub Actions**. CI needs training data after `git checkout`. The simplest approach:

1. Put `drug.csv` in `data/`
2. Commit and push to GitHub
3. `train.py` reads `data/drug.csv` on the runner

The reference project does this: a ~6 KB, ~200-row file. When the tutorial says *“retrain when data or code changes”*, it means **you change the CSV in the repo and push**.

That is a **teaching shortcut**, not how most production ML teams store data.

| Why it works here | Why it does not scale |
|-------------------|------------------------|
| Tiny file | Large datasets bloat git history |
| Static demo data | Data changes often |
| No extra tools to learn | Kaggle license may forbid redistributing CSV in a public repo |
| CI works out of the box | Git is for code, not data lakes |

---

## Four Approaches (Overview)

| Approach | What lives in Git | What lives elsewhere | Best when |
|----------|-------------------|----------------------|-----------|
| **Plain Git** | Code + data files | Nothing | Tiny, static, public demo data (this tutorial) |
| **Git + download in CI** | Code only | Data fetched at build time (Kaggle API, URL, script) | Medium data, private credentials, no DVC yet |
| **Git LFS** | Code + small pointer files | Large blobs on LFS server | A few large binaries, still “git-like” workflow |
| **DVC** | Code + `.dvc` pointers + `dvc.yaml` pipeline | Data/models on S3, GCS, Azure, SSH, etc. | Real ML projects, reproducible pipelines, team data versioning |

---

## Plain Git (What This Tutorial Does)

**How it works:** `data/drug.csv` is a normal tracked file, like `train.py`.

**Appropriate when:**

- File is **small** (kilobytes to low megabytes)
- Data **rarely changes**
- You accept data in repo history (every change is a permanent commit)
- Learning CI/CD without storage infrastructure

**Not appropriate when:**

- Dataset is large (hundreds of MB+)
- Data updates frequently
- License forbids publishing the raw data
- You need strict separation between code repo and data store

**CI pattern:**

```yaml
- uses: actions/checkout@v4
- run: make train   # data/ already in the checkout
```

---

## Git LFS (Large File Storage)

**What it is:** A Git extension. Git stores a **small pointer** in the repo; the **real file** lives on an LFS server (GitHub LFS, GitLab LFS, etc.).

**How it feels:**

```text
git add model.bin     → pointer in git, blob on LFS
git clone             → fetches pointers; LFS pulls large files
```

**Appropriate when:**

- You have **a few large files** (models, checkpoints, medium datasets)
- Team already works in Git and wants minimal new tooling
- Files change occasionally, not at data-lake scale

**Not appropriate when:**

- You need ML **pipeline** semantics (stages, dependencies, `repro`)
- Many large files with complex versioning across remotes
- You want data in S3/GCS with flexible access outside Git hosts
- LFS bandwidth/storage quotas are a concern (hosting limits apply)

**Limits:** LFS fixes “Git is bad at big blobs.” It does **not** replace a full ML data workflow (DVC, feature stores, etc.).

---

## DVC (Data Version Control)

**What it is:** A tool ([dvc.org](https://dvc.org)) for versioning **data and models** separately from code, with optional **pipeline** definitions (`dvc.yaml`) and remotes (S3, GCS, Azure, local, SSH).

**How it feels:**

```text
Git repo     → code, dvc.yaml, small *.dvc pointer files
DVC remote   → actual CSVs, models, metrics (large artifacts)

dvc add data/drug.csv    → tracks file, adds drug.csv.dvc to git
dvc push                 → uploads data to configured remote
dvc pull                 → downloads data for training/CI
dvc repro                → rerun pipeline stages when inputs change
```

**Appropriate when:**

- Datasets or models are **large** or **change often**
- You need **reproducible pipelines** (which steps rerun when data changes)
- Data lives in **cloud storage** (S3, GCS, Azure) or shared team storage
- CI should run `dvc pull` then train, not store data in GitHub
- You want the full DataCamp **course** path (DVC + GitHub Actions + CML)

**Not appropriate when:**

- Project is a one-off tutorial with a 6 KB CSV (overkill)
- Team has no remote storage and no appetite for extra tooling
- You only need one static file and plain Git is enough

**CI pattern (typical):**

```yaml
- uses: actions/checkout@v4
- run: pip install dvc dvc-s3   # or dvc-gs, etc.
- run: dvc pull                 # needs credentials in secrets
- run: make train
```

DVC is from the same ecosystem as **CML** (used in our Makefile `eval` target).

---

## Choosing An Approach (Decision Guide)

```text
Is the data tiny (< ~10 MB) and rarely changes?
  └─ Yes → Plain Git (tutorial) OR download in CI if license forbids committing
  └─ No ↓

Do you only need Git to track a few large binaries, not a full ML pipeline?
  └─ Yes → Consider Git LFS
  └─ No ↓

Do you need cloud remotes, pipeline stages, and proper data versioning?
  └─ Yes → DVC (or platform tools: SageMaker, Vertex, W&B Artifacts, etc.)
```

---

## This Repo Vs A Production Setup

| | **This tutorial / repo** | **Typical production** |
|---|--------------------------|-------------------------|
| Data | `data/drug.csv` in git (or local only + download) | S3/GCS + DVC, or warehouse/API |
| Models after train | `model/model.skops` committed or uploaded to HF | Artifact registry, model store |
| CI | Checkout repo → train | Checkout → `dvc pull` / fetch data → train → register model |
| Tutorial scope | GitHub Actions, Makefile, CML, HF only | + DVC, cloud, monitoring, etc. |

For learning CI/CD mechanics, plain Git (or gitignore + Kaggle download in CI) is enough. Adopt **LFS** or **DVC** when file size, update frequency, or team workflow outgrow that.

---

## Related Docs

- [setup-notes.md](./setup-notes.md) — Kaggle download, project Q&A
- DataCamp **course** (not this tutorial): [CI/CD for Machine Learning](https://www.datacamp.com/courses/cicd-for-machine-learning) — covers DVC in depth

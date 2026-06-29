# Git And GitHub Basics For This Project

Plain answers about git commands used in the tutorial, especially `git add`, `git commit -am`, and what “tracked” means.

---

## GitHub Is Two Things

| Part | What it does |
|------|----------------|
| **Git repo** | Stores your files and history (like a shared folder with undo) |
| **GitHub website** | Shows the repo, PRs, **comments**, and runs **Actions** (CI) |

Pushing code updates the **repo**. CML posts a **comment** on the website. Those are different (see [github-actions-and-cml.md](./github-actions-and-cml.md)).

---

## Three States Every File Can Be In

| State | Meaning |
|-------|---------|
| **Untracked** | Git has never been told about this file |
| **Tracked** | Git knows the file (it was committed or you ran `git add`) |
| **Staged** | A tracked change is **ready for the next commit** (`git add`) |

**Tracked ≠ staged.** You can edit a tracked file without staging it yet.

### Commands To Inspect

```bash
git status -sb       # staged, modified, untracked
git ls-files         # everything staged for next commit
git ls-tree -r HEAD  # everything in the last commit
```

---

## What Was In This Repo At Different Stages

**After `Initial commit` on GitHub:** only `.gitignore` and `README.md` were tracked.

**After you build the project locally:** new files (`train.py`, `Makefile`, `data/drug.csv`, …) start as **untracked**.

**After `git add .`:** they become **staged** (ready to commit).

**After `git commit` + `git push`:** they become **tracked on GitHub**.

---

## `git add`: Tell Git To Include Files

```bash
git add .              # stage all new/changed files (respects .gitignore)
git add train.py       # stage one file
```

**Required for new files.** Git will not commit untracked files unless you `add` them first.

---

## `git commit -am "message"`: What The Flags Mean

```bash
git commit -am "new changes"
```

| Flag | Meaning |
|------|---------|
| **`-m "..."`** | Commit message (avoids opening an editor) |
| **`-a`** | Auto-stage **modifications and deletions** to files Git **already tracks** |

**`-a` does not add brand-new files.** It skips `git add` only for **edits to existing tracked files**.

Same as:

```bash
git add -u                    # stage updates to tracked files only
git commit -m "new changes"
```

---

## Why The Tutorial Shows `commit -am` Without `git add`

The tutorial text says “add the changes” but shows only:

```bash
git commit -am "new changes"
git push origin main
```

That is **misleading for a first push** with many **new** files. `-a` will **not** stage `train.py`, `Makefile`, `data/drug.csv`, etc. if they were never committed before.

**First push with a new project: use**

```bash
git add .
git commit -m "Add training pipeline and CI files"
git push origin main
```

**Later**, when you only **edit** files already on GitHub:

```bash
git commit -am "Update train.py"
git push origin main
```

---

## What `.gitignore` Does

Files matching [`.gitignore`](../.gitignore) (e.g. `.venv/`, `__pycache__/`) are **ignored**; Git will not track them unless you force-add.

This repo does **not** ignore `data/`, `model/`, or `results/`, so those **can** be committed if you choose to.

---

## Quick Reference

| Situation | Command |
|-----------|---------|
| First commit with new files | `git add .` then `git commit -m "..."` |
| Edit existing tracked files | `git commit -am "..."` OK |
| See what will be committed | `git status` |
| New file never added | **Not** included by `-a`; need `git add` |

---

**See also:** [data-in-git-dvc-lfs.md](./data-in-git-dvc-lfs.md) (committing data), [github-actions-and-cml.md](./github-actions-and-cml.md) (CI on push)

# Student Documentation

Documentation for learning **CI/CD for machine learning**: Makefiles, GitHub Actions, CML reports, and Hugging Face Spaces deployment. This repo runs a small scikit-learn training script on a sample CSV so you have something real to train, test, and deploy. **The focus is the automation workflow**, not drug classification or model tuning.

Based on the [DataCamp CI/CD for ML tutorial](https://www.datacamp.com/tr/tutorial/ci-cd-for-machine-learning), with clearer steps and corrected preprocessing. Use the appendix files below when you want extra detail on one topic.

## Start Here

**Main tutorial (follow in order):** [tutorial.md](./tutorial.md)

Work through that document step by step. It includes GitHub Actions setup as Section 8; no separate workflow doc required.

---

## Appendix: Deep Dives And Q&A

Use these when you want more detail on a specific question:

| Document | Topic |
|----------|--------|
| [setup-notes.md](./setup-notes.md) | HF Spaces, licenses, Kaggle, skops, Space card |
| [makefile-tutorial-brief.md](./makefile-tutorial-brief.md) | Makefile quick reference |
| [makefile-tutorial.md](./makefile-tutorial.md) | Makefile full guide |
| [github-and-git-basics.md](./github-and-git-basics.md) | Tracked files, `git add`, `-am` |
| [github-actions-ci-yml.md](./github-actions-ci-yml.md) | `ci.yml` workflow deep dive |
| [github-actions-and-cml.md](./github-actions-and-cml.md) | Runners, CML comments (expanded) |
| [ml-preprocessing-and-models.md](./ml-preprocessing-and-models.md) | Encoders, ColumnTransformer |
| [data-in-git-dvc-lfs.md](./data-in-git-dvc-lfs.md) | Data in git, DVC, LFS |

---

## Topic Finder

| Question | Where |
|----------|--------|
| Full CI/CD walkthrough | [tutorial.md](./tutorial.md) |
| Do I need HF bucket mount? | [setup-notes.md](./setup-notes.md) |
| What is `make train`? | [tutorial.md §5](./tutorial.md) · [makefile-tutorial-brief.md](./makefile-tutorial-brief.md) |
| Notebook vs `train.py`? | [tutorial.md §4](./tutorial.md) · [experiments.ipynb](../experiments.ipynb) |
| What is in `ci.yml`? | [github-actions-ci-yml.md](./github-actions-ci-yml.md) · [tutorial.md §8](./tutorial.md) |
| What is an Actions runner? | [tutorial.md §8](./tutorial.md) · [github-actions-and-cml.md](./github-actions-and-cml.md) |
| Why not DataCamp’s git `-am`? | [tutorial.md §7](./tutorial.md) |

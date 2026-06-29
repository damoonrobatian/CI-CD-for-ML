# Setup Notes (From Project Q&A)

Brief answers to questions raised while working through the DataCamp CI/CD for ML tutorial.

**Full doc index:** [docs/README.md](./README.md)

---

## DataCamp Tutorial Access

- `https://app.datacamp.com/learn/tutorials/ci-cd-for-machine-learning` requires a DataCamp login; the interactive app area is not accessible without an account.
- The same tutorial is public at [A Beginner's Guide to CI/CD for Machine Learning](https://www.datacamp.com/tr/tutorial/ci-cd-for-machine-learning).

## Hugging Face Space: Bucket Mount?

**No.** This tutorial does not use mounted buckets or persistent storage. Deployment uploads files directly into the Space repo via `huggingface-cli upload` (`app/`, `model/`, `results/`). The Gradio app loads the model from a local path inside the Space (e.g. `./model/drug_pipeline.skops`).

## License

- **Not required** for CI/CD or for the app to run.
- HF Space creation offers an **optional** license field (not enforced).
- `license: apache-2.0` in `app/README.md` is metadata for the Hub, not a runtime requirement.
- **What licenses are:** legal rules for how others may reuse your code. **Why use one:** clarity for sharing, Hub display/filtering, and common “no warranty” protection. Optional for a learning project; Apache 2.0 or MIT are common if you add one.

## HF CLI Skill Tip (“Install The Official HF CLI Skill…”)

Optional add-on for AI coding assistants (Cursor, etc.). A “Skill” teaches the agent how to run `hf` commands (manage Spaces, upload, logs, secrets). **Not needed** for this tutorial, which uses GitHub Actions + `huggingface-cli upload` in a Makefile.

## GitHub Vs Hugging Face

Both use Git repos, but different roles in this project:

| | GitHub | Hugging Face Space |
|---|--------|-------------------|
| Role | Source code + CI/CD (train, evaluate) | Host the live Gradio demo |
| Who uses it | You, GitHub Actions | End users in a browser |

Flow: push to GitHub → Actions train/evaluate → CD uploads app + model to HF → Space runs the UI.

Production deployments usually target AWS/GCP/Azure, not HF Spaces. HF here is a simple demo host for learning CI/CD mechanics, not typical enterprise deployment.

## Tutorial Step: Edit Space README (“Make The Necessary Changes”)

That step is vague. HF auto-generates a `README.md` with YAML metadata when you create a Space. In practice:

- Step 3 is mostly “find the file under Files.”
- The real config lives in **`app/README.md`** locally (uploaded to the Space later by CI/CD).
- You can skip editing the Space README on huggingface.co initially; your local `app/` upload replaces it.

## Where Is `app/README.md`?

In this repo: `app/README.md` (alongside `drug_app.py` and `requirements.txt`). It is **not** the root `README.md`. Root README describes the GitHub project; `app/README.md` configures the Hugging Face Space.

## Folder Naming: `App` Vs `app`

The tutorial uses capitalized `App`, `Data`, `Model`, `Results` with hardcoded paths. That is **not** typical Python convention (lowercase is standard: `app/`, `data/`, `model/`, `results/`).

This repo uses **lowercase** folders. Update every path in scripts, Makefile, and workflows to match (Linux paths are case-sensitive).

## `app/README.md` YAML Fields

The `---` block at the top is **Space configuration**, not normal readme prose.

| Field | Purpose |
|-------|---------|
| `title` | Display name on the Space page |
| `emoji` | Icon on the Space card |
| `colorFrom`, `colorTo` | Gradient on the **Space card** thumbnail only (Hub listing) |
| `sdk` | Runtime type (`gradio`) |
| `sdk_version` | Gradio version HF installs |
| `app_file` | Entry script (e.g. `drug_app.py`); must match your file |
| `pinned` | Pin Space to top of your profile |
| `license` | Optional Hub metadata |

**Important:** `colorFrom` / `colorTo` do **not** style the Gradio app UI (that is done in Python, e.g. `gr.themes.Soft()`). Allowed colors: `red`, `yellow`, `green`, `blue`, `indigo`, `purple`, `pink`, `gray`.

## What Is A Space Card?

The small preview tile on huggingface.co (profile, search, browse): emoji, title, and gradient background. Clicking it opens the full running app. Card styling ≠ in-app UI.

## Downloading The Kaggle Dataset

Dataset: [Drug Classification](https://www.kaggle.com/datasets/prathamtripathi/drug-classification) (`drug200.csv`).

**Browser:** log in → Download → unzip → place in `data/` and rename to `drug.csv` (tutorial code expects `drug.csv`, not `drug200.csv`).

**CLI:**

```bash
pip install kaggle
# Kaggle → Settings → API → Create New Token → save as ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json

kaggle datasets download -d prathamtripathi/drug-classification -p data --unzip
mv data/drug200.csv data/drug.csv
```

Never commit `kaggle.json` to the repo.

For why the tutorial commits data to GitHub, and when to use **Git LFS** or **DVC** instead, see [data-in-git-dvc-lfs.md](./data-in-git-dvc-lfs.md).

## Pickle, Joblib, And Skops (Model Saving)

The tutorial saves the trained sklearn `Pipeline` with **skops** instead of **pickle** or **joblib**. All three solve the same basic problem: write a Python object to disk and load it back later. The difference is mainly **how loading works**, not model accuracy.

### What Each Tool Does

| Tool | Typical use | How it saves |
|------|-------------|--------------|
| **pickle** | Generic Python objects | Python’s built-in serialization |
| **joblib** | sklearn models (common default) | Same underlying idea as pickle, optimized for numpy arrays |
| **skops** | sklearn models (sharing / deployment) | Custom format designed for sklearn; avoids blind pickle loading |

In this project, all three could save the same pipeline (preprocessing + `RandomForestClassifier`). Loading any of them gives you back an object you can call `.predict()` on.

```python
# joblib (sklearn's usual local default)
import joblib
joblib.dump(pipe, "model/drug_pipeline.joblib")
pipe = joblib.load("model/drug_pipeline.joblib")

# skops (tutorial + this repo)
import skops.io as sio
sio.dump(pipe, "model/drug_pipeline.skops")
pipe = sio.load("model/drug_pipeline.skops", trusted=...)  # see skops docs for trusted=
```

### What “Pickle Can Run Arbitrary Code” Means (Plain Language)

When you **load** a pickle/joblib file, Python does not just read numbers. It **follows instructions inside the file** to rebuild objects. Those instructions can, in principle, tell Python to run **any code**, not only “create a RandomForest.”

A **normal** model file: “rebuild this sklearn pipeline.”

A **malicious** model file: “read environment variables / delete files / run malware”, and that runs the moment someone calls `joblib.load()` or `pickle.load()`.

So the security issue is not “using pickle is always dangerous.” It is: **loading a file from a source you do not trust is like running a program you did not review.**

### When Security Actually Matters (Concrete Scenarios)

#### Low Risk: Pickle/Joblib Is Fine

These are the common cases in development and in **this tutorial** if you control the whole pipeline:

- You train on your laptop, save, and load the file **yourself** seconds later.
- Your CI trains the model, commits or uploads the artifact, and **only your workflows** produce that file.
- The model file lives in **your private repo**, only you can push to it, and you review what gets deployed.
- You never download someone else’s `.pkl` / `.joblib` from the internet and load it blindly.

For this drug-classifier project (your GitHub repo, your Actions, your HF Space), **the practical security gap between joblib and skops is small.** Either works if you trust your own pipeline.

#### Real Risk: Be Careful With Pickle/Joblib

Security starts to matter when **you load a model file you did not create or cannot verify**:

| Scenario | Why it is risky |
|----------|-----------------|
| Download a `model.pkl` from an unknown Hugging Face user, forum, or email attachment | The file may contain hidden malicious load instructions. |
| A **public repo accepts model uploads** from strangers (issues, PRs with binary artifacts) and CI auto-deploys them | An attacker could submit a malicious pickle; your server loads it on deploy. |
| **Account or repo compromise** (someone else replaces `model.joblib` in your repo or Space) | Your app still calls `load()` automatically; it will execute whatever is in the new file. |
| **Shared ML platform** where users upload models and the platform loads them for inference | Classic pickle attack surface; platforms often ban pickle or use sandboxing. |
| Running `joblib.load()` on artifacts from a **compromised CI cache** or untrusted third-party build | Same as loading any untrusted binary. |

Important nuance: **“Deployed on Hugging Face” alone does not make pickle dangerous.** What matters is whether **someone else could swap the model file** without you noticing. A solo learning project with no outside contributors is not that scenario.

#### Where Skops Helps

`skops` does not load arbitrary pickle blobs. It reads a structured file, lists which Python types are inside, and **only reconstructs them if you explicitly allow those types** (`trusted=...`). That adds a review step: “these are the types in this file; do I expect them?”

It is **not perfect security** (you can still approve bad types, or trust a library with bugs). It is **better than pickle when the file might be tampered with or come from an untrusted publisher.** sklearn’s [model persistence docs](https://scikit-learn.org/stable/model_persistence.html) recommend considering skops when sharing models.

### Why The Tutorial Uses Skops

Reasonable motivations:

- Saves the **full pipeline** (encoders + model), same as joblib.
- Aligns with **public model sharing** on Hugging Face (safer default when strangers might download your artifact).
- Matches current sklearn / Hub guidance for shared models.

Weakness of the tutorial: it never explains **why**; it only says “save with skops.”

### What To Use In This Repo

| Context | Suggestion |
|---------|------------|
| Notebook / local experiments only | **joblib** is simple and standard. |
| This CI/CD project (train in Actions → load in Space) | **skops** (tutorial) or **joblib**; both fine if you control GitHub and HF access. |
| Publishing models for others to download and run | Prefer **skops**; never ask strangers to `pickle.load()` your file. |
| Loading a random model from the internet | Inspect the source first; prefer skops or ONNX/safe formats; **never** `joblib.load()` an untrusted pickle. |

### Summary

- **pickle/joblib:** convenient, universal, fine for **your own** files.
- **skops:** same job for sklearn pipelines, with a **clearer trust boundary** when files are **shared, public, or might be tampered with**.
- **This tutorial:** security is a minor concern in practice; skops is a defensible modern choice, not a fix for an urgent local-only threat.

### Saving The Full Pipeline (Not Just The Model)

The tutorial says loading the file “works out of the box without processing your data in the app.” That refers to saving the **entire sklearn `Pipeline`** (preprocessors + classifier), not to skops being special:

- `pipe.predict(raw_features)` runs encoding/scaling inside the pipeline.
- **joblib** can save the same pipeline the same way; skops adds safer loading for **untrusted** files (see above).

Details: [ml-preprocessing-and-models.md](./ml-preprocessing-and-models.md).

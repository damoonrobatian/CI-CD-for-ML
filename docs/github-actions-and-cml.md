# GitHub Actions And CML

Plain answers: what an Actions runner is, what “install in CI” means, where CML lives, and what `cml comment create report.md` actually does.

---

## GitHub Is A Repo **And** A Robot

You store code on GitHub. **GitHub Actions** runs commands on a **temporary machine** when you push (if you have a workflow file in `.github/workflows/`).

```text
You push code  →  GitHub stores it in the repo
                →  Actions starts a job on a temporary VM
                →  VM runs: make install, make train, make eval
                →  VM is deleted
```

The repo is **storage**. The runner is a **short-lived computer** that copies your repo and runs your Makefile.

---

## What Is An “Actions Runner”?

A **runner** = a machine that executes workflow steps.

For `runs-on: ubuntu-latest`, GitHub assigns a **Linux virtual machine** in their cloud:

1. Checks out your repo (download a copy)
2. Runs each step in `ci.yml` / your Makefile
3. Discards the VM when the job finishes

It is **not** your laptop. It is **not** “inside” the git repo as a file.

---

## What “Install In CI” Means

**CI environment** = software installed on **that temporary runner** for one job.

Example from the tutorial workflow:

```yaml
- uses: iterative/setup-cml@v2   # installs `cml` on the runner
- run: make install                # pip installs from requirements.txt
- run: make train
- run: make eval
```

Those packages exist on the **runner’s disk for minutes**, then disappear. They are **not** automatically added to your repo files.

Your **conda env on your laptop** is a separate environment.

---

## Where Is CML Installed?

| Location | Installed? |
|----------|------------|
| **GitHub Actions runner** | Yes — via `iterative/setup-cml@v2` in `ci.yml` (tutorial) |
| **This repo’s `requirements.txt`** | Not by default — tutorial uses the Action, not `pip install cml` |
| **Your laptop** | Only if you run `pip install cml` yourself |

Locally, `make eval` will fail with “command not found” until CML is installed **and** configured with a GitHub token. The tutorial expects `eval` to run **in CI**.

---

## What Is CML?

**CML** (Continuous Machine Learning) — [cml.dev](https://cml.dev/) — tools from Iterative (same ecosystem as DVC) to report ML results on GitHub.

In this project it is used to **publish training metrics** where you can see them on the website (commit/PR), not only in Actions logs.

---

## The `eval` Target In Our Makefile

```makefile
eval:
	echo "## Model Metrics" > report.md
	cat ./results/metrics.json >> report.md
	echo "## Confusion Matrix Plot" >> report.md
	echo "![Confusion Matrix](./results/confusion_matrix.png)" >> report.md
	cml comment create report.md
```

**Steps 1–4:** Build a markdown file on the CI machine (metrics from `make train`).

**Step 5:** CML publishes that markdown.

---

## What `cml comment create report.md` Means

Decode the command:

```bash
cml comment create report.md
```

| Part | Meaning |
|------|---------|
| `cml` | Run the CML program |
| `comment` | Create a **GitHub comment** (a message on the website) — **not** a git commit |
| `create` | Make a new comment |
| `report.md` | **Input file** — CML reads this and uses it as the comment body |

Plain English: **“Post the contents of `report.md` as a GitHub discussion comment on this CI run.”**

Like `mail < letter.txt` — the command does not say “read,” but it reads the file as input.

---

## Comment Vs Commit — Do Not Mix Them Up

| | **Git commit** | **GitHub comment** |
|---|----------------|-------------------|
| What | Snapshot of repo files | Message on PR/commit page |
| Created by | `git commit` | CML / GitHub API |
| Contains | Tracked files you committed | Markdown text (and embedded images via CML) |
| Is `report.md` in the repo? | Only if **you** `git add` it | **No** — comment is separate from repo files |

The PNG is **not inside the git commit** because of CML. CML uploads/displays the image **inside the comment** on GitHub’s UI. Your commit still only has whatever you pushed with git.

---

## What The Workflow Needs For CML To Work

From the tutorial:

```yaml
permissions: write-all          # allow posting comments

- uses: iterative/setup-cml@v2

- name: Evaluation
  env:
    REPO_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: make eval
```

Without `setup-cml`, no `cml` command. Without `REPO_TOKEN` and write permission, CML cannot post.

---

## Full CI Flow (This Project)

```text
push to main
    │
    ▼
Actions runner (temporary Linux VM)
    │
    ├── checkout repo
    ├── setup-cml  (install cml)
    ├── make install
    ├── make train     → results/, model/
    └── make eval      → report.md → GitHub COMMENT (not a new commit)
```

---

**See also:** [makefile-tutorial-brief.md](./makefile-tutorial-brief.md), [github-and-git-basics.md](./github-and-git-basics.md)

# ML Preprocessing And Model Saving

Plain answers about sklearn pieces in this project, including where the tutorial oversimplifies or gets things wrong.

---

## What `ColumnTransformer` Does

`ColumnTransformer` applies **different preprocessing to different columns**, then **combines** the result into one matrix for the model.

Example from our [train.py](../train.py):

- **Ordinal** encoding for `BP`, `Cholesterol` (with explicit category order)
- **One-hot** encoding for `Sex` (nominal)
- **Impute + scale** for `Age`, `Na_to_K`

One object, one `.fit()` / `.predict()` path: same steps at training and inference.

---

## Why Not `OrdinalEncoder` On Everything? (Tutorial Issue)

The tutorial uses `OrdinalEncoder` on all categorical columns. That is a **shortcut**, not best practice.

| Column | Type | Better encoder |
|--------|------|----------------|
| `Sex` | Nominal (no order) | `OneHotEncoder` |
| `BP` | Ordinal (LOW < NORMAL < HIGH) | `OrdinalEncoder` with **explicit** `categories=[['LOW','NORMAL','HIGH']]` |
| `Cholesterol` | Debatable | One-hot or explicit ordinal |

Default `OrdinalEncoder()` uses **alphabetical** order (e.g. HIGH=0, LOW=1, NORMAL=2), which is wrong even for BP.

Random Forest tolerates this on a small dataset; **principle still matters** for learning and for linear models.

---

## Double Brackets In `categories=[['LOW', 'NORMAL', 'HIGH']]`

The outer list = one entry **per encoded column**.  
The inner list = allowed values **in order** for that column.

Two ordinal columns → two inner lists:

```python
categories=[
    ['LOW', 'NORMAL', 'HIGH'],   # BP
    ['NORMAL', 'HIGH'],          # Cholesterol
]
```

---

## What `handle_unknown='ignore'` Means (`OneHotEncoder`)

When **transform** sees a category that was **not in training data**:

- **`'error'`** (default): crash
- **`'ignore'`**: output all zeros for that column’s one-hot features (safer at inference)

Example: training only had `Sex` = M/F; at predict time someone sends an invalid value. With `'ignore'`, the model gets zeros instead of an exception.

`OrdinalEncoder` defaults to `'error'` for unknown categories unless you configure otherwise.

---

## Why Imputer + Scaler Are In A Nested `Pipeline`

**Correct pattern (this repo):**

```python
Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler()),
])
```

Imputation must run **before** scaling (scaler cannot handle NaN).

**Tutorial pattern (wrong):**

```python
ColumnTransformer([
    ('num_imputer', SimpleImputer(...), num_col),
    ('num_scaler', StandardScaler(), num_col),
])
```

`ColumnTransformer` steps run **in parallel** on the **original** columns; they do not chain. Result:

- Duplicate numeric columns (imputed unscaled + scaled originals)
- Scaler does not see imputed values
- With missing data, scaler can fail on NaN

It “works” on the clean drug dataset because there are no missing values and Random Forest is forgiving. See the demo cell in [experiments.ipynb](../experiments.ipynb).

---

## Saving The Full Pipeline (“Works Out Of The Box”)

The tutorial says loading the pipeline works “without processing your data” in the app.

That describes **sklearn `Pipeline`**, not **skops specifically**:

```python
# Save preprocessing + model together
sio.dump(pipe, "model/model.skops")

# App: raw features in → prediction out
pipe = sio.load("model/model.skops", trusted=...)
pipe.predict([[age, sex, bp, cholesterol, na_to_k]])
```

**Without** a pipeline you would duplicate encoders/scalers in `drug_app.py`, which is easy to get wrong.

**joblib works the same way** for saving the full pipeline:

```python
joblib.dump(pipe, "model/model.joblib")
pipe = joblib.load("model/model.joblib")
```

See [setup-notes.md](./setup-notes.md) for pickle vs joblib vs skops (security when loading **untrusted** files).

---

## Conda Environment (Local Dev)

Create and activate an env for local work:

```bash
conda create -n ci-cd-for-ml python=3.13 -y
conda activate ci-cd-for-ml
pip install -r requirements.txt
```

Match Python version to `python_version` in [app/README.md](../app/README.md) if deploying to Hugging Face.

---

**See also:** [train.py](../train.py), [setup-notes.md](./setup-notes.md) (skops security), [experiments.ipynb](../experiments.ipynb)

# Baseline training

Supply a lawful, documented CSV with `text,label` columns and labels `legitimate` or `scam`:

```sh
python training/train_text.py --data /path/to/consented-or-licensed.csv --out artifacts
```

The script removes duplicates, validates labels, stratifies a reproducible split, writes a TF-IDF/logistic regression artifact and reports precision, recall, F1, confusion matrix, and accuracy. It does not ship synthetic examples or claim that dataset results predict deployment performance. Dataset provenance and permission to use it are the operator's responsibility. The runtime defaults to transparent heuristics until a reviewed model-loading and calibration path is enabled.

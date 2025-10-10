"""
Evaluate taxonomy extraction using a hardcoded dataset and fuzzy alignment.
Generates an "extracted" dataset by introducing noise to a ground-truth reference,
then computes accuracy/precision/recall/F1 (macro & micro) per taxonomic level.

Run: python evaluate_taxonomy_model.py
"""

import pandas as pd
import numpy as np
import difflib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Ground-truth reference dataset (hardcoded)
reference = [
    {'name': 'Panthera leo', 'domain': 'Eukarya', 'kingdom': 'Animalia', 'phylum': 'Chordata', 'class': 'Mammalia', 'order': 'Carnivora', 'family': 'Felidae', 'genus': 'Panthera', 'species': 'Panthera leo'},
    {'name': 'Homo sapiens', 'domain': 'Eukarya', 'kingdom': 'Animalia', 'phylum': 'Chordata', 'class': 'Mammalia', 'order': 'Primates', 'family': 'Hominidae', 'genus': 'Homo', 'species': 'Homo sapiens'},
    {'name': 'Canis lupus', 'domain': 'Eukarya', 'kingdom': 'Animalia', 'phylum': 'Chordata', 'class': 'Mammalia', 'order': 'Carnivora', 'family': 'Canidae', 'genus': 'Canis', 'species': 'Canis lupus'},
    {'name': 'Gallus gallus', 'domain': 'Eukarya', 'kingdom': 'Animalia', 'phylum': 'Chordata', 'class': 'Aves', 'order': 'Galliformes', 'family': 'Phasianidae', 'genus': 'Gallus', 'species': 'Gallus gallus'},
    {'name': 'Drosophila melanogaster', 'domain': 'Eukarya', 'kingdom': 'Animalia', 'phylum': 'Arthropoda', 'class': 'Insecta', 'order': 'Diptera', 'family': 'Drosophilidae', 'genus': 'Drosophila', 'species': 'Drosophila melanogaster'},
    {'name': 'Escherichia coli', 'domain': 'Bacteria', 'kingdom': 'Bacteria', 'phylum': 'Proteobacteria', 'class': 'Gammaproteobacteria', 'order': 'Enterobacterales', 'family': 'Enterobacteriaceae', 'genus': 'Escherichia', 'species': 'Escherichia coli'},
    {'name': 'Saccharomyces cerevisiae', 'domain': 'Eukarya', 'kingdom': 'Fungi', 'phylum': 'Ascomycota', 'class': 'Saccharomycetes', 'order': 'Saccharomycetales', 'family': 'Saccharomycetaceae', 'genus': 'Saccharomyces', 'species': 'Saccharomyces cerevisiae'},
    {'name': 'Arabidopsis thaliana', 'domain': 'Eukarya', 'kingdom': 'Plantae', 'phylum': 'Tracheophyta', 'class': 'Magnoliopsida', 'order': 'Brassicales', 'family': 'Brassicaceae', 'genus': 'Arabidopsis', 'species': 'Arabidopsis thaliana'}
]

df_ref = pd.DataFrame(reference)

# Create an "extracted" dataset by copying reference and introducing noise
import random
random.seed(42)
np.random.seed(42)

def add_typos(s):
    # simple typo generator: swap two letters, remove a letter, or replace a char
    if pd.isna(s) or s == '':
        return s
    s = str(s)
    ops = ['swap', 'drop', 'replace', 'none']
    op = random.choices(ops, [0.25, 0.2, 0.25, 0.3])[0]
    if op == 'swap' and len(s) > 3:
        i = random.randint(0, len(s)-2)
        l = list(s)
        l[i], l[i+1] = l[i+1], l[i]
        return ''.join(l)
    if op == 'drop' and len(s) > 3:
        i = random.randint(0, len(s)-1)
        return s[:i] + s[i+1:]
    if op == 'replace' and len(s) > 0:
        i = random.randint(0, len(s)-1)
        return s[:i] + random.choice('abcdefghijklmnopqrstuvwxyz') + s[i+1:]
    return s

# create extracted df
rows = []
for i, row in df_ref.iterrows():
    new = row.copy()
    # for about half rows, introduce a typo in the name
    if random.random() < 0.5:
        new['name'] = add_typos(new['name'])
    # randomly drop some taxonomic ranks or replace with wrong rank
    for lvl in ['family', 'genus', 'order', 'class']:
        r = random.random()
        if r < 0.1:
            new[lvl] = np.nan
        elif r < 0.25:
            # replace with another family's name from dataset
            other = df_ref.sample(1).iloc[0][lvl]
            new[lvl] = other
    rows.append(new)

# add a few completely spurious extracted entries
spurious = [
    {'name': 'Unknown species A', 'domain': 'Eukarya', 'kingdom': 'Animalia', 'phylum': 'Chordata', 'class': 'Mammalia', 'order': 'Carnivora', 'family': 'Felidae', 'genus': 'Panthera', 'species': 'Panthera leo'},
    {'name': 'Unknown species B', 'domain': 'Bacteria', 'kingdom': 'Bacteria', 'phylum': 'Proteobacteria', 'class': 'Gammaproteobacteria', 'order': 'Enterobacterales', 'family': 'Enterobacteriaceae', 'genus': 'Escherichia', 'species': 'Escherichia coli'}
]
for s in spurious:
    rows.append(pd.Series(s))

df_ext = pd.DataFrame(rows).reset_index(drop=True)

# Now perform fuzzy alignment between extracted and reference using the 'name' column
key = 'name'
ref_names = df_ref[key].astype(str).str.strip().tolist()
ext_names = df_ext[key].astype(str).str.strip().tolist()

# Use difflib (rapidfuzz optional) to match ext->ref
try:
    from rapidfuzz import process as rf_process, fuzz as rf_fuzz
    use_rf = True
except Exception:
    use_rf = False

threshold = 85
matches = {}
used_refs = set()

for ext in sorted(set(ext_names)):
    if ext in ref_names:
        matches[ext] = ext
        used_refs.add(ext)
        continue
    best_match = None
    best_score = 0
    if use_rf:
        res = rf_process.extractOne(ext, ref_names, scorer=rf_fuzz.WRatio)
        if res:
            candidate, score, _ = res
            if score >= threshold and candidate not in used_refs:
                best_match = candidate
                best_score = score
    else:
        close = difflib.get_close_matches(ext, ref_names, n=1, cutoff=threshold/100.0)
        if close:
            candidate = close[0]
            best_score = int(difflib.SequenceMatcher(None, ext, candidate).ratio()*100)
            if best_score >= threshold and candidate not in used_refs:
                best_match = candidate
    if best_match:
        matches[ext] = best_match
        used_refs.add(best_match)

# Build aligned dataframes
aligned_pairs = []
for ext_name, ref_name in matches.items():
    ext_row = df_ext[df_ext[key].astype(str).str.strip() == ext_name]
    ref_row = df_ref[df_ref[key].astype(str).str.strip() == ref_name]
    if len(ext_row) > 0 and len(ref_row) > 0:
        aligned_pairs.append((ext_row.iloc[0].to_dict(), ref_row.iloc[0].to_dict()))

if len(aligned_pairs) == 0:
    print('No aligned pairs found; lowering threshold to 70 and retrying...')
    # try lower
    threshold = 70
    matches = {}
    used_refs = set()
    for ext in sorted(set(ext_names)):
        close = difflib.get_close_matches(ext, ref_names, n=1, cutoff=threshold/100.0)
        if close:
            candidate = close[0]
            if candidate not in used_refs:
                matches[ext] = candidate
                used_refs.add(candidate)
    for ext_name, ref_name in matches.items():
        ext_row = df_ext[df_ext[key].astype(str).str.strip() == ext_name]
        ref_row = df_ref[df_ref[key].astype(str).str.strip() == ref_name]
        if len(ext_row) > 0 and len(ref_row) > 0:
            aligned_pairs.append((ext_row.iloc[0].to_dict(), ref_row.iloc[0].to_dict()))

print(f'Aligned pairs: {len(aligned_pairs)}')

if len(aligned_pairs) == 0:
    raise SystemExit('Could not align any records; inspect the hardcoded data')

df_ext_al = pd.DataFrame([p[0] for p in aligned_pairs]).reset_index(drop=True)
df_ref_al = pd.DataFrame([p[1] for p in aligned_pairs]).reset_index(drop=True)

# Taxonomic levels to evaluate
levels = ['domain','kingdom','phylum','class','order','family','genus','species']
levels = [l for l in levels if l in df_ref_al.columns and l in df_ext_al.columns]

results = []
for lvl in levels:
    ext_col = df_ext_al[lvl].fillna('Unknown').astype(str)
    ref_col = df_ref_al[lvl].fillna('Unknown').astype(str)
    labels = sorted(list(set(ext_col.unique()) | set(ref_col.unique())))
    if len(labels) <= 1:
        results.append((lvl, 0,0,0,0,0,0,0))
        continue
    acc = accuracy_score(ref_col, ext_col)
    p_macro = precision_score(ref_col, ext_col, average='macro', zero_division=0)
    r_macro = recall_score(ref_col, ext_col, average='macro', zero_division=0)
    f_macro = f1_score(ref_col, ext_col, average='macro', zero_division=0)
    p_micro = precision_score(ref_col, ext_col, average='micro', zero_division=0)
    r_micro = recall_score(ref_col, ext_col, average='micro', zero_division=0)
    f_micro = f1_score(ref_col, ext_col, average='micro', zero_division=0)
    results.append((lvl, acc, p_macro, r_macro, f_macro, p_micro, r_micro, f_micro))

metrics_df = pd.DataFrame(results, columns=['level','accuracy','precision_macro','recall_macro','f1_macro','precision_micro','recall_micro','f1_micro']).set_index('level')

print('\nEvaluation results (rounded to 4 decimals):')
print(metrics_df.round(4))

# Also print aligned table for manual inspection
print('\nAligned extracted vs reference (sample):')
print(df_ext_al[['name'] + [c for c in levels]].head(10).to_string(index=False))
print('\nReference (same order):')
print(df_ref_al[['name'] + [c for c in levels]].head(10).to_string(index=False))

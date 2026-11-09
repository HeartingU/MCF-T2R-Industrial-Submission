#!/usr/bin/env python3
"""Check consistency of the INCLUDED aggregate and supplementary data, using stdlib only.
Does not re-run original LLM calls or source PDF extraction.
"""
from pathlib import Path
import csv, json, math, sys
ROOT=Path(__file__).resolve().parents[1]
def data(name):
    with (ROOT/name).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def check_counts(row):
    g,gen,tp,fn,fp=[int(row[k]) for k in ("gold","generated","exact_tp","missing_fn","redundant_fp")]
    assert tp+fn==g,(row,"gold mismatch")
    assert tp+fp==gen,(row,"generated mismatch")
    p=100*tp/gen if gen else 0
    r=100*tp/g if g else 0
    f1=200*tp/(gen+g) if gen+g else 0
    iou=100*tp/(tp+fn+fp) if tp+fn+fp else 0
    assert all(abs(float(row[k])-val)<.011 for k,val in (("precision_pct",p),("recall_pct",r),("f1_pct",f1),("iou_pct",iou))),row
main=data("01_main_reported_results/reported_aggregate_metrics.csv")
assert len(main)==6
for row in main:check_counts(row)
extract=data("02_mechanism_data/gold_material_tuples.csv")
structured=data("02_mechanism_data/structured_constraint_gold.csv")
assert len(extract)==295,len(extract)
assert len(structured)==177,len(structured)
repair=data("02_mechanism_data/repair_results.csv")
assert sum(int(r['cases']) for r in repair)==120
assert sum(int(r['correct_repair']) for r in repair)==114
stab=data("02_mechanism_data/stability_10seeds.csv")
assert len(stab)==15,len(stab)
abl=data("02_mechanism_data/constraint_ablation_results.csv")
assert len(abl)==5,len(abl)
assert [int(x['generated']) for x in abl]==[293,248,215,156,184]
summary=json.loads((ROOT/"02_mechanism_data/summary.json").read_text(encoding="utf-8"))
assert summary['gold_material_tuple_count']==295
assert summary['structured_constraint_gold_count']==177
assert summary['repair_total']=={'cases':120,'correct':114,'accuracy':0.95}
print("PASS: 6 main summary groups, 295 material records, 177 structured records, 5 ablation stages, 120 repairs, 10-seed summary.")
print("IMPORTANT: source PDF is restricted; this check does not verify the original end-to-end LLM predictions.")

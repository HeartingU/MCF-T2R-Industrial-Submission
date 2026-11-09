# MCF-T2R — Industrial Experiment Materials


## File inventory

- `01_main_reported_results/reported_aggregate_results.sql`: the 1,894-reference-tuple experiment **reported summary**, including six methods. This does *not* contain primary per-tuple LLM outputs.
- `01_main_reported_results/reported_aggregate_metrics.csv`: the same six summary rows exported as CSV, not a separate experimental run.
- `02_mechanism_data/gold_material_tuples.csv`: 295 extracted material-cell reference records, with pseudonymized equipment IDs.
- `02_mechanism_data/structured_constraint_gold.csv`: 177 reference tuples with a unique material type/grade/standard mapping.
- `02_mechanism_data/constraint_ablation_results.csv`: one **controlled perturbation** run with seed `20260908`, not fresh LLM inference.
- `02_mechanism_data/repair_results.csv`: 120 controlled repair cases; 114 correct under experiment rules.
- `02_mechanism_data/stability_10seeds.csv`: descriptive statistics over 10 seeded perturbation runs, not 10 LLM runs.
- `02_mechanism_data/maximum_recall_results.csv`: comparison among parser/dictionary selection rules; the reference set is defined by the broadest extraction rule (therefore that rule's 100% score is *by construction*).
- `02_mechanism_data/detailed_per_record_results_deidentified.sql`: 295 reference rows, 177 structured rows, 293 fixed candidate rows, 120 repair cases, and repeated-seed candidate records from the supplementary V2 reconstruction. IDs de-identified consistently.
- `03_code/run_cag_v2_experiments_portable.py`: original analysis script with paths changed to environment variables and equipment labels anonymized. Full reruns require the restricted source PDF and full material database.
- `03_code/validate_included_results.py`: standard-library checks for reported aggregate arithmetic and supplementary record counts.
- `04_database_sample/materials_sample.csv` and `.sql`: pseudonymized-identifier sample rows extracted from the real material catalog; it is **not** the full 585-row catalog.
- `05_deidentified_document_evidence/reconstructed_material_evidence.pdf`: the original 46-page engineering PDF supplied in the archive. Despite its filename, it contains original source pages, including organization, project, and signoff identifiers; it is not an anonymized reconstruction.

## Quick validation (no external dependencies)

```bash
python 03_code/validate_included_results.py
```

## Re-run from authorized raw sources (not included)

Install `pandas`, `numpy`, `pymupdf` in your own research environment and set:

```bash
export CAG_SOURCE_PDF=/path/to/authorized/full_source_heat_exchanger_datasheet.pdf
export CAG_MATERIAL_SQL=/path/to/authorized/full_material_library.sql
export CAG_OUTPUT_DIR=./rerun_results
python 03_code/run_cag_v2_experiments_portable.py
```


-- ============================================================
-- CAG V2 Experiment Summary Results
-- Generated from the experiment tables reported in the manuscript.
--
-- IMPORTANT:
-- 1) This file stores REPORTED SUMMARY RESULTS only.
-- 2) It does NOT reconstruct or fabricate per-tuple raw predictions.
-- 3) The 10-run stability table contains only mean ± std reported
--    in the manuscript, not the 10 individual run records.
-- 4) SQL dialect: MySQL 8.x / MariaDB-compatible basic syntax.
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS cag_experiment_metadata;
DROP TABLE IF EXISTS cag_main_results;
DROP TABLE IF EXISTS cag_stage_gain;
DROP TABLE IF EXISTS cag_candidate_coverage;
DROP TABLE IF EXISTS cag_constraint_ablation;
DROP TABLE IF EXISTS cag_repair_results;
DROP TABLE IF EXISTS cag_stability_summary;

-- ------------------------------------------------------------
-- 1. Experiment metadata
-- ------------------------------------------------------------
CREATE TABLE cag_experiment_metadata (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    experiment_group VARCHAR(100) NOT NULL,
    item_name VARCHAR(150) NOT NULL,
    item_value VARCHAR(500) NOT NULL,
    note VARCHAR(1000) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO cag_experiment_metadata
(experiment_group, item_name, item_value, note)
VALUES
('main_experiment', 'reference_tuple_count', '1894',
 'End-to-end reference tuple set reported in the manuscript.'),
('main_experiment', 'task',
 'relational instance generation for process-equipment engineering design software',
 'Target schema is predefined; evaluation uses exact tuple matching.'),
('supplementary_experiment', 'equipment_units_or_groups', '11',
 'Shell-and-tube heat-exchanger datasheets used for mechanism-level validation.'),
('supplementary_experiment', 'material_cell_reference_count', '295',
 'Reference records obtained from fixed material-cell positions.'),
('supplementary_experiment', 'structured_constraint_tuple_count', '177',
 'Records with unique material-type–grade–standard mappings.'),
('supplementary_experiment', 'uncertain_tuple_count', '120',
 '30 samples for each of four uncertainty types.'),
('supplementary_experiment', 'perturbation_seed', '20260908',
 'Fixed seed used for the single controlled perturbation experiment.'),
('supplementary_experiment', 'stability_runs', '10',
 'Only aggregate mean and standard deviation are reported in this SQL file.'),
('evaluation', 'matching_rule', 'exact tuple match',
 'A generated tuple is correct only when all fields match the reference tuple.');

-- ------------------------------------------------------------
-- 2. Main end-to-end tuple-generation results
-- ------------------------------------------------------------
CREATE TABLE cag_main_results (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    method VARCHAR(100) NOT NULL,
    gold_count INT NOT NULL,
    generated_count INT NOT NULL,
    exact_match_count INT NOT NULL,
    missing_count INT NOT NULL,
    redundant_count INT NOT NULL,
    precision_pct DECIMAL(8,4) NOT NULL,
    recall_pct DECIMAL(8,4) NOT NULL,
    f1_pct DECIMAL(8,4) NOT NULL,
    iou_pct DECIMAL(8,4) NOT NULL,
    missing_rate_pct DECIMAL(8,4) NOT NULL,
    redundancy_rate_pct DECIMAL(8,4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO cag_main_results
(method, gold_count, generated_count, exact_match_count, missing_count, redundant_count,
 precision_pct, recall_pct, f1_pct, iou_pct, missing_rate_pct, redundancy_rate_pct)
VALUES
('Rule-based',        1894, 805,  394, 1500, 411, 48.94, 20.80, 29.20, 17.09, 79.20, 51.06),
('GPT-4o',            1894, 2054, 3,   1891, 2051, 0.15, 0.16, 0.15, 0.08, 99.84, 99.85),
('GPT-4o + RAG',      1894, 1980, 1800, 94, 180, 90.91, 95.04, 92.93, 86.79, 4.96, 9.09),
('CAG (DeepSeek)',    1894, 1953, 1865, 29, 88, 95.49, 98.47, 96.96, 94.10, 1.53, 4.51),
('CAG (gpt-oss)',     1894, 1874, 1800, 94, 74, 96.05, 95.04, 95.54, 91.46, 4.96, 3.95),
('CAG (GPT-4o)',      1894, 1900, 1894, 0, 6, 99.68, 100.00, 99.84, 99.68, 0.00, 0.32);

-- ------------------------------------------------------------
-- 3. Stage-wise gain decomposition under the same GPT-4o backbone
--    Metric deltas are ABSOLUTE percentage-point changes.
-- ------------------------------------------------------------
CREATE TABLE cag_stage_gain (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stage_transition VARCHAR(150) NOT NULL,
    generated_before INT NOT NULL,
    generated_after INT NOT NULL,
    generated_delta INT NOT NULL,
    exact_before INT NOT NULL,
    exact_after INT NOT NULL,
    exact_delta INT NOT NULL,
    missing_before INT NOT NULL,
    missing_after INT NOT NULL,
    missing_delta INT NOT NULL,
    redundant_before INT NOT NULL,
    redundant_after INT NOT NULL,
    redundant_delta INT NOT NULL,
    delta_precision_pp DECIMAL(8,4) NOT NULL,
    delta_recall_pp DECIMAL(8,4) NOT NULL,
    delta_f1_pp DECIMAL(8,4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO cag_stage_gain
(stage_transition,
 generated_before, generated_after, generated_delta,
 exact_before, exact_after, exact_delta,
 missing_before, missing_after, missing_delta,
 redundant_before, redundant_after, redundant_delta,
 delta_precision_pp, delta_recall_pp, delta_f1_pp)
VALUES
('GPT-4o -> GPT-4o + RAG',
 2054, 1980, -74,
 3, 1800, 1797,
 1891, 94, -1797,
 2051, 180, -1871,
 90.76, 94.88, 92.78),
('GPT-4o + RAG -> CAG (GPT-4o)',
 1980, 1900, -80,
 1800, 1894, 94,
 94, 0, -94,
 180, 6, -174,
 8.77, 4.96, 6.91);

-- ------------------------------------------------------------
-- 4. Candidate-coverage experiment on 295 material-cell references
-- ------------------------------------------------------------
CREATE TABLE cag_candidate_coverage (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    method VARCHAR(120) NOT NULL,
    reference_count INT NOT NULL,
    generated_count INT NOT NULL,
    matched_count INT NOT NULL,
    missing_count INT NOT NULL,
    precision_pct DECIMAL(8,4) NOT NULL,
    recall_pct DECIMAL(8,4) NOT NULL,
    f1_pct DECIMAL(8,4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO cag_candidate_coverage
(method, reference_count, generated_count, matched_count, missing_count,
 precision_pct, recall_pct, f1_pct)
VALUES
('Strict Rule-Based Extraction', 295, 170, 170, 125, 100.00, 57.63, 73.12),
('Dictionary-Assisted Extraction', 295, 278, 278, 17, 100.00, 94.24, 97.03),
('Maximum-Recall Strategy', 295, 295, 295, 0, 100.00, 100.00, 100.00);

-- ------------------------------------------------------------
-- 5. Constraint-level ablation under controlled perturbations
-- ------------------------------------------------------------
CREATE TABLE cag_constraint_ablation (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stage VARCHAR(100) NOT NULL,
    gold_count INT NOT NULL,
    generated_count INT NOT NULL,
    matched_count INT NOT NULL,
    missing_count INT NOT NULL,
    redundant_count INT NOT NULL,
    precision_pct DECIMAL(8,4) NOT NULL,
    recall_pct DECIMAL(8,4) NOT NULL,
    f1_pct DECIMAL(8,4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO cag_constraint_ablation
(stage, gold_count, generated_count, matched_count, missing_count, redundant_count,
 precision_pct, recall_pct, f1_pct)
VALUES
('Initial',       177, 293, 149, 28, 144, 50.85, 84.18, 63.40),
('+ Domain',      177, 248, 149, 28, 99,  60.08, 84.18, 70.12),
('+ FD',          177, 215, 149, 28, 66,  69.30, 84.18, 76.02),
('+ Business',    177, 156, 149, 28, 7,   95.51, 84.18, 89.49),
('Full + Repair', 177, 184, 177, 0,  7,   96.20, 100.00, 98.06);

-- ------------------------------------------------------------
-- 6. Uncertain-tuple repair results
-- ------------------------------------------------------------
CREATE TABLE cag_repair_results (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    uncertainty_type VARCHAR(150) NOT NULL,
    sample_count INT NOT NULL,
    correctly_repaired_count INT NOT NULL,
    repair_accuracy_pct DECIMAL(8,4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO cag_repair_results
(uncertainty_type, sample_count, correctly_repaired_count, repair_accuracy_pct)
VALUES
('Missing Material Standard', 30, 30, 100.00),
('Missing Material Type', 30, 30, 100.00),
('Conflicting Material Standard', 30, 30, 100.00),
('Multiple Candidate Material Grades', 30, 24, 80.00),
('Overall', 120, 114, 95.00);

-- ------------------------------------------------------------
-- 7. Stability summary over 10 random perturbation runs
--    Note: only mean ± std are available here.
-- ------------------------------------------------------------
CREATE TABLE cag_stability_summary (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stage VARCHAR(100) NOT NULL,
    precision_mean_pct DECIMAL(8,4) NOT NULL,
    precision_std_pct DECIMAL(8,4) NOT NULL,
    recall_mean_pct DECIMAL(8,4) NOT NULL,
    recall_std_pct DECIMAL(8,4) NOT NULL,
    f1_mean_pct DECIMAL(8,4) NOT NULL,
    f1_std_pct DECIMAL(8,4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO cag_stability_summary
(stage,
 precision_mean_pct, precision_std_pct,
 recall_mean_pct, recall_std_pct,
 f1_mean_pct, f1_std_pct)
VALUES
('Initial',       48.55, 1.89, 83.67, 1.83, 61.44, 1.88),
('+ Domain',      55.79, 2.06, 83.67, 1.83, 66.93, 1.81),
('+ FD',          64.95, 2.41, 83.67, 1.83, 73.12, 2.06),
('+ Business',    89.60, 2.67, 83.67, 1.83, 86.51, 1.69),
('Full + Repair', 91.15, 2.28, 100.00, 0.00, 95.35, 1.23);

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- Convenience queries
-- ============================================================

-- Main end-to-end results
SELECT * FROM cag_main_results ORDER BY id;

-- Constraint ablation
SELECT * FROM cag_constraint_ablation ORDER BY id;

-- Repair results
SELECT * FROM cag_repair_results ORDER BY id;

-- Stability summary
SELECT * FROM cag_stability_summary ORDER BY id;

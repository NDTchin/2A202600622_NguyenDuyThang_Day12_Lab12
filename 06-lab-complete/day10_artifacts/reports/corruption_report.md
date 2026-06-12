# Corruption Comparison Report

## Summary

The corrupted run should expose how data quality issues affect retrieval and answer quality. The repaired run should move metrics back toward the baseline.

## Metric Comparison

| Metric | Baseline | Corrupted | Repaired | Corrupted Delta | Repaired Delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| `samples` | 32 | 32 | 32 | +0.0000 | +0.0000 |
| `retrieval_hit_rate` | 1.0000 | 0.6250 | 1.0000 | -0.3750 | +0.0000 |
| `mean_token_f1` | 1.0000 | 0.6330 | 1.0000 | -0.3670 | +0.0000 |
| `judge_accuracy` | 1.0000 | 0.6250 | 1.0000 | -0.3750 | +0.0000 |
| `mean_judge_score` | 5 | 3.5000 | 5 | -1.5000 | +0.0000 |

## Observability Status

- Corrupted: quality=FAIL, failed_checks=4, freshness=FAIL, stale_rows=3
- Repaired: quality=PASS, failed_checks=0, freshness=PASS, stale_rows=0

## Corrupted Quality Checks

| Check | Status | Observed | Threshold | Severity |
| --- | --- | ---: | --- | --- |
| `row_count_minimum` | PASS | 23 | >= 3 | error |
| `required_columns_present` | PASS | none | no missing columns | error |
| `paper_id_not_blank` | PASS | 0 | 0 blank values | error |
| `paper_id_unique` | FAIL | 2 | 0 duplicates | error |
| `title_not_blank` | PASS | 0 | 0 blank values | error |
| `summary_not_blank` | FAIL | 6 | 0 blank values | error |
| `summary_min_length` | FAIL | 6 | 0 below 40 chars | error |
| `embedding_text_not_blank` | PASS | 0 | 0 blank values | error |
| `published_parseable` | PASS | 0 | 0 invalid dates | error |
| `age_days_parseable` | PASS | 0 | 0 invalid values | error |
| `freshness_threshold` | FAIL | 3 | 0 rows older than 180 days | warning |

## Repaired Quality Checks

| Check | Status | Observed | Threshold | Severity |
| --- | --- | ---: | --- | --- |
| `row_count_minimum` | PASS | 24 | >= 3 | error |
| `required_columns_present` | PASS | none | no missing columns | error |
| `paper_id_not_blank` | PASS | 0 | 0 blank values | error |
| `paper_id_unique` | PASS | 0 | 0 duplicates | error |
| `title_not_blank` | PASS | 0 | 0 blank values | error |
| `summary_not_blank` | PASS | 0 | 0 blank values | error |
| `summary_min_length` | PASS | 0 | 0 below 40 chars | error |
| `embedding_text_not_blank` | PASS | 0 | 0 blank values | error |
| `published_parseable` | PASS | 0 | 0 invalid dates | error |
| `age_days_parseable` | PASS | 0 | 0 invalid values | error |
| `freshness_threshold` | PASS | 0 | 0 rows older than 180 days | warning |

## Freshness Comparison

### Corrupted

| Field | Value |
| --- | ---: |
| `total_rows` | 23 |
| `freshness_threshold_days` | 180 |
| `latest_published` | 2026-12-31 |
| `oldest_published` | 2000-01-01 |
| `stale_rows` | 3 |
| `invalid_published_rows` | 0 |
| `is_fresh` | FAIL |

### Repaired

| Field | Value |
| --- | ---: |
| `total_rows` | 24 |
| `freshness_threshold_days` | 180 |
| `latest_published` | 2027-05-07 |
| `oldest_published` | 2026-12-01 |
| `stale_rows` | 0 |
| `invalid_published_rows` | 0 |
| `is_fresh` | PASS |

## Notes

- Corrupted retrieval hit rate delta from baseline: -0.3750.
- Repaired retrieval hit rate delta from baseline: +0.0000.
- Review the corruption log together with this report to explain which data issues caused metric changes.

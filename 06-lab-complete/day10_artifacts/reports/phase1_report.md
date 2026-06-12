# Phase 1 Baseline Report

## Summary

The baseline pipeline produced a usable dataset and evaluation artifacts.

## Source

| Field | Value |
| --- | --- |
| `source_api` | Crossref REST API |
| `source_query` | agentic retrieval augmented generation large language model |
| `source_filter` | from-pub-date:2025-12-12,has-abstract:true |
| `max_results` | 24 |
| `raw_records` | 24 |
| `clean_records` | 24 |
| `run_date_utc` | 2026-06-10T08:30:09.726489+00:00 |
| `raw_records_path` | D:\Vin\Lab\Day-10-Data-Pipeline-Data-Observability\data\raw\crossref_records.json |
| `clean_csv_path` | D:\Vin\Lab\Day-10-Data-Pipeline-Data-Observability\data\clean\papers_clean.csv |
| `embeddings_manifest_path` | D:\Vin\Lab\Day-10-Data-Pipeline-Data-Observability\data\embeddings\papers_embeddings.json |

## Evaluation Metrics

| Metric | Value |
| --- | ---: |
| `samples` | 32 |
| `retrieval_hit_rate` | 1.0000 |
| `mean_token_f1` | 1.0000 |
| `judge_accuracy` | 1.0000 |
| `mean_judge_score` | 5 |
| `ragas` | skipped=Set RUN_RAGAS=1 to enable the slower Ragas pass. |

## Data Quality

- Overall status: PASS
- Failed checks: 0
- Total rows: 24

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

## Freshness

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

- Retrieval metrics should be compared against the corrupted and repaired runs in the next phase.
- Quality checks are generated from the actual cleaned dataframe used to build the vector index.

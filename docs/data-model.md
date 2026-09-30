# Data model

## Tables

### companies
| Column | Type | Description |
|---|---|---|
| id | TEXT PK | Stable company ID |
| name | TEXT | Company name |
| name_normalized | TEXT | Lowercase, punctuation-stripped |
| official_domain | TEXT | Registrable domain |
| homepage | TEXT | Homepage URL |
| region | TEXT | Region |
| company_state | TEXT | active, acquired, rebranded, defunct, unknown |
| parent_company_id | TEXT | Parent company if acquired |
| created_at | TEXT | Timestamp |

### company_sources
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| company_id | TEXT FK | Company ID |
| source_name | TEXT | Source name |
| profile_url | TEXT | Profile URL |
| listed_url_raw | TEXT | URL as listed |
| listed_url_clean | TEXT | URL after normalization |
| raw_metadata | TEXT | JSON metadata |
| seen_at | TEXT | Timestamp |

### discovery_runs
| Column | Type | Description |
|---|---|---|
| run_id | TEXT PK | Run ID |
| started_at | TEXT | Timestamp |
| config_snapshot | TEXT | JSON config |
| code_version | TEXT | Code version |
| cost_used | REAL | Cost in USD |

### discovery_attempts
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| run_id | TEXT | Run ID |
| company_id | TEXT | Company ID |
| stage | TEXT | Stage name |
| candidate_url | TEXT | Candidate URL |
| method | TEXT | Method |
| agent_involved | INTEGER | Whether AI was involved |
| input | TEXT | JSON input |
| output | TEXT | JSON output |
| evidence | TEXT | JSON evidence |
| outcome | TEXT | Outcome |
| error_class | TEXT | Error classification |
| duration | REAL | Duration in seconds |
| timestamp | TEXT | Timestamp |

### career_destinations
| Column | Type | Description |
|---|---|---|
| company_id | TEXT PK | Company ID |
| status | TEXT | pending, in_progress, verified, needs_review, not_found, blocked, inactive |
| destination_type | TEXT | ats_board, custom_page, custom_page_with_ats, careers_page_no_openings, third_party_official |
| careers_url | TEXT | Careers URL |
| job_board_url | TEXT | Job board URL |
| ats_provider | TEXT | ATS provider |
| ats_slug | TEXT | ATS slug |
| jobs_api_url | TEXT | Jobs API URL |
| open_jobs_count | INTEGER | Number of open jobs |
| discovery_method | TEXT | How it was discovered |
| confidence | REAL | Confidence score |
| evidence_summary | TEXT | Evidence summary |
| fallback_urls | TEXT | Comma-separated fallback URLs |
| last_verified_at | TEXT | Last verification timestamp |
| pipeline_version | TEXT | Pipeline version |

### review_queue
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| company_id | TEXT | Company ID |
| reason | TEXT | Reason for review |
| candidates | TEXT | JSON candidates |
| attempt_summary | TEXT | Attempt summary |
| suggested_next_action | TEXT | Suggested action |
| resolution | TEXT | Resolution |
| resolved_by | TEXT | Who resolved it |
| resolved_at | TEXT | Resolution timestamp |

### merges
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| kept_company_id | TEXT | Company that was kept |
| merged_company_id | TEXT | Company that was merged |
| reason | TEXT | Reason for merge |
| evidence | TEXT | JSON evidence |
| created_at | TEXT | Timestamp |

## Status taxonomy

### status (pipeline state)
- `pending` — not yet processed
- `in_progress` — currently being processed
- `verified` — passed §7 verification
- `needs_review` — plausible, but a check failed
- `not_found` — full ladder exhausted
- `blocked` — access was prevented
- `inactive` — domain dead or parked

### destination_type (when verified)
- `ats_board` — ATS job board
- `custom_page` — custom careers page
- `custom_page_with_ats` — custom page with embedded ATS
- `careers_page_no_openings` — careers page with no current openings
- `third_party_official` — third-party platform (only after review)

### company_state
- `active` — company is active
- `acquired` — company was acquired
- `rebranded` — company was rebranded
- `defunct` — company is defunct
- `unknown` — state unknown

## Semantic rules

- No current openings ≠ no careers page
- `blocked` ≠ `inactive`
- `not_found` ≠ `inactive`
- An acquisition never deletes or overwrites the acquired company
- Every company always has exactly one status

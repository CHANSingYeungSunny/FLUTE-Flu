# Peak Evaluation Specification — peak-evaluation-v1

Frozen before Test access.

- **spec_id**: `"peak-evaluation-v1"`
- **generated_utc**: `"2026-09-21T04:47:43Z"`
- **frozen_before_test_access**: `true`
- **target**: `"ILITOTAL"`
- **channel_index**: `4`
- **scale**: `"inverse-transformed original scale (physical)"`
- **forecast_origin_definition**: `"window index i (0-based); input = data[i:i+104]; target = data[i+104:i+104+L]"`
- **target_date_reconstruction**: `"abs_week = forecast_origin + 104 + step; calendar date from cdc_calendar.load_week_calendar (abs_week 0 = epiweek 200201, week_start 2001-12-30)"`
- **epiweek_convention**: `"CDC epiweek YYYYWW"`
- **calendar_anchors**: `{"abs_week_715": "2016-01-24", "abs_week_769": "2017-02-05", "abs_week_819": "2018-01-21", "abs_week_820": "2018-01-28", "abs_week_821": "2018-02-04"}`
- **season_definition**: `{"convention": "influenza season = epiweek 40..52 of year Y plus epiweek 1..20 of year Y+1, labeled 'YYYY/YYYY+1'", "epiweek_parse": "year = epiweek // 100; week = epiweek % 100", "eligible_season": "a season is eligible for a given (model, horizon, lead) if it has >= 2 distinct target weeks with predictions at that lead AND max observed ILITOTAL > 0"}`
- **metrics**: `{"PTE": "abs(predicted peak week - observed peak week), unit = weeks", "PIE": "abs(predicted peak intensity - observed peak intensity) / abs(observed peak intensity) * 100, unit = percent", "PTE_hit": "PTE <= 1 week", "PIE_hit": "PIE <= 25 percent", "joint_hit": "PTE_hit AND PIE_hit"}`
- **peak_detection**: `{"scope": "single global peak per eligible season over that season's target weeks", "tie_rule": "multiple equal maxima => first (earliest) index (np.argmax semantics)", "rolling_window": "for lead-time l, restrict to target weeks whose lead_weeks == l before peak detection", "dedup": "overlapping forecast origins predicting the same target week are averaged (group by target_date)"}`
- **edge_policies**: `{"missing_week": "exclude that season (or fail-stop if systemic)", "observed_peak_zero": "PIE undefined => exclude (PIE=None, no hit)", "incomplete_season": "season without a full lead-coverage window is reported but marked partial"}`
- **lead_time**: `{"definition": "lead_weeks = step + 1; steps 0..3 => 1..4 weeks ahead", "aggregation": "PTE/PIE computed per lead, reported per lead and averaged over lead"}`
- **citation**: `"Kramer and Shaman (2019) DOI 10.1371/journal.pcbi.1006742 (thresholds only; no CDC-compatible claim unless audited)"`

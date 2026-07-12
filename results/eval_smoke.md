# Text-to-SQL Evaluation Report

- Model: `gpt-oss-120b`
- Strategy: `single`
- Questions: `data/dev_questions_with_answers.json`
- Timestamp: `2026-06-12T15:32:20`

## Summary

| Metric | Value |
|---|---:|
| n | 2 |
| execution_accuracy | 1.000000 |
| overall_accuracy | 1.000000 |
| valid_sql_rate | 1.000000 |
| repair_rate | 0.000000 |
| miscalibrated_clarify_rate | 0.000000 |
| p50_latency_s | 1.878581 |
| p95_latency_s | 1.414362 |
| avg_cost_usd | 0.000775 |
| total_cost_usd | 0.001550 |
| avg_llm_calls | 1.000000 |
| avg_input_tokens | 4251.500000 |
| avg_output_tokens | 229.000000 |

## Per-Question Results

| ID | Correct | Action | Attempts | Latency (s) | SQL |
|---|---:|---|---:|---:|---|
| q_001 | yes | sql | 1 | 2.343 | `SELECT g.Name AS Genre, SUM(il.UnitPrice * il.Quantity) AS TotalSales FROM InvoiceLine il JOIN Track t ON il.TrackId = t.TrackId JOIN Gen...` |
| q_002 | yes | sql | 1 | 1.414 | `SELECT Album.Title FROM Album JOIN Artist ON Album.ArtistId = Artist.ArtistId WHERE Artist.Name = 'AC/DC'` |

# Text-to-SQL Evaluation Report

- Model: `qwen3.6-plus`
- Strategy: `naive`
- Questions: `data/dev_questions_with_answers.json`
- Timestamp: `2026-06-12T15:58:30`

## Summary

| Metric | Value |
|---|---:|
| n | 10 |
| execution_accuracy | 0.100000 |
| overall_accuracy | 0.100000 |
| valid_sql_rate | 0.100000 |
| repair_rate | 0.000000 |
| miscalibrated_clarify_rate | 0.000000 |
| p50_latency_s | 2.645281 |
| p95_latency_s | 3.623727 |
| avg_cost_usd | 0.000789 |
| total_cost_usd | 0.007893 |
| avg_llm_calls | 1.000000 |
| avg_input_tokens | 33.100000 |
| avg_output_tokens | 257.600000 |

## Per-Question Results

| ID | Correct | Action | Attempts | Latency (s) | SQL |
|---|---:|---|---:|---:|---|
| q_001 | no | error | 1 | 3.269 | `SELECT      g.name AS genre,     SUM(il.quantity * il.unit_price) AS total_sales FROM      genres g JOIN      tracks t ON g.genre_id = t....` |
| q_002 | no | error | 1 | 3.145 | `SELECT albums.title FROM albums JOIN artists ON albums.artist_id = artists.artist_id WHERE artists.name = 'AC/DC'` |
| q_003 | no | error | 1 | 0.379 | `SELECT name, email FROM customers WHERE country = 'Brazil'` |
| q_004 | no | error | 1 | 2.797 | `SELECT      mt.name AS media_type,     COUNT(t.track_id) AS track_count FROM      tracks t JOIN      media_types mt ON t.media_type_id = ...` |
| q_005 | no | error | 1 | 3.288 | `SELECT      e.employee_id,     e.first_name,     e.last_name,     COUNT(c.customer_id) AS customer_count FROM      employees e JOIN      ...` |
| q_006 | no | error | 1 | 3.624 | `SELECT      p.playlist_id,     p.name AS playlist_name,     COUNT(pt.track_id) AS track_count FROM      playlist p JOIN      playlist_tra...` |
| q_007 | no | error | 1 | 2.493 | `SELECT SUM(revenue) AS total_revenue FROM orders WHERE YEAR(order_date) = 2021` |
| q_008 | no | error | 1 | 0.445 | `SELECT billing_country, AVG(total) AS average_invoice_total FROM invoices GROUP BY billing_country ORDER BY average_invoice_total DESC` |
| q_009 | no | error | 1 | 1.206 | `SELECT     customer_id,     total_spending,     spending_rank FROM (     SELECT         customer_id,         SUM(amount) AS total_spendin...` |
| q_010 | yes | sql | 1 | 1.317 | `SELECT      ar.Name AS ArtistName,     COUNT(DISTINCT g.GenreId) AS NumberOfDistinctGenres FROM      Artist ar     JOIN Album al ON ar.Ar...` |

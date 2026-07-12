# Text-to-SQL Evaluation Report

- Model: `qwen3.6-plus`
- Strategy: `react`
- Questions: `data/dev_questions_with_answers.json`
- Timestamp: `2026-06-12T15:59:36`

## Summary

| Metric | Value |
|---|---:|
| n | 10 |
| execution_accuracy | 0.800000 |
| overall_accuracy | 0.800000 |
| valid_sql_rate | 1.000000 |
| repair_rate | 0.000000 |
| miscalibrated_clarify_rate | 0.000000 |
| p50_latency_s | 1.113216 |
| p95_latency_s | 1.701597 |
| avg_cost_usd | 0.002824 |
| total_cost_usd | 0.028244 |
| avg_llm_calls | 1.000000 |
| avg_input_tokens | 5045.100000 |
| avg_output_tokens | 100.600000 |

## Per-Question Results

| ID | Correct | Action | Attempts | Latency (s) | SQL |
|---|---:|---|---:|---:|---|
| q_001 | yes | sql | 1 | 1.702 | `SELECT g.Name AS Genre, SUM(il.UnitPrice * il.Quantity) AS TotalSales FROM Genre g JOIN Track t ON g.GenreId = t.GenreId JOIN InvoiceLine...` |
| q_002 | yes | sql | 1 | 0.873 | `SELECT a.Title FROM Album a JOIN Artist ar ON a.ArtistId = ar.ArtistId WHERE ar.Name = 'AC/DC'` |
| q_003 | yes | sql | 1 | 0.604 | `SELECT FirstName, LastName, Email FROM Customer WHERE Country = 'Brazil'` |
| q_004 | yes | sql | 1 | 1.211 | `SELECT mt.Name, COUNT(t.TrackId) AS track_count FROM MediaType mt JOIN Track t ON mt.MediaTypeId = t.MediaTypeId GROUP BY mt.Name ORDER B...` |
| q_005 | no | sql | 1 | 0.897 | `SELECT e.FirstName, e.LastName, COUNT(c.CustomerId) AS CustomerCount FROM Employee e JOIN Customer c ON e.EmployeeId = c.SupportRepId GRO...` |
| q_006 | yes | sql | 1 | 1.016 | `SELECT p.Name AS PlaylistName, COUNT(pt.TrackId) AS TrackCount FROM Playlist p LEFT JOIN PlaylistTrack pt ON p.PlaylistId = pt.PlaylistId...` |
| q_007 | yes | sql | 1 | 0.813 | `SELECT SUM(Total) AS total_revenue FROM Invoice WHERE strftime('%Y', InvoiceDate) = '2021'` |
| q_008 | yes | sql | 1 | 1.266 | `SELECT BillingCountry, AVG(Total) AS AverageInvoiceTotal FROM Invoice GROUP BY BillingCountry ORDER BY AverageInvoiceTotal DESC` |
| q_009 | no | sql | 1 | 1.424 | `SELECT      c.CustomerId,     c.FirstName \|\| ' ' \|\| c.LastName AS CustomerName,     SUM(i.Total) AS TotalSpending,     RANK() OVER (O...` |
| q_010 | yes | sql | 1 | 1.378 | `SELECT a.Name AS ArtistName, COUNT(DISTINCT t.GenreId) AS DistinctGenreCount FROM Artist a JOIN Album al ON a.ArtistId = al.ArtistId JOIN...` |

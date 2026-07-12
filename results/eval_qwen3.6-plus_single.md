# Text-to-SQL Evaluation Report

- Model: `qwen3.6-plus`
- Strategy: `single`
- Questions: `data/dev_questions_with_answers.json`
- Timestamp: `2026-06-12T16:26:23`

## Summary

| Metric | Value |
|---|---:|
| n | 10 |
| execution_accuracy | 1.000000 |
| overall_accuracy | 1.000000 |
| valid_sql_rate | 1.000000 |
| repair_rate | 0.000000 |
| miscalibrated_clarify_rate | 0.000000 |
| p50_latency_s | 1.065587 |
| p95_latency_s | 2.079637 |
| avg_cost_usd | 0.002731 |
| total_cost_usd | 0.027307 |
| avg_llm_calls | 1.000000 |
| avg_input_tokens | 4847.100000 |
| avg_output_tokens | 102.400000 |

## Per-Question Results

| ID | Correct | Action | Attempts | Latency (s) | SQL |
|---|---:|---|---:|---:|---|
| q_001 | yes | sql | 1 | 1.492 | `SELECT g.Name, SUM(il.UnitPrice * il.Quantity) AS TotalSales FROM Genre g JOIN Track t ON g.GenreId = t.GenreId JOIN InvoiceLine il ON t....` |
| q_002 | yes | sql | 1 | 0.940 | `SELECT a.Title FROM Album a JOIN Artist ar ON a.ArtistId = ar.ArtistId WHERE ar.Name = 'AC/DC'` |
| q_003 | yes | sql | 1 | 0.647 | `SELECT FirstName, LastName, Email FROM Customer WHERE Country = 'Brazil'` |
| q_004 | yes | sql | 1 | 1.062 | `SELECT mt.Name, COUNT(t.TrackId) AS TrackCount FROM MediaType mt LEFT JOIN Track t ON mt.MediaTypeId = t.MediaTypeId GROUP BY mt.MediaTyp...` |
| q_005 | yes | sql | 1 | 1.160 | `SELECT e.FirstName \|\| ' ' \|\| e.LastName AS EmployeeName, COUNT(c.CustomerId) AS CustomerCount FROM Employee e LEFT JOIN Customer c ON...` |
| q_006 | yes | sql | 1 | 1.069 | `SELECT p.Name, COUNT(pt.TrackId) AS TrackCount FROM Playlist p LEFT JOIN PlaylistTrack pt ON p.PlaylistId = pt.PlaylistId GROUP BY p.Play...` |
| q_007 | yes | sql | 1 | 0.749 | `SELECT SUM(Total) AS total_revenue FROM Invoice WHERE strftime('%Y', InvoiceDate) = '2021'` |
| q_008 | yes | sql | 1 | 0.738 | `SELECT BillingCountry, AVG(Total) AS AverageInvoiceTotal FROM Invoice GROUP BY BillingCountry ORDER BY AverageInvoiceTotal DESC` |
| q_009 | yes | sql | 1 | 1.286 | `SELECT      c.FirstName \|\| ' ' \|\| c.LastName AS CustomerName,     SUM(i.Total) AS TotalSpending,     RANK() OVER (ORDER BY SUM(i.Tota...` |
| q_010 | yes | sql | 1 | 2.080 | `SELECT      a.Name AS ArtistName,     COUNT(DISTINCT t.GenreId) AS DistinctGenreCount FROM      Artist a JOIN      Album al ON a.ArtistId...` |

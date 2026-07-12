# Text-to-SQL Evaluation Report

- Model: `qwen3.6-plus`
- Strategy: `sc`
- Questions: `data/dev_questions_with_answers.json`
- Timestamp: `2026-06-12T16:01:08`

## Summary

| Metric | Value |
|---|---:|
| n | 10 |
| execution_accuracy | 0.800000 |
| overall_accuracy | 0.800000 |
| valid_sql_rate | 1.000000 |
| repair_rate | 1.000000 |
| miscalibrated_clarify_rate | 0.000000 |
| p50_latency_s | 3.170684 |
| p95_latency_s | 5.406699 |
| avg_cost_usd | 0.007941 |
| total_cost_usd | 0.079406 |
| avg_llm_calls | 3.000000 |
| avg_input_tokens | 14130.300000 |
| avg_output_tokens | 291.800000 |

## Per-Question Results

| ID | Correct | Action | Attempts | Latency (s) | SQL |
|---|---:|---|---:|---:|---|
| q_001 | yes | sql | 3 | 4.139 | `SELECT g.Name AS GenreName, SUM(il.UnitPrice * il.Quantity) AS TotalSales FROM Genre g JOIN Track t ON g.GenreId = t.GenreId JOIN Invoice...` |
| q_002 | yes | sql | 3 | 2.993 | `SELECT a.Title FROM Album a JOIN Artist ar ON a.ArtistId = ar.ArtistId WHERE ar.Name = 'AC/DC'` |
| q_003 | yes | sql | 3 | 2.641 | `SELECT FirstName, LastName, Email FROM Customer WHERE Country = 'Brazil'` |
| q_004 | yes | sql | 3 | 3.263 | `SELECT mt.Name, COUNT(t.TrackId) AS TrackCount FROM MediaType mt JOIN Track t ON mt.MediaTypeId = t.MediaTypeId GROUP BY mt.Name ORDER BY...` |
| q_005 | no | sql | 3 | 5.057 | `SELECT e.FirstName, e.LastName, COUNT(c.CustomerId) AS CustomerCount FROM Employee e JOIN Customer c ON e.EmployeeId = c.SupportRepId GRO...` |
| q_006 | yes | sql | 3 | 3.079 | `SELECT p.Name AS PlaylistName, COUNT(pt.TrackId) AS TrackCount FROM Playlist p LEFT JOIN PlaylistTrack pt ON p.PlaylistId = pt.PlaylistId...` |
| q_007 | yes | sql | 3 | 2.872 | `SELECT SUM(Total) AS total_revenue FROM Invoice WHERE strftime('%Y', InvoiceDate) = '2021'` |
| q_008 | yes | sql | 3 | 2.962 | `SELECT BillingCountry, AVG(Total) AS AverageInvoiceTotal FROM Invoice GROUP BY BillingCountry ORDER BY AverageInvoiceTotal DESC` |
| q_009 | no | sql | 3 | 4.870 | `SELECT      c.CustomerId,     c.FirstName,     c.LastName,     SUM(i.Total) AS TotalSpending,     RANK() OVER (ORDER BY SUM(i.Total) DESC...` |
| q_010 | yes | sql | 3 | 5.407 | `SELECT      a.Name AS ArtistName,     COUNT(DISTINCT t.GenreId) AS DistinctGenreCount FROM      Artist a JOIN      Album al ON a.ArtistId...` |

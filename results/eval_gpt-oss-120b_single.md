# Text-to-SQL Evaluation Report

- Model: `gpt-oss-120b`
- Strategy: `single`
- Questions: `data/dev_questions_with_answers.json`
- Timestamp: `2026-06-12T16:15:31`

## Summary

| Metric | Value |
|---|---:|
| n | 10 |
| execution_accuracy | 1.000000 |
| overall_accuracy | 1.000000 |
| valid_sql_rate | 1.000000 |
| repair_rate | 0.000000 |
| miscalibrated_clarify_rate | 0.000000 |
| p50_latency_s | 1.532402 |
| p95_latency_s | 2.692680 |
| avg_cost_usd | 0.000818 |
| total_cost_usd | 0.008179 |
| avg_llm_calls | 1.000000 |
| avg_input_tokens | 4345.800000 |
| avg_output_tokens | 276.700000 |

## Per-Question Results

| ID | Correct | Action | Attempts | Latency (s) | SQL |
|---|---:|---|---:|---:|---|
| q_001 | yes | sql | 1 | 1.668 | `SELECT g.Name AS Genre, SUM(il.UnitPrice * il.Quantity) AS TotalSales FROM InvoiceLine il JOIN Track t ON il.TrackId = t.TrackId JOIN Gen...` |
| q_002 | yes | sql | 1 | 1.301 | `SELECT Album.Title FROM Album JOIN Artist ON Album.ArtistId = Artist.ArtistId WHERE Artist.Name = 'AC/DC'` |
| q_003 | yes | sql | 1 | 0.964 | `SELECT FirstName, LastName, Email FROM Customer WHERE Country = 'Brazil'` |
| q_004 | yes | sql | 1 | 1.721 | `SELECT mt.Name, COUNT(t.TrackId) AS TrackCount FROM MediaType mt JOIN Track t ON mt.MediaTypeId = t.MediaTypeId GROUP BY mt.MediaTypeId O...` |
| q_005 | yes | sql | 1 | 1.807 | `SELECT (e.FirstName \|\| ' ' \|\| e.LastName) AS EmployeeName, COUNT(c.CustomerId) AS CustomerCount FROM Employee e LEFT JOIN Customer c ...` |
| q_006 | yes | sql | 1 | 1.397 | `SELECT p.Name AS Playlist, COUNT(pt.TrackId) AS TrackCount FROM Playlist p LEFT JOIN PlaylistTrack pt ON p.PlaylistId = pt.PlaylistId GRO...` |
| q_007 | yes | sql | 1 | 1.369 | `SELECT SUM(Total) AS TotalRevenue FROM Invoice WHERE strftime('%Y', InvoiceDate) = '2021'` |
| q_008 | yes | sql | 1 | 1.242 | `SELECT BillingCountry, AVG(Total) AS AverageTotal FROM Invoice GROUP BY BillingCountry ORDER BY AverageTotal DESC` |
| q_009 | yes | sql | 1 | 2.693 | `SELECT     CustomerName,     TotalSpending,     RANK() OVER (ORDER BY TotalSpending DESC) AS Rank FROM (     SELECT c.CustomerId,        ...` |
| q_010 | yes | sql | 1 | 2.014 | `SELECT Artist.Name AS ArtistName, COUNT(DISTINCT Track.GenreId) AS GenreCount FROM Artist JOIN Album ON Artist.ArtistId = Album.ArtistId ...` |

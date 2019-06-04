
```sql
SELECT * FROM logs ORDER BY timestamp DESC LIMIT 5;
```

Find errors:
```sql
SELECT * FROM logs WHERE length(logs.error) > 0;
```
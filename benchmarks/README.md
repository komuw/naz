connect:   
```sh
psql --host=localhost --port=5432 --username=myuser --dbname=mydb
```



```sql
SELECT * FROM logs ORDER BY timestamp DESC LIMIT 5;
```

Find errors:
```sql
SELECT * FROM logs WHERE length(logs.error) > 0 ORDER BY timestamp DESC;
```
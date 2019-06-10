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

```sql
SELECT event,log_id,error FROM logs WHERE length(logs.error) > 0 ORDER BY timestamp DESC;
```

```sh
          event          |   log_id    |                error
-------------------------+-------------+--------------------------------------
 naz.Client.send_data    | 405-jctnhvo | [Errno 104] Connection reset by peer
 naz.Client.receive_data |             | [Errno 104] Connection reset by peer
 naz.Client.send_data    | 78-zbtrpxw  | [Errno 104] Connection reset by peer
 ```


### Results:
The benchmark was run this way:
- `naz-cli` was deployed on a $5/month digitalocean server with 1GB of RAM and 1 cpu in the San Francisco region.       
- A mock SMSC server was also deployed on a $5/month digitalocean server with 1GB of RAM and 1 cpu in the Amsterdam region.     
- A redis server was also deployed the same $5/month digitalocean server in the Amsterdam region.   
- The ping latency between the `naz` server in Sanfrancisco and the SMSC server in Amsterdam was about `154 ms`    

- 


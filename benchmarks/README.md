
### Methodology
The benchmark was run this way:

#### A.
- `naz-cli` was deployed on a $5/month digitalocean server with 1GB of RAM and 1 cpu in the San Francisco region.       
- A mock SMSC server was deployed on a $5/month digitalocean server with 1GB of RAM and 1 cpu in the Amsterdam region.     
- A redis server was also deployed to the same $5/month digitalocean server in the Amsterdam region.   
- The ping latency between the `naz` server in Sanfrancisco and the SMSC server in Amsterdam was about `154 ms`    
- Approximately 100,000 messages were queued on the redis server.   
- `naz-cli` would consume the messages from the redis queue and send them out to the SMSC.   
- In a loop; the `SMSC` would run for a duration of between 13-16 minutes stop for a duration of 1-3 minutes then continue etc.
- In a loop; the `redis server` would run for a duration of between 13-16 minutes stop for a duration of 1-3 minutes then continue etc.
- All this while, `naz-cli` is still accessing the redis server and SMSC, re-establishing connections when neccessary.
- All logs from `naz` were been sent to a timescaleDB container for later analysis.   
- Container/host and custom metrics were also been sent to a prometheus container for later analysis.  

#### B.
- The experiment was repeated as above, however this time around; the SMSC and redis server were let to have near 100% uptime.

### Results:
- TODO


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
Copy (SELECT * FROM logs WHERE length(logs.error) > 0 ORDER BY timestamp DESC) To '/tmp/errors.csv' With CSV DELIMITER ',';
cp /tmp/errors.csv /usr/src/app/
```

```sh
          event          |   log_id    |                error
-------------------------+-------------+--------------------------------------
 naz.Client.send_data    | 405-jctnhvo | [Errno 104] Connection reset by peer
 naz.Client.receive_data |             | [Errno 104] Connection reset by peer
 naz.Client.send_data    | 78-zbtrpxw  | [Errno 104] Connection reset by peer
 ```

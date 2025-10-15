# anomaly-detection-server

## Setup locally

```bash
cp .env.example .env
```

```bash
docker compose --file docker-compose-local.yml up
```


### Load data

```bash
docker exec -it anomaly-detector-server sh
```

```bash
uv run python load_data.py
```


## Query performance 

Primary query looks like the following

```sql
EXPLAIN ANALYZE
SELECT
    transactions.amount,
    transactions.currency,
    transactions.txn_date,
    transactions.status,
    transactions.meta_data,
    transactions.id,
    transactions.user_id
FROM
    transactions
WHERE
    transactions.user_id = '4aed997e-ee19-4a56-9906-05dc8786e7fd'
    AND transactions.txn_date >= '2025-09-15T16:12:34.043621Z'
    AND transactions.txn_date <= '2025-10-15T16:12:34.043676Z'
    AND transactions.amount >= 1.00
    AND transactions.amount <= 100000.00
ORDER BY
    transactions.txn_date DESC,
    transactions.id ASC
LIMIT 100;
```

output of explain analyze

```bash
QUERY PLAN
--------------------------------------------------------------------------------------------------
Limit  (cost=3.61..325.85 rows=100 width=79) (actual time=0.182..0.271 rows=100 loops=1)
  ->  Incremental Sort  (cost=3.61..3757.67 rows=1165 width=79) 
                        (actual time=0.180..0.263 rows=100 loops=1)
        Sort Key: txn_date DESC, id
        Presorted Key: txn_date
        Full-sort Groups: 4  Sort Method: quicksort  Average Memory: 29kB  Peak Memory: 29kB
        ->  Index Scan Backward using ix_user_date_amount_id on transactions 
                                     (cost=0.42..3705.24 rows=1165 width=79) 
                                     (actual time=0.046..0.218 rows=101 loops=1)
              Index Cond: ((user_id = '4aed997e-ee19-4a56-9906-05dc8786e7fd'::uuid) 
                           AND (txn_date >= '2025-09-15 21:42:34.043621+05:30'::timestamp 
                                            with time zone) 
                           AND (txn_date <= '2025-10-15 21:42:34.043676+05:30'::timestamp 
                                            with time zone) 
                           AND (amount > ...))
Planning Time: 0.191 ms
Execution Time: 0.337 ms
```
# PostgreSQL Documentation

## Overview
PostgreSQL is a powerful, open-source object-relational database system known for its reliability, feature robustness, and standards compliance. It provides advanced SQL capabilities, extensibility, and support for both relational and non-relational data models.

## Database Management

### Create Database

```sql
CREATE DATABASE my_database
    OWNER = db_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_GB.UTF-8'
    LC_CTYPE = 'en_GB.UTF-8'
    TEMPLATE = template0
    CONNECTION LIMIT = -1;
```

### Use/Connect to Database

```sql
\c database_name  -- psql command
```

### Alter Database

```sql
ALTER DATABASE my_database RENAME TO new_database_name;

ALTER DATABASE my_database OWNER TO new_owner;

ALTER DATABASE my_database SET TABLESPACE new_tablespace;

-- Set configuration parameters
ALTER DATABASE my_database 
SET configuration_parameter = value;
```

### Drop Database

```sql
DROP DATABASE IF EXISTS my_database WITH (FORCE);
```

## Basic SQL Syntax

### Create Table

```sql
CREATE TABLE products (
    product_no SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price NUMERIC CHECK (price > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Insert Data

```sql
INSERT INTO products (name, price)
VALUES ('Widget', 19.99), ('Gadget', 29.99);
```

### Select Data

```sql
SELECT column1, column2
FROM table_name
WHERE condition
ORDER BY column1;
```

### Update Data

```sql
UPDATE products
SET price = price * 1.1
WHERE category = 'Electronics';
```

### Join Operations

```sql
SELECT 
    orders.order_id,
    customers.customer_name,
    products.product_name
FROM orders
JOIN customers ON orders.customer_id = customers.customer_id
JOIN order_items ON orders.order_id = order_items.order_id
JOIN products ON order_items.product_id = products.product_id;
```

## Advanced Features

### Recursive Common Table Expressions (CTEs)

#### Basic Graph Traversal

```sql
WITH RECURSIVE search_graph(id, link, data, depth) AS (
    -- Base case
    SELECT g.id, g.link, g.data, 1
    FROM graph g
  UNION ALL
    -- Recursive case
    SELECT g.id, g.link, g.data, sg.depth + 1
    FROM graph g, search_graph sg
    WHERE g.id = sg.link
)
SELECT * FROM search_graph;
```

#### Cycle Detection

```sql
WITH RECURSIVE search_graph(id, link, data, depth, path, cycle) AS (
    SELECT g.id, g.link, g.data, 1,
      ARRAY[ROW(g.f1, g.f2)],
      false
    FROM graph g
  UNION ALL
    SELECT g.id, g.link, g.data, sg.depth + 1,
      path || ROW(g.f1, g.f2),
      ROW(g.f1, g.f2) = ANY(path)
    FROM graph g, search_graph sg
    WHERE g.id = sg.link AND NOT cycle
)
SELECT * FROM search_graph;
```

### JSON/JSONB Support

PostgreSQL provides excellent JSON support:

#### Query JSONB for Key-Value Containment

```sql
SELECT jdoc->'guid', jdoc->'name' 
FROM api 
WHERE jdoc @> '{"company": "Magnafone"}';
```

#### Query JSONB for Array Elements

```sql
SELECT jdoc->'guid', jdoc->'name' 
FROM api 
WHERE jdoc @> '{"tags": ["qui"]}';
```

### Full-Text Search

#### Basic Text Search

```sql
SELECT 'a fat cat sat on a mat and ate a fat rat'::tsvector 
    @@ 'cat & rat'::tsquery;
-- Returns: t (true)
```

#### Text Search with Normalization

```sql
SELECT to_tsvector('english', 'The quick brown fox') 
    @@ to_tsquery('english', 'fox');
```

### Extensions

#### Create Extension

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### Schemas

#### Full Qualified Names

```sql
-- database.schema.table (database must match current connection)
SELECT * FROM public.users;
SELECT * FROM schema_name.table_name;
```

## Roles and Permissions

### Create Role

```sql
CREATE ROLE app_user WITH LOGIN PASSWORD 'secure_password';
```

### Grant Privileges

```sql
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_user;
```

### Revoke Privileges

```sql
REVOKE DELETE ON products FROM app_user;
```

## Advanced Query Techniques

### GROUPING SETS, CUBE, ROLLUP

```sql
-- CUBE generates all possible grouping combinations
SELECT 
    region, product, SUM(sales)
FROM sales_data
GROUP BY CUBE(region, product);

-- ROLLUP generates hierarchical groupings
SELECT 
    year, quarter, SUM(revenue)
FROM financial_data
GROUP BY ROLLUP(year, quarter);
```

### Window Functions

```sql
SELECT 
    employee_name,
    department,
    salary,
    AVG(salary) OVER (PARTITION BY department) AS dept_avg_salary,
    RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS salary_rank
FROM employees;
```

## SQL Comments

```sql
-- Single-line comment

/* 
 Multi-line comment
 spanning multiple lines
*/
```

## Embedded SQL (ECPG)

PostgreSQL supports embedded SQL in C programs:

```c
EXEC SQL CONNECT TO mydb@sql.mydomain.com;

EXEC SQL SELECT name FROM users WHERE id = 1 INTO :employee_name;

EXEC SQL INSERT INTO users (name, email) 
VALUES ('Alice', 'alice@example.com');

EXEC SQL DISCONNECT;
```

## Performance and Optimization

### EXPLAIN and ANALYZE

```sql
EXPLAIN ANALYZE
SELECT * FROM large_table 
WHERE indexed_column = 'value';
```

### Indexes

```sql
-- B-tree index (default)
CREATE INDEX idx_users_email ON users(email);

-- GIN index for JSONB
CREATE INDEX idx_api_jdoc ON api USING GIN(jdoc);

-- GiST index for full-text search
CREATE INDEX idx_documents_tsvector 
ON documents USING GiST(to_tsvector('english', content));
```

## PostgreSQL Data Types

- **Numeric**: INTEGER, BIGINT, NUMERIC, REAL, DOUBLE PRECISION
- **Text**: VARCHAR, CHAR, TEXT
- **Date/Time**: DATE, TIME, TIMESTAMP, INTERVAL
- **Boolean**: BOOLEAN
- **JSON**: JSON, JSONB (binary JSON)
- **Arrays**: INTEGER[], TEXT[]
- **Geometric**: POINT, LINE, POLYGON
- **Network**: INET, CIDR, MACADDR
- **UUID**: UUID
- **XML**: XML

## ltree Extension (Hierarchical Data)

PostgreSQL provides the ltree extension for hierarchical data:

### Basic Path Matching

```sql
-- Match exact label path
SELECT * FROM tree WHERE path ~ 'Top.Science.Astronomy';

-- Match any path containing label
SELECT * FROM tree WHERE path ~ '*.Astronomy.*';

-- Match paths ending with label
SELECT * FROM tree WHERE path ~ '*.Astronomy';
```

### lquery Patterns

```sql
-- Complex pattern matching
SELECT * FROM tree 
WHERE path ~ 'Top.*{0,2}.sport*@.!football|tennis{1,}.Russ*|Spain';
```

## Comparison with Graph Databases

### PostgreSQL Strengths
1. **Mature RDBMS**: Decades of development and optimization
2. **ACID Compliance**: Strong transactional guarantees
3. **Rich Type System**: Extensive built-in and custom types
4. **Extensibility**: PostGIS, ltree, pg_trgm, and many more
5. **Standards Compliance**: Strong SQL standard adherence

### PostgreSQL for Graph-Like Data
- **Recursive CTEs**: Can traverse hierarchical/graph structures
- **ltree Extension**: Optimised for tree hierarchies
- **JSONB**: Flexible schema for semi-structured data
- **Foreign Keys**: Define relationships between entities

### Limitations for Graph Workloads
1. **Performance**: Join-heavy queries less efficient than native graph traversal
2. **Relationship Complexity**: Many-to-many relationships require junction tables
3. **Path Queries**: Recursive CTEs less optimised than Cypher pattern matching
4. **Graph Algorithms**: Limited built-in support compared to Neo4j GDS

### When to Choose PostgreSQL
1. **Complex Transactions**: ACID requirements with complex business logic
2. **Structured Data**: Well-defined schema with relational integrity
3. **Geospatial Data**: PostGIS for location-based queries
4. **Hybrid Workloads**: Mix of relational and hierarchical data
5. **Cost**: Free, open-source with no licensing costs

### When to Choose Neo4j
1. **Highly Connected Data**: Social networks, knowledge graphs
2. **Relationship-Centric**: Queries focusing on connections
3. **Pattern Matching**: Complex path finding
4. **Graph Algorithms**: PageRank, community detection, centrality
5. **Performance**: Sub-millisecond graph traversals

## PostgreSQL for PlasticFlower Context

While Neo4j is the core database for PlasticFlower, PostgreSQL knowledge is valuable for:
- **Data Migration**: ETL from relational systems
- **Hybrid Architecture**: Transactional data in PostgreSQL, relationships in Neo4j
- **Comparison Benchmarking**: Understanding graph vs. relational trade-offs
- **User Onboarding**: Helping SQL users transition to Cypher

## Connection and Client Libraries

### psql Command-Line

```bash
psql -h localhost -U username -d database_name
```

### Python (psycopg2)

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="mydb",
    user="user",
    password="password"
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM users WHERE active = true")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
```

## Backup and Restore

### Backup with pg_dump

```bash
pg_dump database_name > backup.sql

# Custom format (compressed)
pg_dump -Fc database_name > backup.dump
```

### Restore with psql

```bash
psql database_name < backup.sql

# Custom format
pg_restore -d database_name backup.dump
```

## Resources

- **Official Documentation**: https://www.postgresql.org/docs/
- **Tutorial**: https://www.postgresql.org/docs/current/tutorial.html
- **SQL Reference**: https://www.postgresql.org/docs/current/sql.html
- **PostGIS**: https://postgis.net/documentation/
- **PostgreSQL Wiki**: https://wiki.postgresql.org/

## Key PostgreSQL Concepts

1. **MVCC**: Multi-Version Concurrency Control for high concurrency
2. **WAL**: Write-Ahead Logging for crash recovery
3. **Vacuum**: Maintenance process for space reclamation
4. **Extensions**: Modular architecture for additional functionality
5. **Foreign Data Wrappers**: Query external data sources as tables






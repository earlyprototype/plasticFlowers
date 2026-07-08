# MySQL Documentation

## Overview
MySQL is a powerful and widely-used open-source relational database management system (RDBMS) that provides a robust SQL interface for data management. This documentation covers core MySQL concepts relevant for comparison with graph databases.

## Basic SQL Syntax

### Database Management

#### Create Database

```sql
CREATE DATABASE my_new_database
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
```

#### Use Database

```sql
USE my_database;
```

#### Drop Database

```sql
DROP DATABASE IF EXISTS my_database;
```

### SELECT Statements

#### Basic SELECT

```sql
SELECT column1, column2, ...
FROM table_name
WHERE condition;
```

#### Pattern Matching with LIKE

```sql
SELECT * FROM users WHERE name LIKE 'A%';
```

#### JOIN Operations

```sql
SELECT 
    orders.order_id,
    customers.customer_name
FROM 
    orders
JOIN 
    customers ON orders.customer_id = customers.customer_id;
```

### Data Definition Language (DDL)

#### Create Table

```sql
CREATE TABLE example_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Insert Data

```sql
INSERT INTO table_name (column1, column2, column3)
VALUES (value1, value2, value3);
```

#### Update Data

```sql
UPDATE MY_TABLE SET A = 5 WHERE condition = 'value';
```

### Subqueries

#### Basic Subquery Syntax

```sql
SELECT column1 FROM table1
WHERE column2 = (SELECT column FROM table2 WHERE condition);
```

#### Subqueries with ANY/SOME

```sql
SELECT * FROM tt
WHERE b > ANY (SELECT * FROM ts);
```

#### Subqueries with ALL

```sql
operand comparison_operator ALL (subquery)
```

## INFORMATION_SCHEMA

MySQL provides a standardised way to query database metadata:

### Query Table Information

```sql
SELECT TABLE_SCHEMA, TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE';
```

### Query Column Information

```sql
SELECT COLUMN_NAME 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'your_table_name';
```

### Query Routines

```sql
SELECT ROUTINE_NAME, ROUTINE_TYPE 
FROM INFORMATION_SCHEMA.ROUTINES 
WHERE ROUTINE_SCHEMA = SCHEMA();
```

## Full-Text Search

MySQL supports full-text search capabilities:

### Basic Syntax

```sql
MATCH (col1, col2, ...) AGAINST (expr [search_modifier])

-- Search modifiers:
-- IN NATURAL LANGUAGE MODE
-- IN NATURAL LANGUAGE MODE WITH QUERY EXPANSION
-- IN BOOLEAN MODE
-- WITH QUERY EXPANSION
```

## Comparison Operators

Basic comparison operators in MySQL:

```sql
=   -- Equal
>   -- Greater than
<   -- Less than
>=  -- Greater than or equal
<=  -- Less than or equal
<>  -- Not equal
!=  -- Not equal (alternative)
```

## SQL Comments

```sql
-- This is a single-line comment

/* 
 This is a multi-line comment
 spanning multiple lines
*/
```

## Prepared Statements

Prepared statements help prevent SQL injection and improve performance:

```sql
PREPARE stmt FROM 'SELECT ? INTO @a';
EXECUTE stmt USING @a;
DEALLOCATE PREPARE stmt;
```

## Database Backup with mysqldump

### Dump Specific Database

```bash
mysqldump [options] db_name [tbl_name ...] > backup.sql
```

### Dump Multiple Databases

```bash
mysqldump [options] --databases db_name1 db_name2 ... > backup.sql
```

### Dump All Databases

```bash
mysqldump [options] --all-databases > backup.sql
```

## Character Sets and Collations

### Specify for Database

```sql
CREATE DATABASE db_name
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
```

### Alter Database

```sql
ALTER DATABASE db_name
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
```

## Connection Management

### MySQL Connection (Ruby Example)

```ruby
require 'mysql2'

# Establish connection
client = Mysql2::Client.new(
  :host => "localhost", 
  :username => "root", 
  :password => "your_password"
)

# Execute query
results = client.query("SELECT * FROM your_table")

# Process results
results.each do |row|
  puts row['column_name']
end
```

## MySQL Extensions to Standard SQL

MySQL provides several extensions beyond standard SQL:
- Auto-increment columns
- LIMIT clause for result set pagination
- INSERT ... ON DUPLICATE KEY UPDATE
- REPLACE statement
- Multiple-table DELETE and UPDATE

## Performance: EXPLAIN Statement

Analyse query performance with EXPLAIN:

```sql
EXPLAIN SELECT ... FROM INFORMATION_SCHEMA.TABLES;
```

## VALUES Statement

Construct a table from row values:

```sql
VALUES 
    ROW(1, 'Alice', 'alice@example.com'),
    ROW(2, 'Bob', 'bob@example.com'),
    ROW(3, 'Charlie', 'charlie@example.com')
ORDER BY column_index
LIMIT number;
```

## Comparison with Graph Databases

### Relational Model (MySQL)
- **Structure**: Tables with rows and columns
- **Relationships**: Defined via foreign keys
- **Queries**: Join-based operations
- **Best For**: Structured data, transactional systems, reporting

### Graph Model (Neo4j)
- **Structure**: Nodes and relationships
- **Relationships**: First-class citizens with properties
- **Queries**: Pattern matching (Cypher)
- **Best For**: Highly connected data, relationship-focused queries, network analysis

### When to Choose MySQL
1. **Structured Data**: Well-defined schema with predictable structure
2. **Transactions**: ACID compliance requirements
3. **Simple Relationships**: Limited relationship complexity
4. **Reporting**: Aggregation and analytics on tabular data
5. **Maturity**: Established tooling and widespread expertise

### When to Choose Neo4j
1. **Complex Relationships**: Many-to-many connections
2. **Path Queries**: Finding connections between entities
3. **Graph Algorithms**: Centrality, community detection
4. **Semantic Search**: Vector-based similarity
5. **Flexible Schema**: Evolving data models

## MySQL for PlasticFlower Context

While Neo4j is the primary database for PlasticFlower's graph-based knowledge representation, understanding MySQL is valuable for:
- **Migration scenarios**: Users may import data from relational systems
- **Hybrid architectures**: Transactional data in MySQL, relationships in Neo4j
- **Comparison documentation**: Helping users understand the graph paradigm
- **Integration patterns**: ETL pipelines from MySQL to Neo4j

## Resources

- **Official Documentation**: https://dev.mysql.com/doc/
- **Reference Manual**: https://dev.mysql.com/doc/refman/9.4/en/
- **MySQL Connector/Python**: https://dev.mysql.com/doc/connector-python/
- **Performance Tuning**: https://dev.mysql.com/doc/refman/9.4/en/optimization.html

## Key MySQL Concepts

1. **ACID Compliance**: Atomicity, Consistency, Isolation, Durability
2. **Indexing**: B-tree indexes for fast lookups
3. **Transactions**: BEGIN, COMMIT, ROLLBACK
4. **Stored Procedures**: Server-side logic execution
5. **Replication**: Master-slave and master-master topologies






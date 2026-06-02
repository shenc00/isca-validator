-- nb_isca_otif_bad_example
-- This notebook intentionally violates multiple ISCA standards for testing.

-- VIOLATION SQL-02: lowercase keywords
select * from s_isca.otif_orders a
where a.region = 'APAC';

-- VIOLATION SQL-01: SELECT *
SELECT *
FROM s_isca.sales_order b
WHERE b.status = 'OPEN';

-- VIOLATION SQL-08: single-letter alias
SELECT b.SalesDocumentNumber
FROM s_isca.sales_order b
LEFT JOIN s_isca.customer c ON b.CustomerNumber = c.CustomerNumber;

-- VIOLATION SQL-05: IFNULL
SELECT IFNULL(one.Region, 'UNKNOWN') AS Region
FROM s_isca.sales_order one;

-- VIOLATION SQL-06: LTRIM + RTRIM together
SELECT LTRIM(RTRIM(one.SalesOrg)) AS sales_org_trimmed
FROM s_isca.sales_order one;

-- VIOLATION SQL-03: ORDER BY position number
SELECT one.SalesDocumentNumber, one.CustomerNumber
FROM s_isca.sales_order one
ORDER BY 1, 2;

-- VIOLATION SQL-04: missing schema prefix
SELECT one.SalesDocumentNumber
FROM sales_order one;

-- VIOLATION NAME-COL-03 + NAME-COL-04: snake_case and lowercase column aliases
SELECT one.SalesDocumentNumber AS sales_document_number,
       one.CustomerNumber AS customerNumber
FROM s_isca.sales_order one;

-- VIOLATION SQL-07: DROP + CREATE TABLE
DROP TABLE s_isca.tmp_result;
CREATE TABLE s_isca.tmp_result AS
SELECT one.SalesDocumentNumber
FROM s_isca.sales_order one;

-- VIOLATION NAME-VIEW-01: view without v_ prefix
CREATE OR REPLACE VIEW s_isca.otif_summary AS
SELECT one.Region, COUNT(*) AS TotalOrders
FROM s_isca.sales_order one
GROUP BY one.Region;

-- VIOLATION NAME-TMPVIEW-01: temp view without tv_ prefix
CREATE TEMPORARY VIEW staging_orders AS
SELECT one.SalesDocumentNumber
FROM s_isca.sales_order one;

-- VIOLATION SQL-10: intermediate table instead of temp view
CREATE TABLE s_isca.intermediate_calc AS
SELECT one.Region, SUM(one.OrderValue) AS TotalValue
FROM s_isca.sales_order one
GROUP BY one.Region;

-- VIOLATION SQL-11: UDF definition
CREATE OR REPLACE FUNCTION normalize_region(region STRING)
RETURNS STRING
LANGUAGE SQL
RETURN UPPER(TRIM(region));

-- VIOLATION NAME-TBL-01: uppercase table name
CREATE TABLE s_isca.SalesOrderSummary AS
SELECT one.Region
FROM s_isca.sales_order one;

-- CORRECT example (no violations expected)
INSERT OVERWRITE TABLE s_isca.otif_kpi
SELECT
    one.SalesDocumentNumber AS SalesDocumentNumber,
    one.CustomerNumber AS CustomerNumber,
    COALESCE(one.Region, 'UNKNOWN') AS Region,
    TRIM(one.SalesOrg) AS SalesOrg
FROM s_isca.sales_order one
LEFT JOIN s_isca.customer_master two
    ON one.CustomerNumber = two.CustomerNumber
WHERE one.Status = 'OPEN'
ORDER BY one.SalesDocumentNumber;

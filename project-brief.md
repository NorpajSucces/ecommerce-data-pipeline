# Project Brief — V1

## Project Goal
Build a local batch pipeline that prepares Olist e-commerce
data for monthly transaction analysis.

## Target User
A data analyst who needs consistent monthly transaction summaries.

## Problem
Order, order item, and customer data are stored in separate CSV files.
The data needs validation, integration, and transformation before
it can support reliable analysis.

## Data Sources
- Orders
- Order items
- Customers

## Expected Output
A monthly summary view containing:
- Order month
- Number of orders
- Total item value, excluding freight

## Initial Scope
- Use historical CSV data.
- Load data into a local PostgreSQL database using Python.
- Transform data using SQL.
- Run the pipeline manually.

## Completion Criteria
- The three source datasets are loaded successfully.
- Relevant data quality issues are identified and documented.
- The monthly summary view is created.
- Summary results are checked against the source data.

## Confirmed V1 Decisions
- Include delivered orders in monthly analytics.
- Group orders by `order_purchase_timestamp`.
- Sum item prices and exclude freight.
- Preserve all source order statuses in staging.
- Convert empty CSV fields to SQL NULL.
- Stop loading on malformed records or database constraint violations.
- Reject initial loading when the target table is not empty.
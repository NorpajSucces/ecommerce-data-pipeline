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
A monthly summary table containing:
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
- The monthly summary table is created.
- Summary results are checked against the source data.

## Decisions to Confirm After Data Inspection
- Which order statuses should be included?
- Which timestamp should define the order month?
- How should missing or invalid values be handled?
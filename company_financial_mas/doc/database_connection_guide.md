# TimescaleDB Connection Guide

This guide provides instructions for setting up and querying the TimescaleDB instance for the Company Financial MAS project.

## Database Structure

The database consists of three main tables:

1. **financial_metrics** - Time-series table for revenue and margin data
   - Primary time column: `date` (TIMESTAMP)
   - Columns: revenue, growth_rate, gross_margin, operating_margin, net_profit_margin

2. **cash_flow_metrics** - Time-series table for cash flow data
   - Primary time column: `date` (TIMESTAMP)
   - Columns: operating_cash_flow, investing_cash_flow, financing_cash_flow, net_cash_flow

3. **annual_metrics** - Regular table for annual report data
   - Primary key: `year` (INT)
   - Columns: revenue, net_income, eps, total_assets, total_liabilities, shareholders_equity, report_path

## Setting Up the Database

1. Run the SQL setup script in `company_financial_mas/data/db/db_setup_guide.sql` to create the tables and necessary indexes.

2. Import the CSV data using the commands at the end of the setup script.

## Fixing Common Issues

### DateTime JSON Serialization Error

If you encounter a JSON serialization error with datetime objects, make sure that:

1. The `DateTimeEncoder` class is properly implemented in `memory_database_interaction.py`.

2. All `json.dumps()` calls use the custom encoder: `json.dumps(data, cls=DateTimeEncoder)`.

### Database Connection Issues

If you encounter connection issues:

1. Verify the credentials in your `timescale-db-61642-credentials.env` file.

2. Check that the database is accessible from your network.

3. Confirm that the tables exist in the database using:
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public';
   ```

## Testing the Connection

You can test your database connection using:

```bash
aiq run --config_file company_financial_mas/configs/memory_database_test.yml --input "What is company last 4 years profits?"
```

This should query the TimescaleDB and return profit information from the financial_metrics table.

## Sample Queries

Here are some sample queries that work well with the memory_database_interaction agent:

### Profit Data
```
What is the company's profit margin trend over the last 4 years?
What was our quarterly profit for 2023?
```

### Revenue Data
```
What was our quarterly revenue for the last two years?
What was our total revenue for 2023?
```

### Cash Flow Data
```
Show me our cash flow data for the last year.
What was our net cash flow in the last quarter?
```

### Annual Report Data
```
Show me the annual financial metrics for the last 2 years.
What was our earnings per share in 2023?
``` 
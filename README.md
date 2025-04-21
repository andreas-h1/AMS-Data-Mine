# AMS_DATA_MINE

This repository contains all the code and configuration needed to migrate a legacy FileMaker Pro database to PostgreSQL, import and consolidate CSV survey data, and manage automated backups.

## Project Structure

```bash
├── postgres/               # PostgreSQL server setup and configuration (e.g., Docker Compose, init scripts)
│   ├── docker-compose.yml
│   └── initdb/             # SQL files to initialize the database schema
├── csv_import/             # Scripts for importing CSV files into staging tables
│   └── import_csvs.sh      # Bulk imports all survey CSVs for DGdata and EENDR
├── sql/                    # SQL migration and data-merging scripts
│   ├── migrate_fmp.sql     # Translates FileMaker Pro exports into PostgreSQL-ready tables
│   ├── merge_dgdata.sql    # Unifies DGdata surveys 2010–2015 into one table
│   ├── merge_eendr.sql     # Unifies EENDR surveys 2010–2015 into one table
│   └── merge_surveys.sql   # Combines DGdata and EENDR merged tables into a final survey table
├── backups/                # Backup scripts and cron job configuration
│   ├── backup.sh           # Runs pg_dump and prunes old backups
│   └── crontab.entry       # Cron definition for daily backups at 2 AM
└── README.md               # This file
```  

## Prerequisites

- PostgreSQL 12 or newer (local or Docker)
- Docker & Docker Compose (if using containerized setup)
- Bash shell
- Cron daemon for scheduled backups

## 1. Setup PostgreSQL Server

1. Clone this repository locally.
2. Navigate to the `postgres/` directory:
   ```bash
   cd postgres/
   ```
3. Launch PostgreSQL (Docker Compose):
   ```bash
   docker-compose up -d
   ```
4. Verify connectivity:
   ```bash
   psql -h localhost -U <your_user> -d <your_db>
   ```

## 2. Data Migration from FileMaker Pro

1. Export FileMaker tables as CSV files.
2. Use the SQL in `sql/migrate_fmp.sql` to create corresponding tables and load data.
   ```bash
   psql -h localhost -U <user> -d <db> -f sql/migrate_fmp.sql
   ```

## 3. Importing Survey CSV Data

The `csv_import/import_csvs.sh` script bulk-loads all DGdata and EENDR CSVs (2010–2015) into staging tables.

```bash
cd csv_import/
./import_csvs.sh
```

This script assumes the CSV files follow the naming convention `dgdata_<year>.csv` and `eendr_<year>.csv`.

## 4. Merging Survey Data

### 4.1 Merge DGdata (2010–2015)

**File: `sql/merge_dgdata.sql`**
```sql
-- Combine individual DGdata tables into one
DROP TABLE IF EXISTS dgdata_merged;
CREATE TABLE dgdata_merged AS
  SELECT * FROM dgdata_2010
  UNION ALL SELECT * FROM dgdata_2011
  UNION ALL SELECT * FROM dgdata_2012
  UNION ALL SELECT * FROM dgdata_2013
  UNION ALL SELECT * FROM dgdata_2014
  UNION ALL SELECT * FROM dgdata_2015;
```  

### 4.2 Merge EENDR (2010–2015)

**File: `sql/merge_eendr.sql`**
```sql
DROP TABLE IF EXISTS eendr_merged;
CREATE TABLE eendr_merged AS
  SELECT * FROM eendr_2010
  UNION ALL SELECT * FROM eendr_2011
  UNION ALL SELECT * FROM eendr_2012
  UNION ALL SELECT * FROM eendr_2013
  UNION ALL SELECT * FROM eendr_2014
  UNION ALL SELECT * FROM eendr_2015;
```  

### 4.3 Combine into Final Survey Table

**File: `sql/merge_surveys.sql`**
```sql
-- Create a unified survey table with NULLs for missing columns
DROP TABLE IF EXISTS surveys_final;
CREATE TABLE surveys_final AS
  SELECT
    d.survey_id,
    d.common_field1,
    d.common_field2,
    d.unique_dg_field,
    NULL          AS unique_eendr_field
  FROM dgdata_merged d
  UNION ALL
  SELECT
    e.survey_id,
    e.common_field1,
    e.common_field2,
    NULL         AS unique_dg_field,
    e.unique_eendr_field
  FROM eendr_merged e;

-- Alternatively, using a full outer join
-- to align on survey_id and preserve all columns
-- DROP TABLE IF EXISTS surveys_final;
-- CREATE TABLE surveys_final AS
-- SELECT COALESCE(d.survey_id, e.survey_id) AS survey_id,
--        d.common_field1,
--        e.common_field2,
--        d.unique_dg_field,
--        e.unique_eendr_field
-- FROM dgdata_merged d
-- FULL OUTER JOIN eendr_merged e USING (survey_id);
```  

## 5. Automated Backups

A daily backup is scheduled via cron to run at 2 AM.  

**File: `backups/crontab.entry`**
```cron
# m h dom mon dow command
0 2 * * * /usr/local/bin/backup.sh
```  

**File: `backups/backup.sh`**
```bash
#!/usr/bin/env bash
# PostgreSQL connection details
PGUSER="your_pg_user"
PGPASSWORD="your_pg_password"
PGHOST="localhost"
PGPORT="5432"
DBNAME="ams_data_mine"

# Backup directory and rotation
BACKUP_DIR="/var/backups/ams_data_mine"
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate filename with date
DATE_STR=$(date +"%F")
BACKUP_FILE="$BACKUP_DIR/${DBNAME}_$DATE_STR.sql"

# Perform the dump
pg_dump -U "$PGUSER" -h "$PGHOST" -p "$PGPORT" "$DBNAME" > "$BACKUP_FILE"

# Remove backups older than retention period
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete
```  

## Contributing

1. Fork the repository.  
2. Create a feature branch (`git checkout -b feature/YourFeature`).  
3. Commit your changes (`git commit -m 'Add new feature'`).  
4. Push to the branch (`git push origin feature/YourFeature`).  
5. Open a pull request.

## License

This project is released under the MIT License. See [LICENSE](LICENSE) for details.


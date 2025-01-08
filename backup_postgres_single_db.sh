#!/bin/bash


# Load variables from .env
source .env

# Configuration
CONTAINER_NAME=postgres    # Replace with your container name
POSTGRES_USER=$POSTGRES_USER               # Replace with your PostgreSQL username
POSTGRES_PASSWORD=$POSTGRES_PASSWORD       # Replace with your PostgreSQL password (if required)
POSTGRES_DB=ams                 # Replace with the database you want to back up
BACKUP_DIR=/home/ams/postgres/backups          # Directory to store backup files
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
BACKUP_FILE=$BACKUP_DIR/${POSTGRES_DB}_backup_$TIMESTAMP.sql

# Ensure the backup directory exists
mkdir -p $BACKUP_DIR

# Execute pg_dump inside the Docker container
docker exec -e PGPASSWORD=$POSTGRES_PASSWORD -t $CONTAINER_NAME pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_FILE

# Optional: Compress the backup file to save space
gzip $BACKUP_FILE

# Optional: Remove backups older than 7 days
#find $BACKUP_DIR -type f -name "${POSTGRES_DB}_backup_*.sql.gz" -mtime +7 -delete

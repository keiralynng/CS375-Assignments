#!/usr/bin/env bash

set -e

echo "======================================"
echo "Rebuilding AI Lakehouse"
echo "======================================"


echo
echo "Starting Docker services..."

docker compose up -d


echo
echo "Installing Python dependencies..."

docker compose exec -T lab \
    pip install -r requirements.txt


echo
echo "Preparing RustFS bucket..."

docker compose exec -T lab \
    python scripts/create_bucket.py


echo
echo "Removing old DuckLake catalog..."

docker compose exec -T lab \
    rm -f /workspace/metadata.ducklake


echo
echo "Creating DuckLake schemas..."

docker compose exec -T lab \
    python -c "
import duckdb

con = duckdb.connect()

con.execute(
    open(
        'sql/00_attach.sql',
        encoding='utf-8'
    ).read()
)

print('DuckLake attached.')
"


echo
echo "Ingesting COCO..."

docker compose exec -T lab \
    python scripts/ingest_coco.py


echo
echo "Ingesting VisDrone..."

docker compose exec -T lab \
    python scripts/ingest_visdrone.py


echo
echo "Building Silver layer..."

docker compose exec -T lab \
    python -c "
import duckdb

con = duckdb.connect()

con.execute(
    open(
        'sql/00_attach.sql',
        encoding='utf-8'
    ).read()
)

con.execute(
    open(
        'sql/20_silver.sql',
        encoding='utf-8'
    ).read()
)

print('Silver layer complete.')
"


echo
echo "Building Gold layer..."

docker compose exec -T lab \
    python -c "
import duckdb

con = duckdb.connect()

con.execute(
    open(
        'sql/00_attach.sql',
        encoding='utf-8'
    ).read()
)

con.execute(
    open(
        'sql/30_gold.sql',
        encoding='utf-8'
    ).read()
)

print('Gold layer complete.')
"


echo
echo "Running verification..."

docker compose exec -T lab \
    python -c "
import duckdb

con = duckdb.connect()

con.execute(
    open(
        'sql/00_attach.sql',
        encoding='utf-8'
    ).read()
)

print()
print('COCO gold rows:')
print(
    con.sql(
        'SELECT COUNT(*) FROM gold.coco_training'
    ).fetchdf()
)

print()
print('VisDrone gold rows:')
print(
    con.sql(
        'SELECT COUNT(*) FROM gold.visdrone_training'
    ).fetchdf()
)

print()
print('Snapshots:')
print(
    con.sql(
        \"SELECT MAX(snapshot_id) AS latest_snapshot FROM ducklake_snapshots('lake')\"
    ).fetchdf()
)
"


echo
echo "======================================"
echo "Lakehouse rebuild complete!"
echo "======================================"
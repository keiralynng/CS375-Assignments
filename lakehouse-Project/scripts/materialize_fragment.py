import os

import boto3
import duckdb


OUTPUT_DIR = "/data/local/materialized"

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True,
)


con = duckdb.connect()

con.execute(
    open(
        "sql/00_attach.sql",
        encoding="utf-8",
    ).read()
)


row = con.sql(
    """
    SELECT
        fragment_uri,
        sequence_name,
        fragment_id,
        n_objects
    FROM silver.visdrone_fragments
    WHERE n_objects > 20
    ORDER BY n_objects DESC
    LIMIT 1
    """
).fetchone()


fragment_uri = row[0]
sequence_name = row[1]
fragment_id = row[2]
n_objects = row[3]


print("Selected fragment:")
print(f"Sequence: {sequence_name}")
print(f"Fragment ID: {fragment_id}")
print(f"Objects: {n_objects}")
print(f"URI: {fragment_uri}")


prefix = "s3://lakehouse/"

if not fragment_uri.startswith(prefix):
    raise ValueError("Unexpected fragment URI")


object_key = fragment_uri[len(prefix):]


s3 = boto3.client(
    "s3",
    endpoint_url="http://rustfs:9000",
    aws_access_key_id="rustfsadmin",
    aws_secret_access_key="rustfsadmin",
)


local_path = os.path.join(
    OUTPUT_DIR,
    f"{sequence_name}_fragment_{fragment_id}.mp4",
)


print()
print("Downloading only the selected fragment...")


s3.download_file(
    "lakehouse",
    object_key,
    local_path,
)


print()
print("Materialization complete!")
print(f"Saved to: {local_path}")
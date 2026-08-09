import os

import duckdb
from datasets import Dataset


token = os.getenv("HF_TOKEN")

if not token:
    raise RuntimeError("HF_TOKEN is missing")


con = duckdb.connect()

con.execute(
    open(
        "sql/00_attach.sql",
        encoding="utf-8",
    ).read()
)


df = con.sql(
    """
    SELECT *
    FROM gold.coco_training
    """
).fetchdf()


print(f"Rows being published: {len(df)}")


dataset = Dataset.from_pandas(
    df,
    preserve_index=False,
)


print("Uploading dataset to Hugging Face...")


dataset.push_to_hub(
    "keiragool/lakehouse-coco-gold",
    token=token,
)


print("Upload complete!")
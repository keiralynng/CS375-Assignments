import boto3
import duckdb
from datasets import load_dataset


MAX_IMAGES = 100

print("Connecting to RustFS...")

s3 = boto3.client(
    "s3",
    endpoint_url="http://rustfs:9000",
    aws_access_key_id="rustfsadmin",
    aws_secret_access_key="rustfsadmin",
)

print("Loading COCO subset...")

dataset = load_dataset(
    "detection-datasets/coco",
    split="val",
    streaming=True,
)

image_rows = []
annotation_rows = []

for index, example in enumerate(dataset):
    if index >= MAX_IMAGES:
        break

    image = example["image"]
    image_id = int(example["image_id"])

    local_path = f"/data/local/coco_{image_id}.jpg"
    image.save(local_path, format="JPEG")

    object_key = f"assets/coco/images/coco_{image_id}.jpg"

    s3.upload_file(
        local_path,
        "lakehouse",
        object_key,
    )

    image_uri = f"s3://lakehouse/{object_key}"

    image_rows.append(
        (
            image_id,
            image_uri,
            int(example["width"]),
            int(example["height"]),
            "val",
        )
    )

    objects = example["objects"]

    for bbox_id, category, bbox, area in zip(
        objects["bbox_id"],
        objects["category"],
        objects["bbox"],
        objects["area"],
    ):
        x1, y1, x2, y2 = bbox

        annotation_rows.append(
            (
                int(bbox_id),
                image_id,
                image_uri,
                int(category),
                float(x1),
                float(y1),
                float(x2),
                float(y2),
                float(area),
            )
        )

    print(f"Processed image {index + 1}/{MAX_IMAGES}")


print("Creating DuckLake tables...")

con = duckdb.connect()
con.execute(open("sql/00_attach.sql").read())

con.execute(
    """
    CREATE OR REPLACE TABLE raw.coco_images (
        image_id BIGINT,
        image_uri VARCHAR,
        width INTEGER,
        height INTEGER,
        split VARCHAR
    )
    """
)

con.executemany(
    """
    INSERT INTO raw.coco_images
    VALUES (?, ?, ?, ?, ?)
    """,
    image_rows,
)

con.execute(
    """
    CREATE OR REPLACE TABLE raw.coco_annotations (
        bbox_id BIGINT,
        image_id BIGINT,
        image_uri VARCHAR,
        category_id INTEGER,
        x1 DOUBLE,
        y1 DOUBLE,
        x2 DOUBLE,
        y2 DOUBLE,
        area DOUBLE
    )
    """
)

con.executemany(
    """
    INSERT INTO raw.coco_annotations
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    annotation_rows,
)

print()
print("COCO ingestion complete!")
print()

print(
    con.sql(
        "SELECT COUNT(*) AS total_images FROM raw.coco_images"
    ).fetchdf()
)

print(
    con.sql(
        "SELECT COUNT(*) AS total_annotations FROM raw.coco_annotations"
    ).fetchdf()
)

print()
print(con.sql("SELECT * FROM raw.coco_annotations LIMIT 5").fetchdf())
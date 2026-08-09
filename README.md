# AI Lakehouse for Vision Datasets

## Overview

This project implements a versioned AI lakehouse for computer vision datasets using DuckDB, DuckLake, and RustFS.

The lakehouse stores large media files such as COCO images and VisDrone video fragments in RustFS object storage. DuckLake stores the structured metadata, annotations, fragment indexes, and references to those media objects.

The project follows a Medallion Architecture:

- Raw: ingested source metadata and annotations
- Silver: cleaned, deduplicated, and standardized data
- Gold: ML-ready datasets

The project also demonstrates DuckLake snapshots, time travel, schema evolution, version comparison, and rollback/restoration.

## Technologies

- Python 3.12
- DuckDB
- DuckLake
- RustFS
- Docker / Docker Compose
- Pandas
- PyArrow
- Hugging Face Datasets
- Boto3
- ImageIO / FFmpeg

## Datasets

### COCO

A 100-image subset of COCO is used.

The image bytes are stored in RustFS under:

```text
s3://lakehouse/assets/coco/images/
```

The Raw layer contains:

```text
raw.coco_images
raw.coco_annotations
```

The subset contains:

- 100 images
- 714 annotations

### VisDrone

The project uses two sequences from the VisDrone2019-VID validation dataset:

```text
uav0000086_00000_v
uav0000117_02622_v
```

The first 300 frames from each sequence are divided into fragments of 100 frames.

This produces six MP4 video fragments.

The video fragments are stored in RustFS under:

```text
s3://lakehouse/assets/visdrone/
```

The Raw layer contains:

```text
raw.visdrone_annotations
raw.visdrone_fragments
```

The selected subset contains:

- 600 processed frames
- 27,431 annotations
- 6 video fragments

## Architecture

The project separates large media files from structured metadata.

```text
COCO / VisDrone
       |
       v
Python ingestion
       |
       +--------------------+
       |                    |
       v                    v
    RustFS              DuckLake
 images/videos      metadata + URIs
                            |
                            v
                           Raw
                            |
                            v
                         Silver
                            |
                            v
                          Gold
                            |
                            v
                     Hugging Face
```

RustFS stores the large media objects while DuckLake stores metadata and `s3://` references to those objects.

## Medallion Layers

### Raw

The Raw layer preserves the ingested metadata.

Tables include:

```text
raw.coco_images
raw.coco_annotations
raw.visdrone_annotations
raw.visdrone_fragments
```

### Silver

The Silver layer performs cleaning, type normalization, and deduplication.

Tables include:

```text
silver.coco_images
silver.coco_annotations
silver.visdrone_annotations
silver.visdrone_fragments
```

Schema evolution is demonstrated by adding:

```text
object_density
```

to the VisDrone fragment data.

`object_density` represents the number of object annotations per frame in a fragment.

### Gold

The Gold layer contains ML-ready tables:

```text
gold.coco_training
gold.visdrone_training
```

The COCO Gold table contains 714 rows.

The VisDrone Gold table contains 6 fragment-level rows.

## Example Queries

### COCO

The following query finds images containing at least five annotated objects:

```sql
SELECT
    image_uri,
    COUNT(*) AS n_objects
FROM silver.coco_annotations
GROUP BY image_uri
HAVING COUNT(*) >= 5
ORDER BY n_objects DESC;
```

For the selected subset, the image with the highest annotation count was:

```text
coco_9590.jpg - 29 objects
```

### VisDrone

The following query selects fragments containing more than 20 object annotations:

```sql
SELECT
    fragment_uri,
    fragment_id,
    start_frame,
    end_frame,
    n_objects,
    object_density
FROM silver.visdrone_fragments
WHERE n_objects > 20
ORDER BY n_objects DESC;
```

The busiest fragment in the selected subset contained 5,502 annotations.

## DuckLake Versioning

DuckLake snapshots are used to preserve historical versions of the lakehouse.

A rollback experiment was performed on:

```text
silver.coco_annotations
```

The known-good snapshot was:

```text
Snapshot 11436
714 rows
```

A deliberately bad change deleted the annotations belonging to one COCO image.

This created:

```text
Snapshot 11437
694 rows
```

DuckLake time travel was used to query snapshot 11436 and confirm that the historical version still contained 714 rows.

The current table was then restored from snapshot 11436, creating:

```text
Snapshot 11438
714 rows
```

This demonstrates snapshot creation, time travel, comparison between versions, and restoration of a known-good version.

## Project Structure

```text
lakehouse-project/
├── docker-compose.yml
├── requirements.txt
├── rebuild.sh
│
├── scripts/
│   ├── create_bucket.py
│   ├── ingest_coco.py
│   ├── ingest_visdrone.py
│   ├── publish_gold.py
│   └── version_demo.py
│
├── sql/
│   ├── 00_attach.sql
│   ├── 20_silver.sql
│   ├── 30_gold.sql
│   └── 40_queries.sql
│
└── local-store/
    └── visdrone/
```

`local-store/` is excluded from Git because the original VisDrone files are large.

RustFS data and credentials are also excluded where appropriate.

## Running the Project

### Requirements

The machine should have:

- Docker Desktop
- Docker Compose
- WSL2 when running Docker Desktop on Windows
- Git

### Start the services

From the project directory:

```bash
docker compose up -d
```

Verify the containers:

```bash
docker compose ps
```

### Install Python dependencies

```bash
docker compose exec lab pip install -r requirements.txt
```

### Enter the lab container

```bash
docker compose exec lab bash
```

### Rebuild

A rebuild script is included:

```bash
bash rebuild.sh
```

The rebuild script:

1. Starts the Docker services.
2. Installs Python dependencies.
3. Prepares the RustFS bucket.
4. Creates the DuckLake catalog and schemas.
5. Ingests COCO.
6. Ingests VisDrone.
7. Builds the Silver layer.
8. Builds the Gold layer.
9. Runs verification queries.

The VisDrone validation files must be available under:

```text
local-store/visdrone/VisDrone2019-VID-val/
```

before running a complete rebuild.

## Hugging Face

The Gold COCO table is published as a Hugging Face dataset.

Dataset:

https://huggingface.co/datasets/keiragool/lakehouse-coco-gold 

The published dataset contains 714 ML-ready COCO annotation rows.

## Security

Secrets such as the Hugging Face access token are stored in `.env`.

`.env` is excluded from Git using `.gitignore`.

Access tokens should never be committed to the repository.

## Reproducibility

The project includes:

```text
requirements.txt
docker-compose.yml
rebuild.sh
```

These files document and automate the environment and lakehouse pipeline.

Large source datasets and generated RustFS object-storage files are intentionally excluded from the Git repository.
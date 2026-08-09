import csv
import os

import boto3
import duckdb
import imageio.v2 as imageio
import pandas as pd


BASE_DIR = "/data/local/visdrone/VisDrone2019-VID-val"

SEQUENCES = [
    "uav0000086_00000_v",
    "uav0000117_02622_v",
]

FRAGMENT_SIZE = 100
MAX_FRAMES_PER_SEQUENCE = 300
FPS = 25


s3 = boto3.client(
    "s3",
    endpoint_url="http://rustfs:9000",
    aws_access_key_id="rustfsadmin",
    aws_secret_access_key="rustfsadmin",
)


annotation_rows = []
fragment_rows = []


for sequence_name in SEQUENCES:
    sequence_dir = os.path.join(
        BASE_DIR,
        "sequences",
        sequence_name,
    )

    annotation_file = os.path.join(
        BASE_DIR,
        "annotations",
        f"{sequence_name}.txt",
    )

    print()
    print(f"Processing {sequence_name}...")

    frame_files = sorted(
        file_name
        for file_name in os.listdir(sequence_dir)
        if file_name.lower().endswith(".jpg")
    )

    frame_files = frame_files[:MAX_FRAMES_PER_SEQUENCE]

    total_frames = len(frame_files)

    print(f"Using {total_frames} frames")

    sequence_annotations = []

    with open(
        annotation_file,
        "r",
        encoding="utf-8",
    ) as file:
        reader = csv.reader(file)

        for row in reader:
            if len(row) < 10:
                continue

            frame_id = int(row[0])

            if frame_id > total_frames:
                continue

            target_id = int(row[1])

            bbox_x = float(row[2])
            bbox_y = float(row[3])
            bbox_width = float(row[4])
            bbox_height = float(row[5])

            score = float(row[6])
            category_id = int(row[7])

            truncation = int(row[8])
            occlusion = int(row[9])

            sequence_annotations.append(
                (
                    sequence_name,
                    frame_id,
                    target_id,
                    category_id,
                    bbox_x,
                    bbox_y,
                    bbox_width,
                    bbox_height,
                    score,
                    truncation,
                    occlusion,
                )
            )

    annotation_rows.extend(sequence_annotations)

    fragment_number = 0

    for start_index in range(
        0,
        total_frames,
        FRAGMENT_SIZE,
    ):
        fragment_number += 1

        fragment_files = frame_files[
            start_index:start_index + FRAGMENT_SIZE
        ]

        if not fragment_files:
            continue

        start_frame = start_index + 1
        end_frame = start_index + len(fragment_files)

        local_fragment = (
            f"/data/local/"
            f"{sequence_name}_fragment_{fragment_number}.mp4"
        )

        print(
            f"Creating fragment {fragment_number}: "
            f"frames {start_frame}-{end_frame}"
        )

        writer = imageio.get_writer(
            local_fragment,
            fps=FPS,
            codec="libx264",
        )

        for frame_file in fragment_files:
            frame_path = os.path.join(
                sequence_dir,
                frame_file,
            )

            frame = imageio.imread(frame_path)

            writer.append_data(frame)

        writer.close()

        object_key = (
            f"assets/visdrone/"
            f"{sequence_name}/"
            f"fragment_{fragment_number}.mp4"
        )

        print(
            f"Uploading fragment {fragment_number} "
            f"to RustFS..."
        )

        s3.upload_file(
            local_fragment,
            "lakehouse",
            object_key,
        )

        fragment_uri = (
            f"s3://lakehouse/{object_key}"
        )

        matching_annotations = [
            row
            for row in sequence_annotations
            if start_frame <= row[1] <= end_frame
        ]

        n_objects = len(matching_annotations)

        start_time = (
            (start_frame - 1) / FPS
        )

        end_time = (
            end_frame / FPS
        )

        fragment_rows.append(
            (
                sequence_name,
                fragment_number,
                fragment_uri,
                start_frame,
                end_frame,
                start_time,
                end_time,
                n_objects,
            )
        )


print()
print("Connecting to DuckLake...")

con = duckdb.connect()

con.execute(
    open(
        "sql/00_attach.sql",
        encoding="utf-8",
    ).read()
)


annotation_df = pd.DataFrame(
    annotation_rows,
    columns=[
        "sequence_name",
        "frame_id",
        "target_id",
        "category_id",
        "bbox_x",
        "bbox_y",
        "bbox_width",
        "bbox_height",
        "score",
        "truncation",
        "occlusion",
    ],
)

con.register(
    "annotation_df",
    annotation_df,
)

con.execute(
    """
    CREATE OR REPLACE TABLE raw.visdrone_annotations AS
    SELECT *
    FROM annotation_df
    """
)


fragment_df = pd.DataFrame(
    fragment_rows,
    columns=[
        "sequence_name",
        "fragment_id",
        "fragment_uri",
        "start_frame",
        "end_frame",
        "start_time",
        "end_time",
        "n_objects",
    ],
)

con.register(
    "fragment_df",
    fragment_df,
)

con.execute(
    """
    CREATE OR REPLACE TABLE raw.visdrone_fragments AS
    SELECT *
    FROM fragment_df
    """
)


print()
print("VisDrone ingestion complete!")
print()

print(
    con.sql(
        """
        SELECT COUNT(*) AS total_annotations
        FROM raw.visdrone_annotations
        """
    ).fetchdf()
)

print()

print(
    con.sql(
        """
        SELECT COUNT(*) AS total_fragments
        FROM raw.visdrone_fragments
        """
    ).fetchdf()
)

print()

print(
    con.sql(
        """
        SELECT *
        FROM raw.visdrone_fragments
        ORDER BY n_objects DESC
        """
    ).fetchdf()
)
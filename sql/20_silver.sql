CREATE OR REPLACE TABLE silver.coco_annotations AS
SELECT DISTINCT
    CAST(bbox_id AS BIGINT) AS bbox_id,
    CAST(image_id AS BIGINT) AS image_id,
    CAST(image_uri AS VARCHAR) AS image_uri,
    CAST(category_id AS INTEGER) AS category_id,
    CAST(x1 AS DOUBLE) AS x1,
    CAST(y1 AS DOUBLE) AS y1,
    CAST(x2 AS DOUBLE) AS x2,
    CAST(y2 AS DOUBLE) AS y2,
    CAST(area AS DOUBLE) AS area
FROM raw.coco_annotations
WHERE image_uri IS NOT NULL
  AND bbox_id IS NOT NULL;


CREATE OR REPLACE TABLE silver.coco_images AS
SELECT DISTINCT
    CAST(image_id AS BIGINT) AS image_id,
    CAST(image_uri AS VARCHAR) AS image_uri,
    CAST(width AS INTEGER) AS width,
    CAST(height AS INTEGER) AS height,
    CAST(split AS VARCHAR) AS split
FROM raw.coco_images
WHERE image_uri IS NOT NULL;


CREATE OR REPLACE TABLE silver.visdrone_annotations AS
SELECT DISTINCT
    CAST(sequence_name AS VARCHAR) AS sequence_name,
    CAST(frame_id AS INTEGER) AS frame_id,
    CAST(target_id AS INTEGER) AS target_id,
    CAST(category_id AS INTEGER) AS category_id,
    CAST(bbox_x AS DOUBLE) AS bbox_x,
    CAST(bbox_y AS DOUBLE) AS bbox_y,
    CAST(bbox_width AS DOUBLE) AS bbox_width,
    CAST(bbox_height AS DOUBLE) AS bbox_height,
    CAST(score AS DOUBLE) AS score,
    CAST(truncation AS INTEGER) AS truncation,
    CAST(occlusion AS INTEGER) AS occlusion
FROM raw.visdrone_annotations
WHERE frame_id IS NOT NULL
  AND sequence_name IS NOT NULL;


CREATE OR REPLACE TABLE silver.visdrone_fragments AS
SELECT DISTINCT
    CAST(sequence_name AS VARCHAR) AS sequence_name,
    CAST(fragment_id AS INTEGER) AS fragment_id,
    CAST(fragment_uri AS VARCHAR) AS fragment_uri,
    CAST(start_frame AS INTEGER) AS start_frame,
    CAST(end_frame AS INTEGER) AS end_frame,
    CAST(start_time AS DOUBLE) AS start_time,
    CAST(end_time AS DOUBLE) AS end_time,
    CAST(n_objects AS INTEGER) AS n_objects
FROM raw.visdrone_fragments
WHERE fragment_uri IS NOT NULL;


ALTER TABLE silver.visdrone_fragments
ADD COLUMN object_density DOUBLE;


UPDATE silver.visdrone_fragments
SET object_density =
    n_objects::DOUBLE
    / NULLIF(end_frame - start_frame + 1, 0);
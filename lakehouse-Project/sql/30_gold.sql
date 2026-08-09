CREATE OR REPLACE TABLE gold.coco_training AS
SELECT
    i.image_id,
    i.image_uri,
    i.width,
    i.height,
    i.split,
    a.category_id,
    a.x1,
    a.y1,
    a.x2,
    a.y2,
    a.area
FROM silver.coco_images AS i
JOIN silver.coco_annotations AS a
    ON i.image_id = a.image_id;


CREATE OR REPLACE TABLE gold.visdrone_training AS
SELECT
    f.sequence_name,
    f.fragment_id,
    f.fragment_uri,
    f.start_frame,
    f.end_frame,
    f.start_time,
    f.end_time,
    f.n_objects,
    f.object_density
FROM silver.visdrone_fragments AS f
WHERE f.n_objects > 0;
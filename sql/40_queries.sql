-- COCO metadata query:
-- Find images with the most annotations in our subset.

SELECT
    image_uri,
    COUNT(*) AS n_objects
FROM silver.coco_annotations
GROUP BY image_uri
HAVING COUNT(*) >= 5
ORDER BY n_objects DESC;


-- VisDrone fragment query:
-- Select the busiest fragments.

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
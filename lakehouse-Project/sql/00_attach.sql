INSTALL ducklake;
LOAD ducklake;

INSTALL httpfs;
LOAD httpfs;

CREATE OR REPLACE SECRET rustfs (
    TYPE s3,
    KEY_ID 'rustfsadmin',
    SECRET 'rustfsadmin',
    ENDPOINT 'rustfs:9000',
    URL_STYLE 'path',
    USE_SSL false
);

ATTACH 'ducklake:metadata.ducklake' AS lake
(DATA_PATH 's3://lakehouse/');

USE lake;

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
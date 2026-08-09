import duckdb


con = duckdb.connect()
con.execute(open("sql/00_attach.sql", encoding="utf-8").read())


print("\nCURRENT SNAPSHOTS")
print(
    con.sql(
        """
        SELECT *
        FROM ducklake_snapshots('lake')
        ORDER BY snapshot_id
        """
    ).fetchdf()
)


print("\nCURRENT ROW COUNT")
print(
    con.sql(
        """
        SELECT COUNT(*) AS rows_before
        FROM silver.coco_annotations
        """
    ).fetchdf()
)


before_snapshot = con.sql(
    """
    SELECT MAX(snapshot_id)
    FROM ducklake_snapshots('lake')
    """
).fetchone()[0]

print(f"\nSnapshot before bad change: {before_snapshot}")


print("\nMAKING DELIBERATELY BAD CHANGE...")

con.execute(
    """
    DELETE FROM silver.coco_annotations
    WHERE image_id = 139
    """
)


after_snapshot = con.sql(
    """
    SELECT MAX(snapshot_id)
    FROM ducklake_snapshots('lake')
    """
).fetchone()[0]

print(f"Snapshot after bad change: {after_snapshot}")


print("\nROW COUNT AFTER BAD CHANGE")
print(
    con.sql(
        """
        SELECT COUNT(*) AS rows_after_bad_change
        FROM silver.coco_annotations
        """
    ).fetchdf()
)


print("\nTIME TRAVEL TO OLD SNAPSHOT")
print(
    con.sql(
        f"""
        SELECT COUNT(*) AS old_version_rows
        FROM silver.coco_annotations
        AT (VERSION => {before_snapshot})
        """
    ).fetchdf()
)


print("\nCOMPARE CURRENT VS OLD VERSION")

current_count = con.sql(
    """
    SELECT COUNT(*)
    FROM silver.coco_annotations
    """
).fetchone()[0]

old_count = con.sql(
    f"""
    SELECT COUNT(*)
    FROM silver.coco_annotations
    AT (VERSION => {before_snapshot})
    """
).fetchone()[0]

print(f"Old version rows: {old_count}")
print(f"Current rows: {current_count}")
print(f"Difference: {old_count - current_count}")


print("\nSNAPSHOTS AFTER CHANGE")
print(
    con.sql(
        """
        SELECT *
        FROM ducklake_snapshots('lake')
        ORDER BY snapshot_id
        """
    ).fetchdf()
)


print("\nAttempting rollback...")

try:
    con.execute(
        f"""
        CALL ducklake_rollback('lake', {before_snapshot})
        """
    )

    print("Rollback completed.")

except Exception as error:
    print("Rollback function failed:")
    print(error)
    print()
    print(
        "DuckLake rollback syntax may differ in this installed version."
    )
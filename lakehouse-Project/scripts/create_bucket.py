import boto3


s3 = boto3.client(
    "s3",
    endpoint_url="http://rustfs:9000",
    aws_access_key_id="rustfsadmin",
    aws_secret_access_key="rustfsadmin",
)


bucket_name = "lakehouse"


existing_buckets = [
    bucket["Name"]
    for bucket in s3.list_buckets()["Buckets"]
]


if bucket_name not in existing_buckets:
    s3.create_bucket(Bucket=bucket_name)
    print("Created lakehouse bucket.")
else:
    print("Lakehouse bucket already exists.")


print("Clearing existing objects...")


response = s3.list_objects_v2(
    Bucket=bucket_name
)


while True:
    objects = response.get("Contents", [])

    if objects:
        s3.delete_objects(
            Bucket=bucket_name,
            Delete={
                "Objects": [
                    {"Key": obj["Key"]}
                    for obj in objects
                ]
            },
        )

    if not response.get("IsTruncated"):
        break

    response = s3.list_objects_v2(
        Bucket=bucket_name,
        ContinuationToken=response["NextContinuationToken"],
    )


print("Bucket ready.")
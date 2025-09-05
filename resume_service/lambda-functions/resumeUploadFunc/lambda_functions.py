import json
import base64
import boto3
import re
from boto3.dynamodb.conditions import Attr

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Constants
S3_BUCKET = "resumeuploadpd"
DYNAMO_TABLE = "resumeuploadtable"

def lambda_handler(event, context):
    try:
        # Parse body
        if "body" in event:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        else:
            body = event

        user_name = body["userName"]
        original_file_name = body["fileName"]
        file_content_base64 = body["fileContent"]

        # Decode base64 file content
        file_bytes = base64.b64decode(file_content_base64)

        # Split original filename into base and extension
        match = re.match(r"(.+)\.([a-zA-Z0-9]+)$", original_file_name)
        if match:
            base_name = match.group(1)
            extension = match.group(2)
        else:
            base_name = original_file_name
            extension = "pdf"  # fallback if no extension

        # DynamoDB table
        table = dynamodb.Table(DYNAMO_TABLE)

        # ✅ Fix: This block was misindented
        response = table.update_item(
            Key={
                'userName': user_name,
                'version': 'V_COUNTER'  # special item to track version number
            },
            UpdateExpression="SET versionNumber = if_not_exists(versionNumber, :start) + :inc",
            ExpressionAttributeValues={
                ':inc': 1,
                ':start': 0
            },
            ReturnValues="UPDATED_NEW"
        )

        version_number = int(response['Attributes']['versionNumber'])
        version_label = f"V{version_number}"

        # Create versioned filename
        versioned_file_name = f"{base_name}{version_label}.{extension}"
        s3_key = f"resumes/{user_name}/{versioned_file_name}"

        # --- Upload to S3 ---
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_bytes,
            ACL='public-read'  # optional
        )

        # --- Get the latest version ID from S3 ---
        versions = s3.list_object_versions(Bucket=S3_BUCKET, Prefix=s3_key)
        latest_version_id = versions['Versions'][0]['VersionId'] if 'Versions' in versions else None

        # Generate presigned URL for the latest version
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': s3_key, 'VersionId': latest_version_id} if latest_version_id else {'Bucket': S3_BUCKET, 'Key': s3_key},
            ExpiresIn=3600
        )

        # Save metadata to DynamoDB
        table.put_item(Item={
            "userName": user_name,
            "version": version_label,        # Sort key
            "versionNumber": version_number,
            "fileName": versioned_file_name,
            "s3Key": s3_key,
            "s3VersionId": latest_version_id,
            "resumeUrl": presigned_url
        })

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"{versioned_file_name} uploaded successfully.",
                "version": version_label,
                "fileName": versioned_file_name,
                "s3Url": presigned_url
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

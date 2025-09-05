import json
import boto3

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# DynamoDB and S3 constants
DYNAMO_TABLE = 'resumeuploadtable'
S3_BUCKET = 'resumeuploadpd'

def lambda_handler(event, context):
    try:
        # Parse input
        if "body" in event:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        else:
            body = event

        user_name = body.get("userName")
        version = body.get("version")

        if not user_name or not version:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'userName' or 'version'"})
            }

        # Fetch item from DynamoDB
        table = dynamodb.Table(DYNAMO_TABLE)
        response = table.get_item(
            Key={
                "userName": user_name,
                "version": version
            }
        )

        if 'Item' not in response:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Resume not found for this user and version"})
            }

        item = response['Item']
        s3_key = item['s3Key']
        s3_version_id = item.get('s3VersionId')
        file_name = item['fileName']

        # Generate pre-signed URL that forces download
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': s3_key,
                **({'VersionId': s3_version_id} if s3_version_id else {}),
                'ResponseContentDisposition': f'attachment; filename="{file_name}"'
            },
            ExpiresIn=3600  # 1 hour
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Resume download link generated.",
                "fileName": file_name,
                "version": version,
                "downloadUrl": presigned_url
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

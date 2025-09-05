import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

DYNAMO_TABLE = "resumeuploadtable"
S3_BUCKET = "resumeuploadpd"

def lambda_handler(event, context):
    try:
        print("Received event:", event)

        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event

        print("Parsed body:", body)

        user_name = body.get("userName")
        print(f"Extracted userName: '{user_name}' (type: {type(user_name)})")

        if not user_name or not isinstance(user_name, str):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid or missing 'userName' in request."})
            }

        table = dynamodb.Table(DYNAMO_TABLE)

        # Query all versions for this user
        response = table.query(
            KeyConditionExpression=Key('userName').eq(user_name)
        )

        items = response.get('Items', [])
        print(f"Found {len(items)} resume(s) for user '{user_name}'.")

        if not items:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "No resumes found for this user."})
            }

        resume_list = []
        for item in items:
            s3_key = item.get("s3Key")
            if s3_key is None:
                print("Warning: s3Key missing in item", item)
                continue

            file_name = item.get("fileName", "unknown")
            version = item.get("version", "unknown")

            presigned_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET, 'Key': s3_key},
                ExpiresIn=3600
            )

            resume_list.append({
                "fileName": file_name,
                "version": version,
                "downloadUrl": presigned_url
            })

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Found {len(resume_list)} resume(s) for user {user_name}.",
                "resumes": resume_list
            })
        }

    except Exception as e:
        print("Exception:", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

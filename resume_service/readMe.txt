This resume services provides APIs to upload, list, and download resumes using AWS services.
It is designed with python, AWS Lambda, API Gateway, S3, and DynamoDB 

🚀 Features

Upload new resumes or create a new version of a resume if existing ones (/resumeUpload)

Fetch list of all resumes for a user (/resumeView)

Get a specific resume download link by version (/resumeList)



🏗️ Architecture
Client → API Gateway → AWS Lambda → DynamoDB (metadata)
                                ↘→ S3 (resume storage)


API Gateway: Handles requests and routes them to Lambda

Lambda: Processes logic (upload, list, download)

S3: Stores resume files

DynamoDB: Tracks file metadata and versions


🛠️ Tech Stack

AWS API Gateway

AWS Lambda

AWS S3 (file storage)

AWS DynamoDB (metadata)


📑 API Endpoints
1. Upload Resume

POST /resumeUpload

Request

{
  "userName": "abc@gmail.com",
  "fileName": "resume.pdf",
  "fileContent": "BASE64_ENCODED_STRING"
}


Response

{
  "statusCode": 200,
  "message": "Resume uploaded successfully."
}

2. List Resumes

POST /resumeView

Request

{
  "userName": "abc@gmail.com"
}


Response

{
  "statusCode": 200,
  "message": "Found 2 resume(s) for user abc@gmail.com.",
  "resumes": [
    {
      "fileName": "resume.pdf",
      "version": "V1",
      "downloadUrl": "https://s3.amazonaws.com/resume.pdf"
    },
    {
      "fileName": "resumeV2.pdf",
      "version": "V2",
      "downloadUrl": "https://s3.amazonaws.com/resumeV2.pdf"
    }
  ]
}

3. Get Resume Download Link

POST /resumeList

Request

{
  "userName": "abc@gmail.com",
  "version": "V2"
}


Response

{
  "statusCode": 200,
  "message": "Resume download link generated.",
  "fileName": "resumeV2.pdf",
  "version": "V2",
  "downloadUrl": "https://s3.amazonaws.com/resumeV2.pdf"
}




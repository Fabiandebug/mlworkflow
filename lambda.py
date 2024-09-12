#Function 1 serializeImageData 

import json
import boto3
import base64

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """A function to serialize target data from S3"""
    
    key = event["s3_key"]  # Extract the S3 key from the event
    bucket = event["s3_bucket"]  # Extract the S3 bucket from the event
    
    # Download the data from S3 to /tmp/image.png
    s3.download_file(bucket, key, "/tmp/image.png")
    
    # Read the data from the file and encode it as base64
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')  # Decode to convert bytes to string

    # Pass the data back to the Step Function
    print("Event:", event.keys())
    return {
        'statusCode': 200,
        'body': json.dumps({
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []
        })
    }


#Function 2 classifyImage

import json
import boto3
import base64

# Set the SageMaker endpoint name
ENDPOINT_NAME = 'image-classification-2024-09-11-20-48-58-154'

runtime = boto3.client('runtime.sagemaker')

def lambda_handler(event, context):
    # Decode the base64 image data
    image = base64.b64decode(event["image_data"])
    
    # Invoke the SageMaker endpoint to get predictions
    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType='application/x-image',
        Body=image
    )
    
    # Read and decode the response
    inferences = json.loads(response['Body'].read().decode('utf-8'))
    
    # Return the data back to the Step Function    
    return {
        'statusCode': 200,
        'body': json.dumps({
            "image_data": event["image_data"],
            "s3_bucket": event["s3_bucket"],
            "s3_key": event["s3_key"],
            "inferences": inferences
        })
    }


#Fuction 3 filterInferences 

import json

THRESHOLD = 0.9

def lambda_handler(event, context):
    # Get the inferences from the event
    inferences = json.loads(event["inferences"])
    
    # Check if any inference confidence values are above the threshold
    meets_threshold = any(float(score) > THRESHOLD for score in inferences.values())
    
    # If the threshold is met, pass the data back, else raise an error
    if meets_threshold:
        return {
            'statusCode': 200,
            'body': json.dumps(event)
        }
    else:
        raise Exception("THRESHOLD_CONFIDENCE_NOT_MET")






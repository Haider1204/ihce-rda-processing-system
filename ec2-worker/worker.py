import boto3
import json
import time
import sys
from datetime import datetime
from decimal import Decimal

# AWS Clients
sqs = boto3.client('sqs', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Configuration
QUEUE_URL = os.environ.get('QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/YOUR-ACCOUNT/rda-processing-queue')
TABLE_NAME = 'rda-documents'
POLL_INTERVAL = 5
MAX_MESSAGES = 10

# DynamoDB table
table = dynamodb.Table(TABLE_NAME)

def convert_floats_to_decimal(obj):
    """Convert float to Decimal for DynamoDB compatibility"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    return obj

def process_message(message):
    """Process a single RDA message"""
    try:
        body = json.loads(message['Body'])
        
        print(f"Processing RDA for patient: {body.get('patient', {}).get('id', 'unknown')}")
        
        patient = body.get('patient', {})
        encounter = body.get('encounter', {})
        facility = encounter.get('facility', {})
        
        item = {
            'patient_id': patient.get('id', 'unknown'),
            'encounter_id': encounter.get('id', f"ENC-{int(time.time())}"),
            'facility_id': facility.get('id', 'unknown'),
            'facility_name': facility.get('name', 'unknown'),
            'encounter_date': encounter.get('date', datetime.utcnow().isoformat()),
            'patient_name': patient.get('name', 'unknown'),
            'patient_birth_date': patient.get('birthDate', ''),
            'patient_gender': patient.get('gender', ''),
            'diagnosis': body.get('diagnosis', []),
            'medications': body.get('medications', []),
            'resource_type': body.get('resourceType', 'ClinicalDocument'),
            'validation_timestamp': body.get('validation_timestamp', ''),
            'validation_status': body.get('validation_status', 'PROCESSED'),
            'processing_timestamp': datetime.utcnow().isoformat(),
            'raw_data': json.dumps(body)
        }
        
        item = convert_floats_to_decimal(item)
        
        response = table.put_item(Item=item)
        
        print(f"✓ Stored in DynamoDB: {item['patient_id']} / {item['encounter_id']}")
        
        sqs.delete_message(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=message['ReceiptHandle']
        )
        
        print(f"✓ Deleted message from queue")
        return True
        
    except Exception as e:
        print(f"✗ Error processing message: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main worker loop"""
    print("=" * 60)
    print("RDA Worker Started")
    print(f"Queue URL: {QUEUE_URL}")
    print(f"DynamoDB Table: {TABLE_NAME}")
    print(f"Poll Interval: {POLL_INTERVAL}s")
    print("=" * 60)
    print()
    
    messages_processed = 0
    errors = 0
    
    try:
        while True:
            print(f"[{datetime.utcnow().isoformat()}] Polling for messages...")
            
            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=MAX_MESSAGES,
                WaitTimeSeconds=20,
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            
            if not messages:
                print("  No messages available")
            else:
                print(f"  Received {len(messages)} message(s)")
                
                for message in messages:
                    if process_message(message):
                        messages_processed += 1
                    else:
                        errors += 1
                
                print(f"  Stats: Processed={messages_processed}, Errors={errors}")
            
            print()
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("Worker stopped by user")
        print(f"Total processed: {messages_processed}")
        print(f"Total errors: {errors}")
        print("=" * 60)
        sys.exit(0)
    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

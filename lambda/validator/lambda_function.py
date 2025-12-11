import json
import boto3
import os
from datetime import datetime

# Cliente SQS
sqs = boto3.client('sqs')
QUEUE_URL = os.environ.get('SQS_QUEUE_URL', '')

def lambda_handler(event, context):
    """
    Valida RDA y envía a SQS si es válido
    """
    print(f"Event received: {json.dumps(event)}")  # Debug
    
    try:
        # Parsear body del request
        body_str = event.get('body', '{}')
        print(f"Body string: {body_str}")  # Debug
        
        # Parsear JSON
        body = json.loads(body_str)
        print(f"Body parsed: {json.dumps(body)}")  # Debug
        
        # Validar estructura básica de RDA
        validation_result = validate_rda(body)
        print(f"Validation result: {validation_result}")  # Debug
        
        if not validation_result['valid']:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Invalid RDA',
                    'details': validation_result['errors']
                })
            }
        
        # Agregar metadata
        body['validation_timestamp'] = datetime.utcnow().isoformat()
        body['validation_status'] = 'VALIDATED'
        
        # Enviar a SQS
        if QUEUE_URL:
            response = sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps(body),
                MessageAttributes={
                    'PatientId': {
                        'StringValue': str(body.get('patient', {}).get('id', 'unknown')),
                        'DataType': 'String'
                    }
                }
            )
            
            return {
                'statusCode': 202,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'RDA accepted for processing',
                    'messageId': response['MessageId'],
                    'queueUrl': QUEUE_URL
                })
            }
        else:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'SQS not configured', 'queue_url': QUEUE_URL})
            }
            
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Invalid JSON', 'details': str(e)})
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }


def validate_rda(rda):
    """
    Validación simplificada de estructura FHIR del RDA
    """
    errors = []
    
    # Verificar que rda sea un dict
    if not isinstance(rda, dict):
        errors.append(f"RDA must be an object, got {type(rda)}")
        return {'valid': False, 'errors': errors}
    
    # Campos obligatorios
    required_fields = ['resourceType', 'patient', 'encounter', 'diagnosis']
    
    for field in required_fields:
        if field not in rda:
            errors.append(f"Missing required field: {field}")
    
    # Validar resourceType
    if rda.get('resourceType') != 'ClinicalDocument':
        errors.append("resourceType must be 'ClinicalDocument'")
    
    # Validar patient
    if 'patient' in rda:
        patient = rda['patient']
        if not isinstance(patient, dict):
            errors.append("Patient must be an object")
        elif 'id' not in patient or 'name' not in patient:
            errors.append("Patient must have 'id' and 'name'")
    
    # Validar encounter
    if 'encounter' in rda:
        encounter = rda['encounter']
        if not isinstance(encounter, dict):
            errors.append("Encounter must be an object")
        elif 'date' not in encounter or 'facility' not in encounter:
            errors.append("Encounter must have 'date' and 'facility'")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
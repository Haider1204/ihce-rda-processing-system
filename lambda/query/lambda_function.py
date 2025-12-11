import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('rda-documents')

class DecimalEncoder(json.JSONEncoder):
    """Helper para serializar Decimal a JSON"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    """
    API de consulta de RDAs
    
    Endpoints:
    - GET /rda/{patient_id} - Obtener todos los RDAs de un paciente
    - GET /rda/{patient_id}/{encounter_id} - Obtener un RDA específico
    - GET /rda?facility_id=XXX - Buscar por facility
    """
    
    print(f"Event: {json.dumps(event)}")
    
    try:
        http_method = event.get('httpMethod', 'GET')
        path_parameters = event.get('pathParameters', {})
        query_parameters = event.get('queryStringParameters', {}) or {}
        
        # GET /rda/{patient_id}/{encounter_id} - RDA específico
        if path_parameters and 'patient_id' in path_parameters and 'encounter_id' in path_parameters:
            patient_id = path_parameters['patient_id']
            encounter_id = path_parameters['encounter_id']
            
            response = table.get_item(
                Key={
                    'patient_id': patient_id,
                    'encounter_id': encounter_id
                }
            )
            
            if 'Item' in response:
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps(response['Item'], cls=DecimalEncoder)
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'RDA not found'})
                }
        
        # GET /rda/{patient_id} - Todos los RDAs de un paciente
        elif path_parameters and 'patient_id' in path_parameters:
            patient_id = path_parameters['patient_id']
            
            response = table.query(
                KeyConditionExpression=Key('patient_id').eq(patient_id)
            )
            
            items = response.get('Items', [])
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'count': len(items),
                    'items': items
                }, cls=DecimalEncoder)
            }
        
        # GET /rda?facility_id=XXX - Buscar por facility
        elif 'facility_id' in query_parameters:
            facility_id = query_parameters['facility_id']
            
            response = table.query(
                IndexName='facility-date-index',
                KeyConditionExpression=Key('facility_id').eq(facility_id)
            )
            
            items = response.get('Items', [])
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'count': len(items),
                    'facility_id': facility_id,
                    'items': items
                }, cls=DecimalEncoder)
            }
        
        # GET /rda - Listar todos (limitado a 100)
        else:
            response = table.scan(Limit=100)
            
            items = response.get('Items', [])
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'count': len(items),
                    'items': items,
                    'note': 'Limited to 100 items'
                }, cls=DecimalEncoder)
            }
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }

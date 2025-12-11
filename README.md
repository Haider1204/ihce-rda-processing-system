# Sistema de Procesamiento de Resúmenes Digitales de Atención (RDA)

## 📋 Descripción

Prototipo de sistema de interoperabilidad para Historia Clínica Electrónica basado en la Resolución 1888 de 2025 del Ministerio de Salud de Colombia. Implementa procesamiento asíncrono escalable de Resúmenes Digitales de Atención (RDA) usando arquitectura serverless y orientada a eventos.

## 🏗️ Arquitectura
```
Cliente → API Gateway → Lambda Validator → SQS → EC2 Worker → DynamoDB
                    ↓                                            ↑
                Lambda Query ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ┘
```

### Componentes

- **API Gateway**: REST API para ingesta y consulta de RDAs
- **Lambda Validator**: Validación de estructura FHIR y envío a cola
- **SQS**: Cola de mensajes para desacoplamiento producer-consumer
- **EC2 Worker**: Procesador asíncrono con systemd service
- **DynamoDB**: Almacenamiento NoSQL de RDAs procesados
- **Lambda Query**: API de consulta con múltiples patrones de búsqueda
- **CloudWatch**: Logs, métricas, dashboards y alarmas

## 🚀 Endpoints

### POST /rda
Enviar nuevo RDA para validación y procesamiento
```bash
curl -X POST https://API-ID.execute-api.us-east-1.amazonaws.com/prod/rda \
  -H "Content-Type: application/json" \
  -d @tests/test-rda-valid.json
```

### GET /rda
Listar todos los RDAs (limitado a 100)
```bash
curl https://API-ID.execute-api.us-east-1.amazonaws.com/prod/rda
```

### GET /rda/{patient_id}
Obtener todos los RDAs de un paciente
```bash
curl https://API-ID.execute-api.us-east-1.amazonaws.com/prod/rda/CC-12345678
```

### GET /rda/{patient_id}/{encounter_id}
Obtener un RDA específico
```bash
curl https://API-ID.execute-api.us-east-1.amazonaws.com/prod/rda/CC-12345678/ENC-001
```

### GET /rda?facility_id={id}
Buscar RDAs por facility
```bash
curl https://API-ID.execute-api.us-east-1.amazonaws.com/prod/rda?facility_id=HSP-001
```

## 📦 Instalación

### Prerequisitos
- AWS Academy Learner Lab account
- AWS CLI configurado
- Python 3.11+
- Node.js (para Artillery)

### Lambda Functions
```bash
# Lambda Validator
cd lambda/validator
pip install -r requirements.txt -t .
zip -r function.zip .
aws lambda update-function-code --function-name rda-validator --zip-file fileb://function.zip

# Lambda Query
cd lambda/query
pip install -r requirements.txt -t .
zip -r function.zip .
aws lambda update-function-code --function-name rda-query --zip-file fileb://function.zip
```

### EC2 Worker
```bash
# SSH a tu instancia EC2
ssh -i key.pem ec2-user@EC2-IP

# Clonar repo
git clone https://github.com/YOUR-USER/ihce-rda-processing-system.git
cd ihce-rda-processing-system/ec2-worker

# Instalar
chmod +x install.sh
./install.sh

# Verificar
sudo systemctl status rda-worker
```

## 🧪 Testing

### Unit Tests
```bash
cd tests
python -m pytest
```

### Load Testing con Artillery
```bash
cd tests
artillery run load-test.yml
```

### Resultados esperados
- Throughput: 50+ req/s
- P95 Latency: < 500ms
- Success rate: > 99%

## 📊 Monitoreo

### CloudWatch Dashboard
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=IHCE-RDA-Dashboard

### Métricas clave
- Lambda invocations
- SQS messages (sent/received/deleted)
- DynamoDB read/write capacity
- API Gateway latency

## 🎯 Atributos de Calidad

| Atributo | Implementación | Métrica Objetivo |
|----------|----------------|------------------|
| Performance | Serverless, índices DynamoDB | P95 < 500ms |
| Scalability | Auto-scaling Lambda, on-demand DynamoDB | 0-1000 req/s |
| Reliability | SQS retry, DLQ, systemd restart | 99.9% uptime |
| Availability | Multi-AZ AWS, serverless | 99.95% |
| Security | HTTPS, IAM roles, CORS | - |
| Interoperability | REST API, JSON, FHIR | - |

## 💰 Costos Estimados

**Escenario: 100,000 RDAs/mes**

- Lambda: $0.40
- API Gateway: $0.35
- SQS: $0.08
- DynamoDB: $12.50
- EC2 t2.micro: $8.50
- **Total: ~$22/mes**



## 🙏 Agradecimientos

- Ministerio de Salud y Protección Social de Colombia
- HL7 International (FHIR Standard)
- AWS Academy Program
```
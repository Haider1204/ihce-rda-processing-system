# Architecture Overview - Sistema RDA

## 1. Introducción

### 1.1 Propósito
El Sistema de Procesamiento de Resúmenes Digitales de Atención (RDA) es un prototipo de interoperabilidad para Historia Clínica Electrónica que permite el intercambio estandarizado de información clínica entre instituciones de salud en Colombia.

### 1.2 Alcance
Este documento describe la arquitectura del sistema RDA, incluyendo:
- Componentes arquitectónicos principales
- Patrones de diseño aplicados
- Decisiones arquitectónicas clave
- Atributos de calidad implementados

### 1.3 Contexto Regulatorio
El sistema implementa los requisitos de la **Resolución 1888 de 2025** del Ministerio de Salud y Protección Social de Colombia, utilizando el estándar internacional **FHIR R4** para la estructuración de datos clínicos.

---

## 2. Stakeholders

| Stakeholder | Rol | Preocupaciones Principales |
|-------------|-----|---------------------------|
| Instituciones de Salud (IPS) | Proveedores de servicios | Facilidad de integración, bajo costo, interoperabilidad |
| Ministerio de Salud | Ente regulador | Cumplimiento normativo, trazabilidad, auditoría |
| Pacientes | Usuarios finales | Privacidad de datos, disponibilidad, seguridad |
| Equipo de Desarrollo | Implementadores | APIs claras, documentación, mantenibilidad |
| Equipo de Operaciones | Administradores | Monitoreo, alertas, costos, escalabilidad |
| Arquitectos de TI | Diseñadores de sistema | Patrones estándar, extensibilidad, reusabilidad |

---

## 3. Requisitos Arquitectónicos

### 3.1 Requisitos Funcionales Clave

**RF-001**: Validación de RDAs  
El sistema debe validar la estructura de los Resúmenes Digitales de Atención contra el esquema FHIR R4.

**RF-002**: Procesamiento Asíncrono  
Los RDAs deben procesarse de forma asíncrona para permitir alta concurrencia.

**RF-003**: Almacenamiento Persistente  
Los RDAs validados deben almacenarse de forma persistente con alta disponibilidad.

**RF-004**: Consulta Multi-criterio  
El sistema debe permitir consultas por:
- ID de paciente
- ID de encuentro médico
- ID de institución
- Listado general

### 3.2 Atributos de Calidad (Quality Attributes)

#### Performance
- **Latency**: P95 < 500ms para operaciones de escritura y lectura
- **Throughput**: Capacidad de manejar 50+ requests/segundo

#### Scalability
- **Elasticidad**: Auto-scaling de 0 a 1000 req/s sin intervención manual
- **Costo-eficiencia**: Pago por uso (pay-per-request)

#### Availability
- **Uptime**: 99.95% de disponibilidad (objetivo)
- **Redundancia**: Despliegue multi-zona de disponibilidad

#### Security
- **Confidencialidad**: HTTPS para todas las comunicaciones
- **Autenticación**: IAM roles con principio de mínimo privilegio
- **Cumplimiento**: HIPAA-ready, Ley 1581 de Colombia

#### Reliability
- **Durabilidad**: Los datos no se pierden (DynamoDB replication)
- **Fault Tolerance**: Reintentos automáticos, Dead Letter Queues
- **Recovery**: Capacidad de recuperación ante fallos

#### Maintainability
- **Observabilidad**: Logs centralizados (CloudWatch)
- **Monitoreo**: Métricas y alarmas proactivas
- **Deployability**: Proceso de despliegue automatizable

---

## 4. Restricciones

### 4.1 Restricciones Técnicas
- **Plataforma**: AWS (requisito académico - AWS Academy)
- **Presupuesto**: Limitado a recursos gratuitos/bajo costo
- **Lenguaje**: Python 3.11+ para Lambdas y Worker
- **Estándar**: FHIR R4 para estructura de documentos clínicos

### 4.2 Restricciones de Negocio
- **Tiempo**: Desarrollo en contexto académico (semestre)
- **Equipo**: Equipo reducido (1-3 desarrolladores)
- **Alcance**: Prototipo funcional, no sistema productivo completo

### 4.3 Restricciones Regulatorias
- **Privacidad**: Cumplimiento Ley 1581 de 2012 (Habeas Data - Colombia)
- **Salud**: Resolución 1888/2025 del Ministerio de Salud
- **Interoperabilidad**: Estándar FHIR (HL7 International)

---

## 5. Architectural Style

### 5.1 Estilo Principal: Event-Driven Architecture

**Justificación**:
- Desacoplamiento entre productores (validación) y consumidores (procesamiento)
- Mejor escalabilidad independiente de componentes
- Resiliencia: fallos en procesamiento no afectan ingesta

### 5.2 Patrón: Serverless Architecture

**Justificación**:
- **Costo**: Pay-per-use alineado con presupuesto académico
- **Operaciones**: Sin gestión de infraestructura
- **Escalabilidad**: Auto-scaling nativo de AWS Lambda
- **Desarrollo**: Enfoque en lógica de negocio vs. infraestructura

### 5.3 Patrón: CQRS (Command Query Responsibility Segregation)

**Aplicación parcial**:
- Comandos (POST /rda): Lambda Validator → SQS → EC2 Worker → DynamoDB
- Queries (GET /rda): Lambda Query → DynamoDB
- Separación permite optimizar cada flujo independientemente

---

## 6. Vista de Contexto

### 6.1 System Context Diagram

```
┌─────────────────┐
│  Instituciones  │
│    de Salud     │◄─────────┐
│   (Clientes)    │          │
└────────┬────────┘          │
         │                    │
         │ HTTPS              │ HTTPS
         │ JSON/FHIR          │ JSON
         │                    │
         ▼                    │
┌─────────────────────────────┴──────┐
│                                     │
│     Sistema RDA Processing         │
│                                     │
│  ┌──────────┐  ┌────────────────┐  │
│  │   API    │  │   Procesador   │  │
│  │ Gateway  │  │   Asíncrono    │  │
│  └──────────┘  └────────────────┘  │
│                                     │
└─────────────────────────────────────┘
         │
         │ Almacena
         │
         ▼
┌─────────────────┐
│   DynamoDB      │
│  (Base de Datos)│
└─────────────────┘
```

### 6.2 Actores Externos

**Instituciones Prestadoras de Salud (IPS)**
- Envían RDAs cuando hay encuentros médicos
- Consultan RDAs históricos de pacientes
- Ejemplo: Hospitales, clínicas, consultorios

**Sistemas de Historia Clínica Electrónica (HCE)**
- Integran con API REST del sistema RDA
- Generan RDAs en formato FHIR
- Consumen información de otros prestadores

---

## 7. Principios Arquitectónicos

### 7.1 Separation of Concerns
Cada componente tiene una responsabilidad única y bien definida:
- API Gateway: Routing HTTP
- Lambda Validator: Validación de esquema
- SQS: Buffer de mensajes
- EC2 Worker: Procesamiento de negocio
- DynamoDB: Persistencia

### 7.2 Loose Coupling
Los componentes interactúan a través de interfaces estándar (HTTP, SQS messages) sin conocimiento interno de implementación.

### 7.3 Scalability by Design
Cada componente puede escalar independientemente:
- Lambda: Concurrencia automática
- SQS: Buffer ilimitado
- EC2 Worker: Múltiples instancias
- DynamoDB: Particionamiento automático

### 7.4 Security in Depth
Múltiples capas de seguridad:
- Network: HTTPS, VPC
- Authentication: IAM roles
- Authorization: Políticas de mínimo privilegio
- Data: Encriptación en tránsito y reposo

### 7.5 Observability First
Logging, métricas y trazas en todos los componentes:
- CloudWatch Logs para debugging
- CloudWatch Metrics para monitoreo
- Alarmas para notificación proactiva

---

## 8. High-Level Architecture

```
                            ┌─────────────────────────────────────┐
                            │        AWS Cloud (us-east-1)        │
                            │                                     │
┌──────────────┐            │  ┌────────────────────────────────┐│
│              │   HTTPS    │  │                                ││
│  Prestadores │───────────────►│       API Gateway              ││
│  de Servicio │            │  │    (REST API Endpoint)         ││
│              │◄───────────────│                                ││
└──────────────┘  JSON/FHIR │  └───────────┬────────────────────┘│
                            │              │                      │
                            │              │ Invoke               │
                            │              ▼                      │
                            │  ┌────────────────────────────────┐│
                            │  │   Lambda Validator             ││
                            │  │   • Validación FHIR            ││
                            │  │   • Enriquecimiento metadata   ││
                            │  │   • Envío a SQS                ││
                            │  └───────────┬────────────────────┘│
                            │              │                      │
                            │              │ SendMessage          │
                            │              ▼                      │
                            │  ┌────────────────────────────────┐│
                            │  │        SQS Queue               ││
                            │  │   • Desacoplamiento            ││
                            │  │   • Buffer mensajes            ││
                            │  │   • DLQ para errores           ││
                            │  └───────────┬────────────────────┘│
                            │              │                      │
                            │              │ ReceiveMessage       │
                            │              ▼                      │
                            │  ┌────────────────────────────────┐│
                            │  │      EC2 Worker                ││
                            │  │   • Polling SQS                ││
                            │  │   • Procesamiento RDA          ││
                            │  │   • Escritura DynamoDB         ││
                            │  └───────────┬────────────────────┘│
                            │              │                      │
                            │              │ PutItem              │
                            │              ▼                      │
                            │  ┌────────────────────────────────┐│
                            │  │        DynamoDB                ││
                            │  │   • Tabla: rda-documents       ││
                            │  │   • PK: patient_id             ││
                            │  │   • SK: encounter_id           ││
                            │  │   • GSI: facility-date-index   ││
                            │  └────────────▲───────────────────┘│
                            │               │                     │
                            │               │ Query/GetItem       │
                            │               │                     │
                            │  ┌────────────┴───────────────────┐│
                            │  │      Lambda Query              ││
                            │  │   • Consultas optimizadas      ││
                            │  │   • Múltiples patrones acceso  ││
                            │  └────────────▲───────────────────┘│
                            │               │                     │
                            │               │ Invoke              │
                            │               │                     │
                            │  ┌────────────┴───────────────────┐│
                            │  │       API Gateway              ││
                            │  │    (GET /rda endpoints)        ││
                            │  └────────────────────────────────┘│
                            │                                     │
                            │  ┌────────────────────────────────┐│
                            │  │      CloudWatch                ││
                            │  │   • Logs                       ││
                            │  │   • Metrics                    ││
                            │  │   • Alarms                     ││
                            │  │   • Dashboard                  ││
                            │  └────────────────────────────────┘│
                            │                                     │
                            └─────────────────────────────────────┘
```

---

## 9. Technology Stack

### 9.1 AWS Services

| Servicio | Propósito | Justificación |
|----------|-----------|---------------|
| API Gateway | HTTP endpoints | Managed service, auto-scaling, integración Lambda |
| Lambda | Compute serverless | Pay-per-request, auto-scaling, sin gestión servidores |
| SQS | Message queue | Desacoplamiento, buffer, retry automático |
| EC2 | Worker continuo | Procesamiento long-running, control total |
| DynamoDB | Database NoSQL | Alta disponibilidad, auto-scaling, latencia baja |
| CloudWatch | Observabilidad | Logs centralizados, métricas, alarmas |
| IAM | Seguridad | Roles, políticas, principio mínimo privilegio |

### 9.2 Frameworks y Librerías

- **Python 3.11**: Lambda runtime, EC2 worker
- **Boto3**: AWS SDK para Python
- **FHIR Validation**: Validación esquemas clínicos
- **Artillery**: Load testing
- **pytest**: Unit testing

---

## 10. Deployment Architecture

### 10.1 Regiones y Disponibilidad
- **Región**: us-east-1 (N. Virginia)
- **Multi-AZ**: DynamoDB, Lambda (inherente)
- **Single-AZ**: EC2 Worker (prototipo)

### 10.2 Ambientes
- **Production**: Único ambiente (contexto académico)
- **Stage en API Gateway**: `prod`

---

## 11. Referencias

- [Resolución 1888/2025 - Ministerio de Salud Colombia](https://www.minsalud.gov.co)
- [FHIR R4 Specification](https://hl7.org/fhir/R4/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Serverless Architecture Patterns](https://aws.amazon.com/serverless/)
- [Event-Driven Architecture Guide](https://aws.amazon.com/event-driven-architecture/)
| Arquitecto | [Nombre] | | |
| Tech Lead | [Nombre] | | |
| Product Owner | [Nombre] | | |

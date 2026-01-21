# API Reference

## Overview

The Rapid Intervention Fraud Detection API provides endpoints for analyzing interventions to detect potential fraudulent
activity. The API is built with FastAPI and provides automatic OpenAPI documentation.

## Base URL

- Development: `http://localhost:8000`
- Production: `[Your production URL]`

## Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: `{BASE_URL}/docs`
- **ReDoc**: `{BASE_URL}/redoc`
- **OpenAPI Schema**: `{BASE_URL}/openapi.json`

## Authentication

Currently, the API does not require authentication. Add authentication middleware as needed for your deployment.

## Endpoints

### Fraud Detection

#### POST /fraud/detect

Analyzes an intervention for potential fraudulent activity using all configured fraud checkers.

**Request:**

```http
POST /fraud/detect
Content-Type: application/json

{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Emergency Road Repair",
  "description": "Urgent repair needed for pothole on Main Street causing traffic issues",
  "images": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001", 
      "url": "https://example.com/pothole-image.jpg"
    }
  ]
}
```

**Parameters:**

| Field        | Type   | Required | Description                               |
|--------------|--------|----------|-------------------------------------------|
| id           | UUID   | Yes      | Unique identifier for the intervention    |
| title        | string | Yes      | Title of the intervention                 |
| description  | string | Yes      | Detailed description of the intervention  |
| images       | array  | Yes      | Array of associated images (can be empty) |
| images[].id  | UUID   | Yes      | Unique identifier for the image           |
| images[].url | string | Yes      | URL where the image can be accessed       |

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "intervention_id": "550e8400-e29b-41d4-a716-446655440000",
  "fraud_detected": false,
  "fraud_rating": 0.16,
  "details": [
    {
      "checker_type": "TEXT",
      "image": null,
      "fraud_detected": false,
      "fraud_rating": 0.0,
      "reason": "No issues found in text content.",
      "result_weight": 1.0
    },
    {
      "checker_type": "IMAGE", 
      "image": null,
      "fraud_detected": false,
      "fraud_rating": 0.4,
      "reason": "Api returned no issues.",
      "result_weight": 4.0
    }
  ]
}
```

**Response Fields:**

| Field                    | Type         | Description                                   |
|--------------------------|--------------|-----------------------------------------------|
| intervention_id          | UUID         | ID of the analyzed intervention               |
| fraud_detected           | boolean      | Overall fraud detection result                |
| fraud_rating             | number       | Weighted average fraud score (0.0-1.0)        |
| details                  | array        | Results from individual checkers              |
| details[].checker_type   | string       | Type of checker that ran                      |
| details[].image          | object\|null | Associated image if checker is image-specific |
| details[].fraud_detected | boolean      | Fraud detection result for this checker       |
| details[].fraud_rating   | number       | Fraud score from this checker (0.0-1.0)       |
| details[].reason         | string       | Human-readable explanation of the result      |
| details[].result_weight  | number       | Weight of this checker in final calculation   |

**Status Codes:**

- `200 OK`: Fraud detection completed successfully
- `400 Bad Request`: Invalid input data
- `422 Unprocessable Entity`: Validation error in request body
- `500 Internal Server Error`: Server error during processing

**Example Error Response:**

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "id"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

## Data Models

### Intervention

Main input model for fraud detection requests.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "string",
  "description": "string",
  "images": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "url": "string"
    }
  ]
}
```

### Image

Represents an image associated with an intervention.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "url": "https://example.com/image.jpg"
}
```

### FraudDetectionResult

Main response model containing overall fraud analysis results.

```json
{
  "intervention_id": "550e8400-e29b-41d4-a716-446655440000",
  "fraud_detected": false,
  "fraud_rating": 0.16,
  "details": [...]
}
```

### FraudCheckerDetail

Individual checker result within the overall fraud detection response.

```json
{
  "checker_type": "TEXT",
  "image": null,
  "fraud_detected": false,
  "fraud_rating": 0.0,
  "reason": "No issues found in text content.",
  "result_weight": 1.0
}
```

### FraudCheckerType

Enum defining the types of fraud checkers available:

- `INTERVENTION`: Checks the entire intervention
- `TEXT`: Analyzes text content (title + description)
- `IMAGE`: Analyzes associated images

## Scoring Algorithm

The overall fraud score is calculated using a weighted average of individual checker results:

```
fraud_rating = Σ(checker_rating × checker_weight) / Σ(checker_weight)
```

The `fraud_detected` boolean is `true` if any individual checker detects fraud.

## Rate Limiting

Currently, no rate limiting is implemented. Consider adding rate limiting middleware for production deployments.

## Error Handling

The API follows standard HTTP status code conventions:

- **2xx**: Success
- **4xx**: Client errors (invalid input, validation failures)
- **5xx**: Server errors (internal processing errors)

All error responses include a `detail` field with specific error information.

## Health Checks

The application includes health check endpoints:

- **Health Check**: Available through the automatic `/docs` endpoint
- **Docker Health Check**: Configured to check `/docs` endpoint every 30 seconds

## Examples

### cURL Examples

**Basic fraud detection:**

```bash
curl -X POST "http://localhost:8000/fraud/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Road Repair", 
    "description": "Fix pothole on Main St",
    "images": []
  }'
```

**With images:**

```bash  
curl -X POST "http://localhost:8000/fraud/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Bridge Maintenance",
    "description": "Monthly inspection and minor repairs", 
    "images": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "url": "https://example.com/before.jpg"
      },
      {
        "id": "550e8400-e29b-41d4-a716-446655440002", 
        "url": "https://example.com/after.jpg"
      }
    ]
  }'
```

### Python Client Example

```python
import asyncio
import aiohttp
import uuid

async def check_fraud(intervention_data):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/fraud/detect",
            json=intervention_data
        ) as response:
            return await response.json()

# Usage
intervention = {
    "id": str(uuid.uuid4()),
    "title": "Emergency Repair",
    "description": "Urgent water leak repair needed",
    "images": []
}

result = asyncio.run(check_fraud(intervention))
print(f"Fraud detected: {result['fraud_detected']}")
print(f"Fraud rating: {result['fraud_rating']}")
```

### JavaScript Client Example

```javascript
async function checkFraud(interventionData) {
    const response = await fetch('http://localhost:8000/fraud/detect', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(interventionData)
    });

    return await response.json();
}

// Usage
const intervention = {
    id: '550e8400-e29b-41d4-a716-446655440000',
    title: 'Street Light Repair',
    description: 'Replace broken street light on Oak Avenue',
    images: []
};

checkFraud(intervention)
    .then(result => {
        console.log('Fraud detected:', result.fraud_detected);
        console.log('Fraud rating:', result.fraud_rating);
    })
    .catch(error => console.error('Error:', error));
```

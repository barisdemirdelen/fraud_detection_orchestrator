# Rapid Intervention Fraud Detection

A modular fraud detection orchestrator built with FastAPI that delegates fraud checking to various components through a
plugin-based architecture.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Creating New Checkers](#creating-new-checkers)
- [Development](#development)
- [Docker Deployment](#docker-deployment)
- [Testing](#testing)

## Overview

This service acts as an orchestrator for fraud detection across different intervention types. It uses a plugin-based
architecture where different fraud checkers can be easily added, removed, or modified without affecting the core system.

### Key Features

- **Modular Architecture**: Easy to add new fraud detection plugins
- **Async Processing**: All checkers run concurrently for optimal performance
- **Weighted Scoring**: Different checkers can have different weights in the final score
- **Flexible Input**: Supports text, image, and intervention-level checking
- **RESTful API**: Simple HTTP endpoint for fraud detection
- **Docker Ready**: Containerized with health checks

## Architecture

### Core Components

```
src/
├── main.py              # FastAPI application entry point and checker registry
├── fraud_router.py      # API router with fraud detection endpoint
├── schema.py            # Pydantic models for request/response
└── checkers/            # Fraud checker plugins
    ├── base.py          # Abstract base class for all checkers
    ├── basic_text_checker.py    # Example text-based checker
    └── basic_api_checker.py     # Example API-based checker
```

### Data Flow

1. **Request**: Client sends intervention data to `/fraud/detect`
2. **Orchestration**: System retrieves checkers from main.py and runs them concurrently
3. **Aggregation**: Results are collected and scored using weighted average
4. **Response**: Combined fraud detection result is returned

### Checker Architecture

All fraud checkers inherit from `BaseChecker` and implement the `check()` method:

```python
@dataclasses.dataclass
class BaseChecker(ABC):
    type: FraudCheckerType
    result_weight: float = 1.0

    @abc.abstractmethod
    async def check(self, intervention: Intervention) -> FraudCheckerDetail: ...
```

## Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd rapid-intervention-fraud-detection
```

2. Install dependencies:

```bash
uv sync
```

3. Run the application:

```bash
uv run python src/main.py
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

## API Documentation

### POST /fraud/detect

Analyzes an intervention for potential fraud.

**Request Body:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Intervention Title",
  "description": "Detailed description of the intervention",
  "images": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "url": "https://example.com/image.jpg"
    }
  ]
}
```

**Response:**

```json
{
  "intervention_id": "550e8400-e29b-41d4-a716-446655440000",
  "fraud_detected": false,
  "fraud_rating": 0.2,
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

## Creating New Checkers

### Step 1: Create the Checker Class

Create a new file in `src/checkers/` that inherits from `BaseChecker`:

```python
# src/checkers/my_custom_checker.py
import asyncio
from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, Intervention


class MyCustomChecker(BaseChecker):
    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        # Your fraud detection logic here
        await asyncio.sleep(0.1)  # Simulate processing time

        # Perform your checks
        fraud_detected = False  # Your detection logic
        fraud_rating = 0.0  # Score between 0.0 and 1.0

        return FraudCheckerDetail(
            checker_type=self.type,
            image=None,  # Set to specific image if checking images
            fraud_detected=fraud_detected,
            fraud_rating=fraud_rating,
            reason="Description of what was checked and found",
            result_weight=self.result_weight,
        )
```

### Step 2: Register the Checker

Add your checker to the `checkers` list in `src/main.py`:

```python
from src.checkers.my_custom_checker import MyCustomChecker

checkers = [
    BasicTextChecker(type=FraudCheckerType.TEXT),
    BasicApiChecker(type=FraudCheckerType.IMAGE, result_weight=4.0),
    MyCustomChecker(type=FraudCheckerType.INTERVENTION, result_weight=2.0),  # Add this line
]
```

### Step 3: Add New Checker Types (if needed)

If your checker requires a new type, add it to `FraudCheckerType` enum in `src/schema.py`:

```python
class FraudCheckerType(Enum):
    INTERVENTION = "INTERVENTION"
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    MY_NEW_TYPE = "MY_NEW_TYPE"  # Add new types here
```

### Checker Examples

#### API-Based Checker

```python
import aiohttp
from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, Intervention


class ExternalAPIChecker(BaseChecker):
    def __init__(self, api_url: str, **kwargs):
        super().__init__(**kwargs)
        self.api_url = api_url

    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        async with aiohttp.ClientSession() as session:
            payload = {
                "text": f"{intervention.title} {intervention.description}",
                "images": [img.url for img in intervention.images]
            }

            async with session.post(self.api_url, json=payload) as response:
                result = await response.json()

                return FraudCheckerDetail(
                    checker_type=self.type,
                    fraud_detected=result.get("fraud_detected", False),
                    fraud_rating=result.get("confidence", 0.0),
                    reason=result.get("reason", "External API analysis"),
                    result_weight=self.result_weight,
                )
```

#### ML Model Checker

```python
import pickle
from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, Intervention


class MLModelChecker(BaseChecker):
    def __init__(self, model_path: str, **kwargs):
        super().__init__(**kwargs)
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        # Extract features from intervention
        features = self._extract_features(intervention)

        # Run prediction
        prediction = self.model.predict_proba([features])[0]
        fraud_probability = prediction[1]  # Assuming binary classification

        return FraudCheckerDetail(
            checker_type=self.type,
            fraud_detected=fraud_probability > 0.5,
            fraud_rating=fraud_probability,
            reason=f"ML model prediction with {fraud_probability:.2%} confidence",
            result_weight=self.result_weight,
        )

    def _extract_features(self, intervention: Intervention) -> list:
        # Feature extraction logic
        return [
            len(intervention.description),
            len(intervention.images),
            # Add more features as needed
        ]
```

## Development

### Code Style

This project uses `ruff` for code formatting and linting:

```bash
# Check code style
uv run ruff check src/

# Auto-fix issues
uv run ruff check src/ --fix

# Format code
uv run ruff format src/
```

### Adding Dependencies

Use `uv` to add new dependencies:

```bash
# Production dependency
uv add requests

# Development dependency  
uv add --dev pytest-mock
```

### Project Structure Best Practices

- Keep checkers simple and focused on one type of fraud detection
- Use async/await for all I/O operations
- Add proper error handling in your checkers
- Include meaningful logging for debugging
- Write unit tests for new checkers

## Docker Deployment

### Building and Running

```bash
# Build the Docker image
docker build -t fraud-detection-api .

# Run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f fraud-detection-api

# Stop the service
docker-compose down
```

### Health Checks

The application includes built-in health checks accessible at `/docs`. The Docker setup automatically monitors the
health endpoint.

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run coverage run -m pytest
uv run coverage report
```

### Writing Tests for Checkers

Create test files in a `tests/` directory:

```python
# tests/test_checkers.py
import pytest
from src.checkers.my_custom_checker import MyCustomChecker
from src.schema import Intervention, Image, FraudCheckerType
import uuid


@pytest.mark.asyncio
async def test_my_custom_checker():
    checker = MyCustomChecker(type=FraudCheckerType.TEXT)

    intervention = Intervention(
        id=uuid.uuid4(),
        title="Test intervention",
        description="Test description",
        images=[]
    )

    result = await checker.check(intervention)

    assert isinstance(result.fraud_detected, bool)
    assert 0.0 <= result.fraud_rating <= 1.0
    assert result.checker_type == FraudCheckerType.TEXT
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `PYTHONPATH` is set correctly
2. **Async Issues**: Always use `await` with async checker methods
3. **Docker Issues**: Check that port 8000 is not in use
4. **Dependency Issues**: Run `uv sync` to ensure all dependencies are installed

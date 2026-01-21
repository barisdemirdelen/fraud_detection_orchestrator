# Architecture Guide

## Overview

The Rapid Intervention Fraud Detection system is designed as a modular, extensible orchestrator that coordinates
multiple fraud detection components. This guide explains the architectural decisions, patterns, and design principles
used in the system.

## Design Principles

### 1. Plugin Architecture

The system uses a plugin-based architecture where fraud checkers are independent, interchangeable components. This
allows for:

- Easy addition/removal of fraud detection methods
- Independent development and testing of checkers
- Flexible configuration and weighting of different detection strategies

### 2. Async-First Design

All fraud checking operations are asynchronous, enabling:

- Concurrent execution of multiple checkers
- Non-blocking I/O operations
- Better resource utilization and performance

### 3. Separation of Concerns

Clear separation between:

- **Orchestration** (fraud_router.py): Coordinates checker execution and result aggregation
- **Data Models** (schema.py): Defines request/response structures
- **Business Logic** (checkers/): Individual fraud detection implementations
- **Infrastructure** (main.py): Application setup and configuration

### 4. Extensibility

The system is designed for easy extension through:

- Abstract base classes defining clear contracts
- Standardized input/output formats
- Configuration-based checker registration

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
├─────────────────────────────────────────────────────────────┤
│                    Fraud Router                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │               Orchestrator                              │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │            Checker Registry                         │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │            Result Aggregator                        │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Fraud Checkers                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   Text       │ │   Image      │ │   Custom     │   ...  │
│  │   Checker    │ │   Checker    │ │   Checker    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                   External Services                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   ML APIs    │ │  Image APIs  │ │   Other      │   ...  │
│  │              │ │              │ │   Services   │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. FastAPI Application (main.py)

The entry point of the application, responsible for:

- Application initialization and configuration
- Checker registry and configuration
- Router registration
- Server startup and lifecycle management

```python
checkers = [
    BasicTextChecker(type=FraudCheckerType.TEXT),
    BasicApiChecker(type=FraudCheckerType.IMAGE, result_weight=4.0),
]


def get_app():
    app = FastAPI(title="Rapid Intervention Fraud Detection")
    app.include_router(fraud_router)
    return app
```

**Design Decision**: Centralizing checker registration in main.py provides better separation of concerns and makes the
system easier to configure. Factory pattern for app creation allows for easy testing and configuration management.

### 2. Fraud Router (fraud_router.py)

The orchestration layer that:

- Defines API endpoints
- Coordinates checker execution
- Aggregates results

The router now receives checkers as a parameter, separating concerns between configuration (main.py) and execution (
fraud_router.py).

**Design Decision**: Moving checker registration to main.py improves separation of concerns and makes the router more
focused on its core responsibility of orchestrating fraud detection.

### 3. Data Models (schema.py)

Pydantic models that define:

- Request/response contracts
- Data validation rules
- Type safety throughout the system

```python
class Intervention(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    images: list[Image]
```

**Design Decision**: Pydantic provides automatic validation, serialization, and OpenAPI documentation generation.

### 4. Base Checker (checkers/base.py)

Abstract base class defining the contract for all fraud checkers:

```python
@dataclasses.dataclass
class BaseChecker(ABC):
    type: FraudCheckerType
    result_weight: float = 1.0

    @abc.abstractmethod
    async def check(self, intervention: Intervention) -> FraudCheckerDetail: ...
```

**Design Decision**:

- Dataclass for simple configuration and immutability
- Abstract method ensures all checkers implement the required interface
- Weight attribute allows for flexible result aggregation

## Data Flow

### 1. Request Processing

```
HTTP Request → FastAPI → Pydantic Validation → Router Handler
```

1. FastAPI receives the HTTP request
2. Pydantic automatically validates the request body against the `Intervention` model
3. The validated data is passed to the router handler

### 2. Checker Execution

```
Main.py (Checker Registry) → Router → Async Orchestrator → Individual Checkers
```

1. Main.py defines and configures all checkers
2. Router receives checkers as parameters from the application context
3. Creates async tasks for each checker
4. Executes all checkers concurrently using `asyncio.gather()`
5. Collects results from all checkers

### 3. Result Aggregation

```
Individual Results → Weighted Average → Final Score → Response
```

1. Individual checker results are collected
2. Weighted average is calculated based on checker weights
3. Overall fraud detection boolean is determined (true if any checker detects fraud)
4. Response is serialized and returned

## Patterns and Practices

### 1. Strategy Pattern

Each fraud checker implements a different strategy for fraud detection, following the Strategy pattern:

- **Context**: The orchestrator (fraud_router)
- **Strategy Interface**: BaseChecker abstract class
- **Concrete Strategies**: Individual checker implementations

### 2. Template Method Pattern

BaseChecker defines the template for all checkers:

- Common attributes (type, weight) are defined in the base class
- Specific implementation is left to subclasses via the abstract `check` method

### 3. Async Coordination Pattern

The system uses async/await for coordinating multiple I/O operations:

```python
tasks = [checker.check(intervention) for checker in checkers]
results = await asyncio.gather(*tasks)
```

### 4. Factory Pattern

The `get_app()` function acts as a factory for creating the FastAPI application, enabling:

- Easy testing with different configurations
- Clean separation of app creation and startup logic

## Extension Points

### 1. Adding New Checker Types

To add a new fraud checker type:

1. Add the type to `FraudCheckerType` enum
2. Create a new checker class inheriting from `BaseChecker`
3. Implement the `check` method
4. Register the checker in the `checkers` list

### 2. Custom Aggregation Logic

The `calculate_fraud_score` function can be modified to implement different aggregation strategies:

- Majority voting
- Threshold-based detection
- Machine learning ensemble methods

### 3. Dynamic Checker Registration

Future enhancement could implement dynamic checker registration:

```python
class CheckerRegistry:
    def __init__(self):
        self.checkers = []

    def register(self, checker: BaseChecker):
        self.checkers.append(checker)

    def get_checkers(self) -> list[BaseChecker]:
        return self.checkers
```

### 4. Configuration Management

Environment-based configuration for checkers:

```python
@dataclasses.dataclass
class CheckerConfig:
    enabled: bool = True
    weight: float = 1.0
    timeout: float = 30.0
    # ... other config options
```

## Performance Considerations

### 1. Concurrent Execution

All checkers run concurrently, not sequentially:

- **Sequential**: Total time = sum of all checker times
- **Concurrent**: Total time = max(individual checker times)

### 2. Memory Usage

Each checker operates independently, avoiding shared state issues:

- No global state between checkers
- Clean separation of concerns
- Easy to reason about memory usage

### 3. Error Isolation

If one checker fails, others continue:

```python
# Future enhancement: individual error handling
async def safe_check(checker, intervention):
    try:
        return await checker.check(intervention)
    except Exception as e:
        # Log error and return default result
        return create_error_result(checker, e)
```

## Security Considerations

### 1. Input Validation

Pydantic models provide automatic input validation:

- Type checking
- Format validation (UUIDs, URLs)
- Required field enforcement

### 2. External Service Calls

Checkers making external API calls should implement:

- Timeout handling
- Retry logic with exponential backoff
- Circuit breaker patterns
- Authentication and authorization

### 3. Resource Limits

Consider implementing:

- Request rate limiting
- Memory usage limits
- Maximum execution time per checker

## Monitoring and Observability

### 1. Logging Strategy

Implement structured logging at different levels:

```python
import structlog

logger = structlog.get_logger()


async def check(self, intervention: Intervention) -> FraudCheckerDetail:
    logger.info(
        "checker_started",
        checker_type=self.type,
        intervention_id=intervention.id
    )
    # ... checker logic ...
    logger.info(
        "checker_completed",
        checker_type=self.type,
        fraud_detected=result.fraud_detected,
        fraud_rating=result.fraud_rating
    )
```

### 2. Metrics Collection

Key metrics to track:

- Request count and rate
- Response times (overall and per checker)
- Fraud detection rates
- Checker success/failure rates
- External service response times

### 3. Health Checks

The application includes health checks for:

- Application availability
- External service connectivity
- Resource usage monitoring

## Testing Strategy

### 1. Unit Testing

Test individual checkers in isolation:

```python
@pytest.mark.asyncio
async def test_text_checker():
    checker = BasicTextChecker(type=FraudCheckerType.TEXT)
    intervention = create_test_intervention()

    result = await checker.check(intervention)

    assert isinstance(result, FraudCheckerDetail)
    assert result.checker_type == FraudCheckerType.TEXT
```

### 2. Integration Testing

Test the complete fraud detection pipeline:

```python
@pytest.mark.asyncio
async def test_fraud_detection_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/fraud/detect", json=test_data)

        assert response.status_code == 200
        assert "fraud_detected" in response.json()
```

### 3. Contract Testing

Ensure checker implementations match the expected interface:

```python
def test_checker_contract(checker_class):
    """Test that checker class follows the expected contract"""
    assert issubclass(checker_class, BaseChecker)
    assert hasattr(checker_class, 'check')
    # ... additional contract tests
```

## Deployment Architecture

### 1. Container Strategy

The application is containerized for easy deployment:

- Multi-stage Docker build for optimization
- Non-root user for security
- Health checks for monitoring

### 2. Horizontal Scaling

The stateless design enables horizontal scaling:

- Each instance can handle requests independently
- No shared state between instances
- Load balancer can distribute requests

### 3. Environment Configuration

Use environment variables for configuration:

```python
import os


class Settings:
    api_timeout: float = float(os.getenv("API_TIMEOUT", "30.0"))
    external_service_url: str = os.getenv("EXTERNAL_SERVICE_URL", "")
```

## Future Enhancements

### 1. Dynamic Configuration

- Runtime checker registration/deregistration
- Dynamic weight adjustment
- Feature flags for enabling/disabling checkers

### 2. Advanced Aggregation

- Machine learning-based result aggregation
- Contextual weighting based on intervention type
- Confidence intervals for fraud scores

### 3. Caching Layer

- Cache results for similar interventions
- Reduce load on external services
- Configurable TTL based on checker type

### 4. Event Streaming

- Publish fraud detection events to message queue
- Enable real-time monitoring and alerting
- Support for event sourcing patterns

# Plugin Development Guide

This guide provides detailed instructions for developing fraud detection plugins (checkers) for the Rapid Intervention
Fraud Detection system.

## Table of Contents

- [Quick Start](#quick-start)
- [Checker Interface](#checker-interface)
- [Types of Checkers](#types-of-checkers)
- [Implementation Examples](#implementation-examples)
- [Best Practices](#best-practices)
- [Testing Your Checker](#testing-your-checker)
- [Advanced Topics](#advanced-topics)
- [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Create Your Checker Class

```python
# src/checkers/my_checker.py
from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, FraudCheckerType, Intervention


class MyChecker(BaseChecker):
    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        # Your fraud detection logic here
        return FraudCheckerDetail(
            checker_type=self.type,
            fraud_detected=False,  # Your logic result
            fraud_rating=0.0,  # Score between 0.0 and 1.0
            reason="Explanation of the check result",
            result_weight=self.result_weight,
        )
```

### 2. Register Your Checker

Add it to the checkers list in `src/main.py`:

```python
from src.checkers.my_checker import MyChecker

checkers = [
    BasicTextChecker(type=FraudCheckerType.TEXT),
    BasicApiChecker(type=FraudCheckerType.IMAGE, result_weight=4.0),
    MyChecker(type=FraudCheckerType.TEXT, result_weight=2.0),  # Add this
]
```

### 3. Test Your Checker

```bash
# Run the application
uv run python src/main.py

# Test with curl
curl -X POST "http://localhost:8000/fraud/detect" \
  -H "Content-Type: application/json" \
  -d '{"id": "550e8400-e29b-41d4-a716-446655440000", "title": "Test", "description": "Test description", "images": []}'
```

## Checker Interface

### BaseChecker Class

All fraud checkers must inherit from `BaseChecker`:

```python
@dataclasses.dataclass
class BaseChecker(ABC):
    type: FraudCheckerType  # The type of fraud checking this performs
    result_weight: float = 1.0  # Weight in final score calculation

    @abc.abstractmethod
    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        """
        Perform fraud checking on the given intervention.
        
        Args:
            intervention: The intervention to check for fraud
            
        Returns:
            FraudCheckerDetail: Result of the fraud check
        """
        ...
```

### Required Implementation

You must implement the `check` method with the following signature:

```python
async def check(self, intervention: Intervention) -> FraudCheckerDetail:
```

### Input: Intervention Object

The `Intervention` object contains:

```python
class Intervention(BaseModel):
    id: uuid.UUID  # Unique identifier
    title: str  # Title of the intervention
    description: str  # Detailed description
    images: list[Image]  # Associated images
```

### Output: FraudCheckerDetail Object

Your checker must return a `FraudCheckerDetail`:

```python
class FraudCheckerDetail(BaseModel):
    checker_type: FraudCheckerType  # Type of this checker
    image: Image | None = None  # Associated image (if applicable)
    fraud_detected: bool  # Whether fraud was detected
    fraud_rating: float  # Fraud confidence score (0.0-1.0)
    reason: str  # Human-readable explanation
    result_weight: float  # Weight of this result
```

## Types of Checkers

### FraudCheckerType Enum

Available checker types:

```python
class FraudCheckerType(Enum):
    INTERVENTION = "INTERVENTION"  # Analyzes the entire intervention
    TEXT = "TEXT"  # Analyzes text content
    IMAGE = "IMAGE"  # Analyzes images
```

### When to Use Each Type

- **INTERVENTION**: When analyzing the intervention as a whole (metadata, patterns, etc.)
- **TEXT**: When focusing on text analysis (title + description)
- **IMAGE**: When processing individual images or image metadata

### Adding New Types

If you need a new checker type:

1. Add it to the enum in `src/schema.py`:

```python
class FraudCheckerType(Enum):
    INTERVENTION = "INTERVENTION"
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    METADATA = "METADATA"  # New type
```

2. Use it in your checker:

```python
MyChecker(type=FraudCheckerType.METADATA)
```

## Implementation Examples

### 1. Simple Text Analysis Checker

```python
# src/checkers/keyword_checker.py
import re
from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, Intervention


class KeywordChecker(BaseChecker):
    def __init__(self, suspicious_keywords: list[str], **kwargs):
        super().__init__(**kwargs)
        self.suspicious_keywords = [kw.lower() for kw in suspicious_keywords]

    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        text_content = f"{intervention.title} {intervention.description}".lower()

        found_keywords = []
        for keyword in self.suspicious_keywords:
            if keyword in text_content:
                found_keywords.append(keyword)

        fraud_detected = len(found_keywords) > 0
        fraud_rating = min(len(found_keywords) * 0.3, 1.0)  # 0.3 per keyword, max 1.0

        if found_keywords:
            reason = f"Suspicious keywords found: {', '.join(found_keywords)}"
        else:
            reason = "No suspicious keywords detected"

        return FraudCheckerDetail(
            checker_type=self.type,
            fraud_detected=fraud_detected,
            fraud_rating=fraud_rating,
            reason=reason,
            result_weight=self.result_weight,
        )

# Usage in fraud_router.py:
# KeywordChecker(
#     type=FraudCheckerType.TEXT,
#     suspicious_keywords=["urgent", "emergency", "immediate", "crisis"],
#     result_weight=1.5
# )
```

### 2. External API Checker

```python
# src/checkers/sentiment_api_checker.py
import aiohttp
import asyncio
from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, Intervention


class SentimentAPIChecker(BaseChecker):
    def __init__(self, api_url: str, api_key: str, timeout: float = 10.0, **kwargs):
        super().__init__(**kwargs)
        self.api_url = api_url
        self.api_key = api_key
        self.timeout = timeout

    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        text_content = f"{intervention.title}. {intervention.description}"

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                payload = {"text": text_content}

                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status
                        )

                    result = await response.json()

                    sentiment_score = result.get("sentiment_score", 0.0)  # Assuming -1 to 1
                    confidence = result.get("confidence", 0.0)  # 0 to 1

                    # Convert sentiment to fraud probability
                    # Negative sentiment might indicate fraudulent content
                    if sentiment_score < -0.5:
                        fraud_detected = True
                        fraud_rating = abs(sentiment_score) * confidence
                        reason = f"Negative sentiment detected (score: {sentiment_score:.2f})"
                    else:
                        fraud_detected = False
                        fraud_rating = 0.0
                        reason = f"Normal sentiment (score: {sentiment_score:.2f})"

        except asyncio.TimeoutError:
            fraud_detected = False
            fraud_rating = 0.0
            reason = "Sentiment analysis timed out"

        except Exception as e:
            fraud_detected = False
            fraud_rating = 0.0
            reason = f"Sentiment analysis failed: {str(e)}"

        return FraudCheckerDetail(
            checker_type=self.type,
            fraud_detected=fraud_detected,
            fraud_rating=fraud_rating,
            reason=reason,
            result_weight=self.result_weight,
        )
```

### 3. Machine Learning Checker

```python
# src/checkers/ml_classifier_checker.py
import pickle
import numpy as np
from pathlib import Path
from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, Intervention


class MLClassifierChecker(BaseChecker):
    def __init__(self, model_path: str, feature_extractor=None, **kwargs):
        super().__init__(**kwargs)
        self.model_path = Path(model_path)
        self.feature_extractor = feature_extractor or self._default_feature_extractor
        self._load_model()

    def _load_model(self):
        """Load the pre-trained model"""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        except Exception as e:
            raise Exception(f"Failed to load model: {e}")

    def _default_feature_extractor(self, intervention: Intervention) -> np.ndarray:
        """Extract features from intervention for ML model"""
        features = [
            len(intervention.title),  # Title length
            len(intervention.description),  # Description length
            len(intervention.images),  # Number of images
            len(intervention.description.split()),  # Word count
            intervention.title.count('!'),  # Exclamation marks
            intervention.description.count('!'),
            1 if 'urgent' in intervention.title.lower() else 0,  # Urgency indicator
            1 if 'emergency' in intervention.description.lower() else 0,
        ]
        return np.array(features).reshape(1, -1)

    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        try:
            # Extract features
            features = self.feature_extractor(intervention)

            # Make prediction
            if hasattr(self.model, 'predict_proba'):
                # Classification with probability
                probabilities = self.model.predict_proba(features)[0]
                fraud_probability = probabilities[1] if len(probabilities) > 1 else probabilities[0]
                prediction = fraud_probability > 0.5
            else:
                # Simple binary classification
                prediction = bool(self.model.predict(features)[0])
                fraud_probability = 0.8 if prediction else 0.2

            fraud_detected = prediction
            fraud_rating = float(fraud_probability)

            if fraud_detected:
                reason = f"ML model detected fraud with {fraud_probability:.1%} confidence"
            else:
                reason = f"ML model found no fraud (confidence: {1 - fraud_probability:.1%})"

        except Exception as e:
            fraud_detected = False
            fraud_rating = 0.0
            reason = f"ML classifier failed: {str(e)}"

        return FraudCheckerDetail(
            checker_type=self.type,
            fraud_detected=fraud_detected,
            fraud_rating=fraud_rating,
            reason=reason,
            result_weight=self.result_weight,
        )
```

### 4. Image Analysis Checker

```python
# src/checkers/image_metadata_checker.py
import aiohttp
from PIL import Image as PILImage
from PIL.ExifTags import TAGS
import io
from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, Intervention, Image


class ImageMetadataChecker(BaseChecker):
    def __init__(self, max_file_size: int = 10 * 1024 * 1024, **kwargs):  # 10MB default
        super().__init__(**kwargs)
        self.max_file_size = max_file_size

    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        if not intervention.images:
            return FraudCheckerDetail(
                checker_type=self.type,
                fraud_detected=False,
                fraud_rating=0.0,
                reason="No images to analyze",
                result_weight=self.result_weight,
            )

        suspicious_count = 0
        total_images = len(intervention.images)
        issues_found = []

        for image in intervention.images:
            try:
                image_issues = await self._check_single_image(image)
                if image_issues:
                    suspicious_count += 1
                    issues_found.extend(image_issues)
            except Exception as e:
                issues_found.append(f"Failed to analyze image {image.id}: {str(e)}")

        fraud_detected = suspicious_count > 0
        fraud_rating = suspicious_count / total_images if total_images > 0 else 0.0

        if issues_found:
            reason = f"Image metadata issues: {'; '.join(issues_found)}"
        else:
            reason = f"All {total_images} images passed metadata validation"

        return FraudCheckerDetail(
            checker_type=self.type,
            fraud_detected=fraud_detected,
            fraud_rating=fraud_rating,
            reason=reason,
            result_weight=self.result_weight,
        )

    async def _check_single_image(self, image: Image) -> list[str]:
        """Check a single image for suspicious metadata"""
        issues = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image.url) as response:
                    if response.status != 200:
                        issues.append(f"Image {image.id} not accessible (HTTP {response.status})")
                        return issues

                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > self.max_file_size:
                        issues.append(f"Image {image.id} too large ({content_length} bytes)")
                        return issues

                    image_data = await response.read()

                    # Analyze with PIL
                    pil_image = PILImage.open(io.BytesIO(image_data))

                    # Check EXIF data
                    exif_data = pil_image.getexif()
                    if exif_data:
                        for tag_id, value in exif_data.items():
                            tag = TAGS.get(tag_id, tag_id)

                            # Check for signs of manipulation
                            if tag == "Software" and any(editor in str(value).lower()
                                                         for editor in ["photoshop", "gimp", "editor"]):
                                issues.append(f"Image {image.id} shows signs of editing ({value})")

                            # Check for missing camera info (might be stripped)
                            if tag in ["Make", "Model"] and not value:
                                issues.append(f"Image {image.id} missing camera metadata")

                    # Check image properties
                    width, height = pil_image.size
                    if width < 100 or height < 100:
                        issues.append(f"Image {image.id} unusually small ({width}x{height})")

                    if width > 10000 or height > 10000:
                        issues.append(f"Image {image.id} unusually large ({width}x{height})")

        except Exception as e:
            issues.append(f"Error analyzing image {image.id}: {str(e)}")

        return issues
```

## Best Practices

### 1. Error Handling

Always handle exceptions gracefully:

```python
async def check(self, intervention: Intervention) -> FraudCheckerDetail:
    try:
        # Your checking logic
        result = await self._perform_check(intervention)
        return self._create_success_result(result)

    except TimeoutError:
        return self._create_error_result("Operation timed out")

    except Exception as e:
        return self._create_error_result(f"Check failed: {str(e)}")


def _create_error_result(self, error_message: str) -> FraudCheckerDetail:
    return FraudCheckerDetail(
        checker_type=self.type,
        fraud_detected=False,  # Default to no fraud on error
        fraud_rating=0.0,
        reason=error_message,
        result_weight=self.result_weight,
    )
```

### 2. Configuration Management

Use constructor parameters for configuration:

```python
class ConfigurableChecker(BaseChecker):
    def __init__(self,
                 api_url: str,
                 timeout: float = 30.0,
                 retry_count: int = 3,
                 **kwargs):
        super().__init__(**kwargs)
        self.api_url = api_url
        self.timeout = timeout
        self.retry_count = retry_count
```

### 3. Logging

Add structured logging for debugging:

```python
import logging


class LoggedChecker(BaseChecker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        self.logger.info(f"Starting check for intervention {intervention.id}")

        try:
            result = await self._perform_check(intervention)
            self.logger.info(
                f"Check completed for {intervention.id}: "
                f"fraud_detected={result.fraud_detected}, "
                f"fraud_rating={result.fraud_rating}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Check failed for {intervention.id}: {e}")
            raise
```

### 4. Performance Optimization

#### Caching

```python
from functools import lru_cache


class CachedChecker(BaseChecker):
    @lru_cache(maxsize=1000)
    def _analyze_text(self, text: str) -> tuple[bool, float]:
        # Expensive text analysis here
        return fraud_detected, fraud_rating

    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        text_content = f"{intervention.title} {intervention.description}"
        fraud_detected, fraud_rating = self._analyze_text(text_content)
        # ... rest of implementation
```

#### Connection Pooling

```python
class PooledAPIChecker(BaseChecker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        if not self.session:
            self.session = aiohttp.ClientSession()

        # Use self.session for requests
        async with self.session.post(self.api_url, json=data) as response:
    # ... process response
```

### 5. Security Considerations

#### Input Sanitization

```python
import html
import re


class SecureChecker(BaseChecker):
    def _sanitize_text(self, text: str) -> str:
        # HTML escape
        text = html.escape(text)

        # Remove potential injection patterns
        text = re.sub(r'[<>\"\'&]', '', text)

        # Limit length
        return text[:1000]  # Truncate to prevent DoS

    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        safe_title = self._sanitize_text(intervention.title)
        safe_description = self._sanitize_text(intervention.description)
        # ... use sanitized data
```

#### Rate Limiting

```python
import asyncio
from collections import defaultdict
from time import time


class RateLimitedChecker(BaseChecker):
    def __init__(self, max_requests_per_minute: int = 60, **kwargs):
        super().__init__(**kwargs)
        self.max_requests_per_minute = max_requests_per_minute
        self.request_times = defaultdict(list)

    async def _wait_for_rate_limit(self, key: str = "global"):
        now = time()
        minute_ago = now - 60

        # Clean old requests
        self.request_times[key] = [
            req_time for req_time in self.request_times[key]
            if req_time > minute_ago
        ]

        # Check if we need to wait
        if len(self.request_times[key]) >= self.max_requests_per_minute:
            sleep_time = 60 - (now - self.request_times[key][0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        self.request_times[key].append(now)

    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        await self._wait_for_rate_limit()
        # ... perform check
```

## Testing Your Checker

### 1. Unit Tests

```python
# tests/test_my_checker.py
import pytest
import uuid
from src.checkers.my_checker import MyChecker
from src.schema import Intervention, Image, FraudCheckerType


@pytest.fixture
def sample_intervention():
    return Intervention(
        id=uuid.uuid4(),
        title="Test Intervention",
        description="This is a test intervention for fraud detection",
        images=[
            Image(
                id=uuid.uuid4(),
                url="https://example.com/test-image.jpg"
            )
        ]
    )


@pytest.fixture
def checker():
    return MyChecker(type=FraudCheckerType.TEXT, result_weight=2.0)


@pytest.mark.asyncio
async def test_checker_returns_correct_format(checker, sample_intervention):
    result = await checker.check(sample_intervention)

    assert hasattr(result, 'checker_type')
    assert hasattr(result, 'fraud_detected')
    assert hasattr(result, 'fraud_rating')
    assert hasattr(result, 'reason')
    assert hasattr(result, 'result_weight')

    assert isinstance(result.fraud_detected, bool)
    assert 0.0 <= result.fraud_rating <= 1.0
    assert isinstance(result.reason, str)


@pytest.mark.asyncio
async def test_checker_detects_fraud(checker):
    # Test case that should detect fraud
    fraudulent_intervention = Intervention(
        id=uuid.uuid4(),
        title="URGENT EMERGENCY!!!",
        description="Need immediate money transfer NOW!!!",
        images=[]
    )

    result = await checker.check(fraudulent_intervention)

    # Assert that fraud is detected (adjust based on your logic)
    # This is just an example
    assert result.fraud_detected == True
    assert result.fraud_rating > 0.5


@pytest.mark.asyncio
async def test_checker_no_fraud(checker):
    # Test case that should not detect fraud
    normal_intervention = Intervention(
        id=uuid.uuid4(),
        title="Regular maintenance work",
        description="Scheduled maintenance on the equipment",
        images=[]
    )

    result = await checker.check(normal_intervention)

    assert result.fraud_detected == False
    assert result.fraud_rating < 0.5


@pytest.mark.asyncio
async def test_checker_error_handling(checker):
    # Test error handling with invalid data
    # This depends on your checker implementation
    pass
```

### 2. Integration Tests

```python
# tests/test_integration.py
import pytest
from httpx import AsyncClient
from src.main import get_app


@pytest.mark.asyncio
async def test_fraud_detection_with_new_checker():
    app = get_app()

    async with AsyncClient(app=app, base_url="http://test") as client:
        test_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Test Title",
            "description": "Test Description",
            "images": []
        }

        response = await client.post("/fraud/detect", json=test_data)

        assert response.status_code == 200
        result = response.json()

        # Verify your checker appears in results
        checker_results = [
            detail for detail in result["details"]
            if detail["checker_type"] == "TEXT"  # Your checker type
        ]

        assert len(checker_results) > 0
        assert all(
            0.0 <= detail["fraud_rating"] <= 1.0
            for detail in checker_results
        )
```

### 3. Performance Tests

```python
# tests/test_performance.py
import pytest
import time
from src.checkers.my_checker import MyChecker
from src.schema import FraudCheckerType


@pytest.mark.asyncio
async def test_checker_performance(sample_intervention):
    checker = MyChecker(type=FraudCheckerType.TEXT)

    start_time = time.time()
    result = await checker.check(sample_intervention)
    end_time = time.time()

    execution_time = end_time - start_time

    # Assert reasonable execution time (adjust threshold as needed)
    assert execution_time < 5.0, f"Checker took too long: {execution_time}s"

    # Verify result is still valid
    assert hasattr(result, 'fraud_detected')
```

### 4. Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_my_checker.py

# Run with coverage
uv run pytest --cov=src tests/

# Run performance tests only
uv run pytest tests/test_performance.py -v
```

## Advanced Topics

### 1. Async Context Managers

For checkers that need resource management:

```python
class ResourceManagedChecker(BaseChecker):
    async def __aenter__(self):
        self.connection = await create_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'connection'):
            await self.connection.close()

    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        # Use self.connection
        pass


# Usage in fraud_router.py:
async def run_checkers(intervention: Intervention) -> FraudDetectionResult:
    tasks = []

    for checker in checkers:
        if hasattr(checker, '__aenter__'):
            async with checker:
                task = checker.check(intervention)
        else:
            task = checker.check(intervention)
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    # ... rest of function
```

### 2. Dynamic Checker Loading

For loading checkers from configuration:

```python
# src/checker_registry.py
import importlib
from typing import Type
from src.checkers.base import BaseChecker


class CheckerRegistry:
    def __init__(self):
        self.checkers: list[BaseChecker] = []

    def load_from_config(self, config: dict):
        for checker_config in config.get("checkers", []):
            checker_class = self._import_checker_class(checker_config["class"])
            checker_instance = checker_class(**checker_config["params"])
            self.checkers.append(checker_instance)

    def _import_checker_class(self, class_path: str) -> Type[BaseChecker]:
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

# Configuration file (config.yml):
# checkers:
#   - class: "src.checkers.keyword_checker.KeywordChecker"
#     params:
#       type: "TEXT"
#       result_weight: 1.5
#       suspicious_keywords: ["urgent", "emergency"]
```

### 3. Circuit Breaker Pattern

For resilient external service calls:

```python
import asyncio
from enum import Enum
from time import time


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        return (time() - self.last_failure_time) >= self.recovery_timeout

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


class ResilientAPIChecker(BaseChecker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30.0
        )

    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        try:
            result = await self.circuit_breaker.call(
                self._make_api_call,
                intervention
            )
            return self._process_api_result(result)

        except Exception as e:
            return FraudCheckerDetail(
                checker_type=self.type,
                fraud_detected=False,
                fraud_rating=0.0,
                reason=f"Service unavailable: {str(e)}",
                result_weight=self.result_weight,
            )
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: `ModuleNotFoundError` when importing your checker

**Solution**:

- Ensure `PYTHONPATH` includes the project root
- Check that `__init__.py` files exist in all package directories
- Verify the import path is correct

```bash
export PYTHONPATH=/path/to/rapid-intervention-fraud-detection
```

#### 2. Async/Await Issues

**Problem**: `RuntimeError: coroutine was never awaited`

**Solution**: Always use `await` with async functions:

```python
# Wrong
result = checker.check(intervention)

# Correct
result = await checker.check(intervention)
```

#### 3. Type Validation Errors

**Problem**: Pydantic validation errors when returning results

**Solution**: Ensure all required fields are included and have correct types:

```python
return FraudCheckerDetail(
    checker_type=self.type,  # Must be FraudCheckerType enum
    image=None,  # Image object or None
    fraud_detected=bool_value,  # Must be boolean
    fraud_rating=float_value,  # Must be float between 0.0-1.0
    reason="string_value",  # Must be string
    result_weight=self.result_weight,  # Must be float
)
```

#### 4. Timeout Issues

**Problem**: Checker operations timing out

**Solution**: Implement proper timeout handling:

```python
import asyncio


async def check(self, intervention: Intervention) -> FraudCheckerDetail:
    try:
        result = await asyncio.wait_for(
            self._long_running_operation(intervention),
            timeout=30.0  # 30 second timeout
        )
        return result
    except asyncio.TimeoutError:
        return self._create_timeout_result()
```

### Debugging Tips

#### 1. Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def check(self, intervention: Intervention) -> FraudCheckerDetail:
    logger.debug(f"Starting check for intervention: {intervention.id}")
    # ... your logic
    logger.debug(f"Check result: fraud_detected={result.fraud_detected}")
    return result
```

#### 2. Test Individual Checkers

```python
# test_individual_checker.py
import asyncio
import uuid
from src.checkers.my_checker import MyChecker
from src.schema import Intervention, FraudCheckerType


async def test_checker():
    checker = MyChecker(type=FraudCheckerType.TEXT)

    intervention = Intervention(
        id=uuid.uuid4(),
        title="Test",
        description="Test description",
        images=[]
    )

    result = await checker.check(intervention)
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(test_checker())
```

#### 3. Mock External Dependencies

```python
# For testing
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_api_checker_with_mock():
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"fraud_score": 0.3}
        mock_post.return_value.__aenter__.return_value = mock_response

        checker = MyAPIChecker(type=FraudCheckerType.TEXT)
        result = await checker.check(sample_intervention)

        assert result.fraud_rating == 0.3
```

### Performance Optimization

#### 1. Profile Your Checker

```python
import cProfile
import asyncio


async def profile_checker():
    # Your test code here
    pass


if __name__ == "__main__":
    cProfile.run("asyncio.run(profile_checker())")
```

#### 2. Memory Usage Monitoring

```python
import tracemalloc
import asyncio


async def monitor_memory():
    tracemalloc.start()

    # Your checker code here

    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory usage: {current / 1024 / 1024:.2f} MB")
    print(f"Peak memory usage: {peak / 1024 / 1024:.2f} MB")

    tracemalloc.stop()


if __name__ == "__main__":
    asyncio.run(monitor_memory())
```

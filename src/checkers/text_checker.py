import aiohttp

from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, Intervention


class TextChecker(BaseChecker):
    api_endpoint: str

    def __init__(self, api_endpoint: str, **kwargs):
        super().__init__(**kwargs)
        self.api_endpoint = api_endpoint

    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        # Send intervention description to text analysis API endpoint
        async with aiohttp.ClientSession() as session:
            try:
                # Create JSON payload with intervention description
                payload = {"intervention_description": [intervention.description]}

                # Send to API endpoint with JSON
                async with session.post(
                    self.api_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status == 200:
                        result_data = await response.json()

                        # Extract analysis results (API returns list of results)
                        results = result_data.get("results", [])
                        if not results:
                            return self.create_result(
                                fraud_detected=False,
                                fraud_rating=0.0,
                                reason="No analysis results returned from text API",
                            )

                        # Get the first result (we only send one description)
                        analysis = results[0]

                        # Extract text analysis data
                        total_word_count = analysis.get("total_word_count", 0)
                        clarity_score = analysis.get("clarity_score", 0.0)
                        is_clear_enough = analysis.get("is_clear_enough", True)
                        entities_found = analysis.get("entities_found", [])
                        entity_count = analysis.get("entity_count", 0)

                        # Determine if text is suspicious based on analysis
                        # Consider it suspicious if text is not clear enough or has very low word count
                        is_suspicious = not is_clear_enough or total_word_count < 5

                        # Calculate fraud rating based on clarity and completeness
                        fraud_rating = 0.0
                        if not is_clear_enough and total_word_count < 3:
                            fraud_rating = (
                                0.8  # Very suspicious - unclear and very short
                            )
                        elif not is_clear_enough:
                            fraud_rating = 0.6  # Suspicious - unclear text
                        elif total_word_count < 5:
                            fraud_rating = 0.4  # Somewhat suspicious - very short text

                        # Build reason from analysis
                        if is_suspicious:
                            reasons = []
                            if not is_clear_enough:
                                reasons.append(
                                    f"text clarity insufficient (score: {clarity_score:.2f})"
                                )
                            if total_word_count < 5:
                                reasons.append(
                                    f"description too brief ({total_word_count} words)"
                                )

                            reason = f"Suspicious text detected: {', '.join(reasons)}"
                        else:
                            reason = f"Text analysis completed (clarity: {clarity_score:.2f}, words: {total_word_count})"

                        # Add entity information if available
                        if entity_count > 0:
                            # Handle entities_found which may contain dict objects instead of strings
                            entity_names = []
                            for entity in entities_found:
                                if isinstance(entity, dict):
                                    # If entity is a dict, try to extract a name/text field
                                    name = (
                                        entity.get("name")
                                        or entity.get("text")
                                        or entity.get("entity")
                                        or str(entity)
                                    )
                                    entity_names.append(name)
                                elif entity:  # If it's already a string and not empty
                                    entity_names.append(str(entity))

                            if entity_names:
                                reason += f". Entities found ({entity_count}): {', '.join(entity_names[:3])}"
                                if len(entity_names) > 3:
                                    reason += f" and {len(entity_names) - 3} more"
                            else:
                                reason += f". {entity_count} entities detected"

                        return self.create_result(
                            fraud_detected=is_suspicious,
                            fraud_rating=fraud_rating,
                            reason=reason,
                        )

                    else:
                        # Log the error response for debugging
                        try:
                            error_text = await response.text()
                            print(f"Text API Error {response.status}: {error_text}")
                        except Exception:
                            print(f"Text API returned status {response.status}")

                        return self.create_result(
                            fraud_detected=False,
                            fraud_rating=0.0,
                            reason=f"Text API error: {response.status}",
                        )

            except Exception as e:
                # Handle network or other errors
                print(f"Text checker error: {e}")
                return self.create_result(
                    fraud_detected=False,
                    fraud_rating=0.0,
                    reason=f"Text analysis failed: {str(e)}",
                )

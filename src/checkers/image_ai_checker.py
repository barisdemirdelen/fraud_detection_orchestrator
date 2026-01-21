import aiohttp

from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, Intervention


class ImageAiChecker(BaseChecker):
    api_endpoint: str

    def __init__(self, api_endpoint: str, **kwargs):
        super().__init__(**kwargs)
        self.api_endpoint = api_endpoint

    async def check(
        self, intervention: Intervention
    ) -> FraudCheckerDetail | list[FraudCheckerDetail]:
        # Download images and send as form-data to API endpoint
        results = []
        async with aiohttp.ClientSession() as session:
            try:
                # Process each image
                for image in intervention.images:
                    # Download image data
                    async with session.get(image.url) as image_response:
                        if image_response.status != 200:
                            continue
                        image_data = await image_response.read()

                    # Create form data with the image as binary (API expects "file" field)
                    data = aiohttp.FormData()
                    data.add_field(
                        "file",
                        image_data,
                        filename=f"image_{image.id}.jpg",
                        content_type="image/jpeg",
                    )

                    # Send to API endpoint with form data
                    async with session.post(self.api_endpoint, data=data) as response:
                        if response.status == 200:
                            result_data = await response.json()

                            # Extract fraud detection info from new API response format
                            is_ai_generated = result_data.get("is_ai_generated", False)
                            confidence_score = result_data.get("confidence_score", 0.0)
                            analysis_details = result_data.get("analysis_details", {})

                            # Consider it fraud if AI generated
                            fraud_detected = is_ai_generated

                            # Build reason from analysis
                            if is_ai_generated:
                                reason = f"AI generated image detected (confidence: {confidence_score:.2f})"
                                if analysis_details:
                                    # Include any additional details if available
                                    details_str = ", ".join(
                                        f"{k}: {v}"
                                        for k, v in analysis_details.items()
                                        if v
                                    )
                                    if details_str:
                                        reason += f". Additional details: {details_str}"
                            else:
                                reason = f"No AI generation detected (confidence: {confidence_score:.2f})"

                            results.append(
                                self.create_result(
                                    fraud_detected=fraud_detected,
                                    fraud_rating=confidence_score,
                                    reason=reason,
                                    image=image,
                                )
                            )
                        else:
                            # Log the error response for debugging
                            try:
                                error_text = await response.text()
                                print(f"API Error {response.status}: {error_text}")
                            except Exception as e:
                                print(f"API returned status {response.status} {e}")

                            results.append(
                                self.create_result(
                                    fraud_detected=False,
                                    fraud_rating=0.0,
                                    image=image,
                                    reason=f"API error: {response.status}",
                                )
                            )
                            continue

                return results

            except Exception as e:
                # Handle network or other errors
                raise e

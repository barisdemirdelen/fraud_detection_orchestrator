import aiohttp

from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, Intervention


class ImageAnalyzerApiChecker(BaseChecker):
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

                    # Create form data with the image as binary
                    data = aiohttp.FormData()
                    data.add_field(
                        "file",
                        image_data,
                        filename=f"image_{image.id}",
                        content_type="image/jpeg",
                    )

                    # Send to API endpoint
                    async with session.post(self.api_endpoint, data=data) as response:
                        if response.status == 200:
                            result_data = await response.json()

                            # Extract fraud detection info from API response
                            overall_score = result_data.get("overall_fraud_score", 0.0)
                            ai_detection = result_data.get("ai_detection", {})
                            summary = result_data.get("summary", {})

                            # Determine if fraud is detected based on score and AI detection
                            is_ai_generated = ai_detection.get("is_ai_generated", False)
                            confidence_score = ai_detection.get("confidence_score", 0.0)

                            # Consider it fraud if AI generated or high overall score
                            fraud_detected = is_ai_generated or overall_score > 0.7

                            # Build detailed reason from analysis
                            primary_concerns = summary.get("primary_concerns", [])
                            risk_level = (
                                "high"
                                if summary.get("high_risk")
                                else "medium"
                                if summary.get("medium_risk")
                                else "low"
                            )

                            if is_ai_generated:
                                reason = f"AI generated image detected (confidence: {confidence_score:.2f})"
                                if primary_concerns:
                                    reason += f". Primary concerns: {', '.join(primary_concerns)}"
                            elif overall_score > 0.5:
                                reason = f"Suspicious image detected (score: {overall_score:.2f}, risk: {risk_level})"
                                if primary_concerns:
                                    reason += (
                                        f". Concerns: {', '.join(primary_concerns)}"
                                    )
                            else:
                                reason = f"Image analysis completed (score: {overall_score:.2f}, risk: {risk_level})"

                            results.append(
                                self.create_result(
                                    fraud_detected=fraud_detected,
                                    fraud_rating=overall_score,
                                    reason=reason,
                                    image=image,
                                )
                            )
                        else:
                            results.append(
                                self.create_result(
                                    fraud_detected=False,
                                    fraud_rating=0.0,
                                    image=image,
                                    reason="Api not available pr returned an error.",
                                )
                            )
                            continue

                return results

            except Exception as e:
                # Handle network or other errors
                raise e

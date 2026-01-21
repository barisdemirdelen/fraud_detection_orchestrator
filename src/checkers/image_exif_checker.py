import aiohttp

from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, Intervention


class ImageExifChecker(BaseChecker):
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

                            # Extract EXIF analysis info from API response
                            exif_data = result_data.get("exif_data", {})
                            is_suspicious = result_data.get("is_suspicious", False)
                            is_edited = result_data.get("is_edited", False)
                            editing_indicators = result_data.get(
                                "editing_indicators", {}
                            )

                            # Consider it fraud if suspicious or edited
                            fraud_detected = is_suspicious or is_edited

                            # Build reason from EXIF analysis
                            if is_edited and is_suspicious:
                                reason = "Image appears to be edited and shows suspicious EXIF patterns"
                            elif is_edited:
                                reason = "Image appears to be edited"
                            elif is_suspicious:
                                reason = "Image shows suspicious EXIF patterns"
                            else:
                                reason = "No suspicious EXIF patterns detected"

                            # Add EXIF details if available
                            exif_details = []
                            if exif_data.get("software"):
                                exif_details.append(
                                    f"Software: {exif_data['software']}"
                                )
                            if exif_data.get("make") and exif_data.get("model"):
                                exif_details.append(
                                    f"Camera: {exif_data['make']} {exif_data['model']}"
                                )
                            if exif_data.get("datetime_original"):
                                exif_details.append(
                                    f"Date taken: {exif_data['datetime_original']}"
                                )

                            if exif_details:
                                reason += f". EXIF details: {', '.join(exif_details)}"

                            # Add editing indicators if available
                            if editing_indicators:
                                indicators = [
                                    f"{k}: {v}"
                                    for k, v in editing_indicators.items()
                                    if v
                                ]
                                if indicators:
                                    reason += (
                                        f". Editing indicators: {', '.join(indicators)}"
                                    )

                            # Calculate fraud rating based on suspicion and editing
                            fraud_rating = 0.0
                            if is_suspicious and is_edited:
                                fraud_rating = 0.9
                            elif is_suspicious:
                                fraud_rating = 0.7
                            elif is_edited:
                                fraud_rating = 0.5

                            results.append(
                                self.create_result(
                                    fraud_detected=fraud_detected,
                                    fraud_rating=fraud_rating,
                                    reason=reason,
                                    image=image,
                                )
                            )
                        else:
                            # Log the error response for debugging
                            try:
                                error_text = await response.text()
                                print(f"EXIF API Error {response.status}: {error_text}")
                            except Exception:
                                print(f"EXIF API returned status {response.status}")

                            results.append(
                                self.create_result(
                                    fraud_detected=False,
                                    fraud_rating=0.0,
                                    image=image,
                                    reason=f"EXIF API error: {response.status}",
                                )
                            )

                return results

            except Exception as e:
                # Handle network or other errors
                raise e

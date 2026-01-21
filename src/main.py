import asyncio

import uvicorn
from fastapi import FastAPI

from src.checkers.basic_api_checker import BasicApiChecker
from src.checkers.basic_text_checker import BasicTextChecker
from src.fraud_router import router as fraud_router
from src.schema import FraudCheckerType

checkers = [
    BasicTextChecker(type=FraudCheckerType.TEXT),
    BasicApiChecker(type=FraudCheckerType.IMAGE, result_weight=4.0),
]


def get_app():
    app = FastAPI(title="Rapid Intervention Fraud Detection")

    app.include_router(fraud_router)

    return app


async def main():
    app = get_app()
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())

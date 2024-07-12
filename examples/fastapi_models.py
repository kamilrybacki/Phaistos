import os
import logging
import typing

import fastapi
import uvicorn

import phaistos  # type: ignore
import phaistos.schema  # type: ignore


example_schemas_path = os.path.join(os.path.dirname(__file__), 'schemas')
os.environ['PHAISTOS__SCHEMA_PATH'] = example_schemas_path
app = fastapi.FastAPI()
manager = phaistos.Manager.start()

response_model = manager.get_factory('Mockument')


MOCKUMENTS = {
    1: {
        "name": "The Mockument",
        "year": 2021,
        "rating": 10.0,
    },
    2: {  # This one has no name and the year is in future
        "name": "",
        "year": 2025,
        "rating": 9.0,
    },
    3: {  # This one has only invalid rating
        "name": "The Mockument 3",
        "year": 2023,
        "rating": -1.0,
    },
}


@app.get("/", response_class=fastapi.responses.HTMLResponse)
def index():
    return """
    <html>
    <body>
    <h1>FastAPI + Phaistos</h1>
    <p>
        Visit <a href="/mockument">/mockument</a> to see the Phaistos schema in action!
    </p>
    """


def build_mockument_data(mockument_id: int):
    if not (mockument_data := MOCKUMENTS.get(mockument_id)):
        raise fastapi.HTTPException(status_code=404, detail="Mockument not found")
    if validated_data := response_model.build(mockument_data):
        manager.logger.info(f"Built mockument data: {validated_data}")
        return validated_data
    manager.logger.info(f"Failed to build mockument data: {mockument_data}")
    raise fastapi.HTTPException(
        status_code=400,
        detail=f"Invalid data: {'; '.join([
            str(error)
            for error in response_model.errors
        ])}"
    )


@app.get("/mockument/{mockument_id}")
def get_mockument(
    mockument: typing.Annotated[
        type[phaistos.schema.TranspiledSchema],
        fastapi.Depends(build_mockument_data)
    ]
):
    return mockument


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        app,
        host="localhost",
        port=42069,
    )

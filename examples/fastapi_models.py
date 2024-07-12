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
        Visit <a href="/mockuments">/mockuments</a> to see the Phaistos schema in action!
    </p>
    """


@app.get("/mockuments", response_class=fastapi.responses.HTMLResponse)
def mockument():
    mockuments_list = '<br>'.join([
        f'<a href="/mockuments/{mockument_id}">Mockument {mockument_id}</a>'
        for mockument_id in MOCKUMENTS
    ])
    return f"""
    <html>
    <body>
    <h1>Mockument</h1>
    <p>
        {mockuments_list}
    </p>
    """


def build_mockument_data(mockument_id: int) -> phaistos.schema.TranspiledSchema:
    """
    Build mockument data from the mockument ID.
    Injected as a dependency to the FastAPI endpoint.

    Args:
        mockument_id (int): The mockument ID (taken from the URL query params).

    Returns:
        phaistos.schema.TranspiledSchema: The built mockument data.

    Raises:
        fastapi.HTTPException: If the mockument ID is not found or the data is invalid.
    """
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


@app.get("/mockuments/{mockument_id}")
def get_mockument(
    mockument: typing.Annotated[
        type[phaistos.schema.TranspiledSchema],
        fastapi.Depends(build_mockument_data)  # Inject the built mockument data
    ]
):
    """
    Get a mockument by its ID.
    """
    return mockument


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)  # Set logging level to INFO
    uvicorn.run(
        app,
        host="localhost",
        port=42069,
    )

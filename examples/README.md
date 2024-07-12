# Phaistos usage examples

## Before you start

Make sure you have installed the Phaistos library. If you haven't, you can install it using pip:

```bash
    pip install phaistos
```

## Introduction

This directory contains several examples of how to use the Phaistos library. The examples are written in Python and are intended to be run from the command line.

```bash
    python3 <example>.py
```

All examples use YAML manifests located in the `schemas/` directory.

## Examples

* [**`automatic.py`**](automatic.py): An example of how to use the automatic schema discovery and data validation features of Phaistos.
* [**`instances.py`**](instances.py): An example of how to manually define a schema and validate data against it to create structured data entries.
* [**`skip_discovery.py`**](skip_discovery.py): An example of how to skip the automatic schema discovery and manually define a schema to validate data against it.
* [**`fastapi_models.py`**](fastapi_models.py): An example of how to use Phaistos with FastAPI to validate incoming requests and responses.

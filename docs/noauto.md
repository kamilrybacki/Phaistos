## Manual manifest loading

There is an option to disable automatic schema discovery to then
load the schema manifests manually, either with data read from a file
or by constructing the schema directly in the code.

To do this, set the `PHAISTOS__DISABLE_SCHEMA_DISCOVERY` environment variable
to any value.

```bash
export PHAISTOS__DISABLE_SCHEMA_DISCOVERY=1
```

This will prevent the automatic schema discovery during the first initialization
of the `Validator` class. Then new schemas can be inserted manually, using
`load_schema` method.

Here is an example of how you can load a schema manifest from a file:

```python
from phaistos import Validator

# Initialize the Validator
validator = Validator.start()

# Create schema manually

schema = {
    "version": "v1",
    "description": "A schema for a person",
    "name": "Person",
    "properties": {
        "name": {
            "type": "str",
            "description": "The name of the person"
        },
        "age": {
            "type": "int",
            "description": "The age of the person",
            "validator": 'if value < 18: raise ValueError("The age must be at least 18")'
        },
        "email": {
            "type": "str",
            "description": "The email of the person"
        }
    }
}

# Load the schema - this will return the name of the schema
# that can be used in the against_schema method
schema_name = validator.load_schema(schema)

# Validate data against the schema
data = {
    "name": "John Doe",
    "age": 30,
    "email": "xxx@gmail.com"
}

# Validate the data against the schema
result = validator.against_schema(
    data=data,
    schema=schema_name
)
```

In this example, we first initialize the `Validator` class and then load a schema
manually. The schema is a dictionary that describes the schema manifest and
adheres to the `SchemaInputFile` structure:

**phaistos.typings.SchemaInputFile**

::: phaistos.typings.SchemaInputFile

**phaistos.typings.RawSchemaProperty**

::: phaistos.typings.RawSchemaProperty

The `load_schema` method is used to load the schema into the `Validator` object,
which can be then used as a target for `against_schema` method. The `schema`
argument **must match** the `name` field in the schema manifest (here: `Person`).
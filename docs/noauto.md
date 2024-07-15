## Manual manifest loading

There are two options to disable automatic schema discovery to then
load the schema manifests manually, either with data read from a file
or by constructing the schema directly in the code.

First is by using optional `discover` argument of the `Manager.start`
class method, which by default looks if the `PHAISTOS__DISABLE_SCHEMA_DISCOVERY`
environment variable is set to any value. If yes: the automatic schema
discovery is disabled.

```python
from phaistos import Manager

# Initialize the manager
manager = Manager.start(discover=False)
```

This will result with a `Manager` object that has no schemas loaded
(its `_schemas` attribute is an empty dictionary). The schemas can
be then loaded manually, using `load_schema` method.

The second option is to disable the automatic schema discovery via aforementioned
environment variable. To do this, set the `PHAISTOS__DISABLE_SCHEMA_DISCOVERY` environment variable
to any value.

```bash
export PHAISTOS__DISABLE_SCHEMA_DISCOVERY=1
```

This will prevent the automatic schema discovery during the first initialization
of the `Manager` class. Then new schemas can be inserted manually, using
`load_schema` method.

Here is an example of how you can load a schema manifest from a file:

```python
from phaistos import Manager

# Initialize the manager
manager = Manager.start()  # manager._schemas is now equal to {}

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
            "manager": 'if value < 18: raise ValueError("The age must be at least 18")'
        },
        "email": {
            "type": "str",
            "description": "The email of the person"
        }
    }
}

# Load the schema - this will return the name of the schema
# that can be used in the validate method
schema_name = manager.load_schema(schema)

# Validate data against the schema
data = {
    "name": "John Doe",
    "age": 30,
    "email": "xxx@gmail.com"
}

# Validate the data against the schema
result = manager.validate(
    data=data,
    schema=schema_name
)
```

In this example, we first initialize the `Manager` class and then load a schema
manually. The schema is a dictionary that describes the schema manifest and
adheres to the `SchemaInputFile` structure:

**phaistos.typings.SchemaInputFile**

::: phaistos.typings.SchemaInputFile

**phaistos.typings.RawSchemaProperty**

::: phaistos.typings.RawSchemaProperty

The `load_schema` method is used to load the schema into the `Manager` object,
which can be then used as a target for `validate` method. The `schema`
argument **must match** the `name` field in the schema manifest (here: `Person`).

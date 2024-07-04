## Main workhorse - Transpiler

The main component of Phaistos is the transpiler, which is responsible for converting the YAML schema into a Pydantic model.

This object is used under-the-hood by the `Validator` class (to be described in a lil' bit) automatically, but there is nothing stopping You from using it
declaratively in Your code. The transpiler is devoid of state, so it can
be directly used in a functional manner.

Below, the main methods of the transpiler are described.

### Schema transpilation

This action is performed by `schema` method and is responsible for converting the YAML schema into a Pydantic model and returns it.

`phaistos.transpiler.Transpiler.schema`

::: phaistos.transpiler.Transpiler.schema

As for the information returned by this method, it is a Pydantic model, which can be used to validate the data with some fields automatically injected during transpilation:

`phaistos.schema.TranspiledSchema`

::: phaistos.schema.TranspiledSchema

If You poke around the source code (or believe me on my word), You will find that the transpiler is a simple class with a single method, which is responsible for compiling the schema data into a Pydantic model.

The schema data is a dictionary, which is a result of parsing the YAML schema file. It is a collection of fields, which are then converted into Pydantic fields
and compiled validator functions, which are then used to validate the data.

::: phaistos.typings.TranspiledModelData

Each property is expressed with a 3-tuple, where the first element is the field name, the second is the field type, and the third is the field default value.

As for the validators, the compiled functions are stored as dictionaries of `TranspiledPropertyValidator` dictionaries:

`phaistos.typings.TranspiledPropertyValidator`

::: phaistos.typings.TranspiledPropertyValidator

### So, how can I use it?

The transpiler is a simple object, which can be used in a functional manner. Below is an example of how to use it:

```python
from phaistos import Transpiler
from phaistos.typings import TranspiledSchema

schema_read_from-data = ... # Read the schema from a file or something

transpiled_schema: TranspiledSchema = Transpiler.schema(schema_read_from_data)
```

After that, the `TranspiledSchema` can be manually invoked via `validate` method,
which takes the data to be validated as an argument:

```python
data = ... # Read the data from somewhere

transpiled_schema.validate(data)
```

Congratulations! You have performed the thing that the `Validator` class does
in the background.

### Get the data model

If You need to get the Pydantic model for a schema, you can use the `get_model` method:

```python
from phaistos import Validator

# Initialize the Validator
validator = Validator.start()

schema_name = "person"

# Get the Pydantic model for the schema
model = validator.get_model(schema_name)
```

This model can be then used to create instances of the underlying data classes:

```python
data = {
    "name": "John Doe",
    "age": 30,
    "email": "xxx@yahoo.com"
}

# Create an instance of the Pydantic model
instance = model(**data)
```

This approch is useful when the data is to be used in a more object-oriented way e.g. when creating entries to a database.

#### What is the difference between `validate` and `get_model`?

The `validate` method is used to validate the data against the schema, while the `get_model` method is used to get the Pydantic model for the schema.

So, the main result of `validate` is just a report on whether the data is valid or not, while the `get_model` method returns the Pydantic model, which can be used to create instances of the data classes.

So, in short:

* `get_model` -> `model` -> `model(**data)` -> VALIDATION -> CLEAN INSTANCE

* `validate` -> VALIDATION -> IS VALID?

## Schema manifest

Custom data schemas are defined for Phaistos using YAML manifests.
The general structure of a schema manifest is as follows:

```yaml
version: <SCHEMA VERSION>
name: <SCHEMA NAME>
description: <SCHEMA DESCRIPTION>
properties:
    <FIELD_NAME>:
        type: <FIELD_TYPE>
        description: <FIELD_DESCRIPTION>
        validator?: |
            <VALIDATOR_CODE>
        default?: <DEFAULT_VALUE>
```

The restrictions for names are the same as for Python variables, so they must start with a letter and can contain only letters, numbers, and underscores. **DO NOT USE UNDERSCORED** (they will be ignored in the resulting Pydantic models).

Phaistos allows you to define data fields and their types in a simple and intuitive way. All built-in Python types are supported, so you can define fields as `str`, `int`, `float` and `bool`.

Given that there are inherent limitations in the YAML format, the only container types supported are `list` and `dict`.

### `list` type

The `list` type is defined by specifying the type of the elements in the list,
similarly how they are defined inside Python code e.g. `list[int]`, `list[str]`, `list[float]`, `list[bool]`:

```yaml
version: <SCHEMA VERSION>
name: <SCHEMA NAME>
description: <SCHEMA DESCRIPTION>
properties:
    <FIELD_NAME>:
        type: list[<ELEMENT_TYPE>]
        description: <FIELD_DESCRIPTION>
        validator?: |
            <VALIDATOR_CODE>
        default?: <DEFAULT_VALUE>
```

The transpiled model will be equipped from the get-go with a `list` validator, which will ensure that the data is a list and that all elements in the list are of the specified type.

### `dict` type

The `dict` type is treated as a **nested schema** so, in simple words, the transpiler will generate a new model for the nested schema and define it as an annotation in the parent model.

You can define nested schemas by specifying the `type` as `dict` and then defining the nested schema inside the `properties` key, as shown in the example below:

```yaml
version: <SCHEMA VERSION>
name: <SCHEMA NAME>
description: <SCHEMA DESCRIPTION>
properties:
    <FIELD_NAME>:
        description: <FIELD_DESCRIPTION>
        properties:
            <NESTED_FIELD_NAME>:
                type: <NESTED_FIELD_TYPE>
                description: <NESTED_FIELD_DESCRIPTION>
                validator?: |
                    <NESTED_VALIDATOR_CODE>
                default?: <NESTED_DEFAULT_VALUE>
```

### `validator` field

The `validator` field is optional and allows you to define custom validation functions for the data field. The code inside the `validator` field will be injected into the Pydantic model as a custom validator function.

The code inside the `validator` field must be a valid Python code snippet that includes a snippet that is to be executed before the `return` statement in the validator function.

The main rules are:

1. The code must be a valid Python code snippet.
2. Refer to the field value as `value`.
3. Define it as a **multiline string** using the `|` character.
4. **DO NOT** use the `return` statement in the code snippet.

The **compiled** validator function will be composed of the following parts:

```python
def validate_<FIELD_NAME>(value: <FIELD_TYPE>) -> <FIELD_TYPE>:
    # Custom validator code
    <VALIDATOR_CODE> # Injected code taken from the schema manifest
    <COLLECTION_VALIDATOR_CODE> # Injected code for list type
    return value
```

This is done **automagically** by the Phaistos transpiler, so you don't have to worry about the details of the Pydantic model generation.

#### The bummer

There are modules which are considered critical and are blocked from being imported in the custom validator code. This is done to prevent any malicious code from being executed when the Pydantic model is created.

The list of blocked modules is as follows: `os`, `sys`, `importlib`, `pydoc`, `subprocess`, `pickle`, `shutil`, `tempfile`, `inspect`, `shlex`.

### Transpilation result

To visualize to result of the transpilation, let's consider the following schema manifest:

```yaml
version: 1
name: Person
description: A simple person schema
properties:
    name:
        type: str
        description: The name of the person
        validator?: |
            if len(value) < 3:
                raise ValueError("Name must be at least 3 characters long")
    age:
        type: int
        description: The age of the person
        validator?: |
            if value < 0:
                raise ValueError("Age must be a positive number")
    friends:
        type: list[str]
        description: The list of friends of the person
    address:
        description: The address of the person
        properties:
            street:
                type: str
                description: The street of the address
            city:
                type: str
                description: The city of the address
            zip_code:
                type: int
                description: The ZIP code of the address
```

The transpiled Pydantic model will look like this:

```python
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    zip_code: int

class Person(BaseModel):
    name: str
    age: int
    friends: list[str]
    address: Address

    def validate_name(value: str) -> str:
        if len(value) < 3:
            raise ValueError("Name must be at least 3 characters long")
        return value

    def validate_age(value: int) -> int:
        if value < 0:
            raise ValueError("Age must be a positive number")
        return value
```

This model becomes a part of available Pydantic models in the Phaistos validator, and you can use it to validate data against the schema.

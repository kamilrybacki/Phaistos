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
context?:
    <CONTEXT_KEY>: <CONTEXT_VALUE>
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
                    <NESTED_FIELD_VALIDATOR_CODE>
                default?: <NESTED_DEFAULT_VALUE>
        validator?: |
            <NESTED_MODEL_VALIDATOR_CODE>
```

### `validator` field

The `validator` field is optional and allows you to define custom validation functions for the data field. The code inside the `validator` field will be injected into the Pydantic model as a custom validator function.

The code inside the `validator` field must be a valid Python code snippet that includes a snippet that is to be executed before the `return` statement in the validator function.

The main rules are:

1. The code must be a valid Python code snippet.
2. Define it as a **multiline string** using the `|` character.
3. **DO NOT** use the `return` statement in the code snippet.

The **compiled** validator function will be composed of the following parts:

```python
def validate_<FIELD_NAME>(value: <FIELD_TYPE>) -> <FIELD_TYPE>:
    <LOGGER IMPORT AND GLOBALS SETUP>
    <VALIDATOR_CODE> # Injected code taken from the schema manifest
    <COLLECTION_VALIDATOR_CODE> # Injected code for list type
    return value
```

The `<LOGGER IMPORT AND GLOBALS SETUP>` snippet performs the following actions:

1. Imports the Phaistos validator logger and makes it available in the validator function.
2. Copies the value of the validated field into a global variable with
the name corresponding to the field name.

#### What does this mean for you?

**You can use the variable name** for the
validation code (so if the `FIELD_NAME` is `age`, you can use `age` in the validator) and **you can log messages** using the `logger` object.

An example of validator would be:

```yaml
name: age
validator: |
  logger.info('Checking if user is underage')
  if age < 18:
    raise ValueError("The age must be at least 18")
```

This is done **automagically** by the Phaistos transpiler, so you don't have to worry about the details of the Pydantic model generation.

##### What about the `value` variable?

What if you want to use the `value` variable in the validator code (as done
normally in Pydantic models)? You can do that by using the `value` variable in the validator code, as shown in the example below:

```yaml
name: age
validator: |
  logger.info('Checking if user is underage')
  if value < 18:
    raise ValueError("The age must be at least 18")
```

Where does it come in handy? Where you want to create a YAML anchor and reference it in multiple places, you can use the `value` variable to refer to the validated field.

```yaml
underscore_in_name: &underscore_in_name
  validator:
    mode: after
    source: |
      if value.startswith('_'):
        raise ValueError(f'{info.field_name} cannot start with underscore')

...  # other parts of the schema
properties:
  name:
    type: str
    description: Name of the database
    <<: *underscore_in_name
  surname:
    type: str
    description: Name of the table
    <<: *underscore_in_name
```

### Extra context

The `info` object is available in the validator code, [as provided by Pydantic](https://docs.pydantic.dev/latest/concepts/validators/#validation-context). It contains information about the field being validated, such as the field name, the field value, and the field type.

You can also pass additional context to the validator function by using the `context` field in the schema manifest. The context is a dictionary that contains additional information that you want to pass to the validator function.

```yaml
<FIELD_NAME>:
    type: <FIELD_TYPE>
    description: <FIELD_DESCRIPTION>
    validator?: |
        <VALIDATOR_CODE>
context:
    <CONTEXT_KEY>: <CONTEXT_VALUE>
```

Then, in the validator code, you can access the context values by using the `context` dictionary, as shown in the example below:

```yaml
...
    name: age
    validator: |
    logger.info('Checking if user is underage')
    min_age = context.get('min_age', 18)
    if age < min_age:
        raise ValueError(f"The age must be at least {min_age}")
context:
    min_age: 18
```

As You can see, the context is inherently global, so you can use it in any validator code in the schema manifest.

### Isolated modules

There are modules which are considered critical and are blocked from being imported in the custom validator code. This is done to prevent any malicious code from being executed when the Pydantic model is created.

The list of blocked modules is as follows: `os`, `sys`, `importlib`, `pydoc`, `subprocess`, `pickle`, `shutil`, `tempfile`, `inspect`, `shlex`.

Any `import` statements which try to redefine these modules in the validator
global will result in the schema transpilation error!

### Constraints

Phaisots allows you to define constraints for the data fields, in a similar way to how they are defined in Pydantic models. The constraints are defined as follows:

```yaml
<FIELD_NAME>:
    type: <FIELD_TYPE>
    description: <FIELD_DESCRIPTION>
    constraints:
        <CONSTRAINT_NAME>: <CONSTRAINT_VALUE>
```

The constraints are defined as key-value pairs, where the key is the name of the constraint and the value is the value of the constraint. These constraints are then injected into the Pydantic `FieldInfo` constructors for each transpiled field.

To define multiple constraints for a field, you can define them as separate key-value pairs, as shown in the example below:

```yaml
<FIELD_NAME>:
    type: <FIELD_TYPE>
    description: <FIELD_DESCRIPTION>
    constraints:
        <CONSTRAINT_NAME>: <CONSTRAINT_VALUE>
        <CONSTRAINT_NAME>: <CONSTRAINT_VALUE>
```

The constraints are then injected into the Pydantic model as follows:

```python
from pydantic import BaseModel, Field

class <SCHEMA_NAME>(BaseModel):
    <FIELD_NAME>: <FIELD_TYPE> = Field(..., **<CONSTRAINTS>)
```

To check the available constraints, refer to the [Pydantic documentation](https://docs.pydantic.dev/latest/concepts/fields/).

### What if I want both?

You can define both a `validator` and `constraints` for a field. The constraints will be injected into the Pydantic model as described above, and the `validator` code will be injected into the custom validator function.

```yaml
<FIELD_NAME>:
    type: <FIELD_TYPE>
    description: <FIELD_DESCRIPTION>
    constraints:
        <CONSTRAINT_NAME>: <CONSTRAINT_VALUE>
    validator: |
        <VALIDATOR_CODE>
```

### `default` field

The `default` field is optional and allows you to define a default value for the data field. The default value will be used if the field is not present in the data being validated.

### Model validators

You can define a model validator in the schema manifest, for entries that are
of the `dict` type i.e. any entries that represent a global or a nested schema.

The model validator is defined in the `validator` field of the schema manifest and is injected into the Pydantic model as a custom validator function,
**for a whole Pydantic model**.

The quality-of-life enhancements are the same as for the field validators, so you can use the `logger` object and the field names directly in the validator code.

So, for a nested model such as:

```yaml
name: Person
... # other parts of the schema
properties:
    occupation:
        description: The occupation of the person
        properties:
            title:
                type: str
                description: The title of the occupation
            salary:
                type: int
                description: The salary of the occupation
context:
    min_salary: 100000
    max_salary: 1000000
```

The `validator` field can look like this:

```yaml
        validator: |
            logging.info('Checking if the salary is in the correct range')
            if salary < min_salary:
                raise ValueError("The salary is too low")
            if salary > max_salary:
                raise ValueError("The salary is too high")
```

### Why both model and field validators?

The imposed order of validator execution is as follows:

1. Field validators are executed first.
2. Model validators are executed after all field validators have passed.

This means that you can use the field validators to check the individual fields and the model validator to check the relationships between the fields.

This is cool, if You want to check for example database connection data
for their syntax and then perform a connection check in the model validator.

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
            if len(name) < 3:
                raise ValueError("Name must be at least 3 characters long")
    age:
        type: int
        description: The age of the person
        validator?: |
            if age < 0:
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
        validator: |
            if len(street) < 3:
                raise ValueError("Street name must be at least 3 characters long")
            if len(city) < 3:
                raise ValueError("City name must be at least 3 characters long")
            if zip_code < 0:
                raise ValueError("ZIP code must be a positive number")
```

The transpiled Pydantic model will look like this:

```python
import pydantic

class Address(pydantic.BaseModel):
    street: str
    city: str
    zip_code: int

    @classmethod
    def validate_model(cls, data: dict[str, Any]):
        if len(data['street']) < 3:
            raise ValueError("Street name must be at least 3 characters long")
        if len(data['city']) < 3:
            raise ValueError("City name must be at least 3 characters long")
        if data['zip_code'] < 0:
            raise ValueError("ZIP code must be a positive number")


class Person(pydantic.BaseModel):
    name: str
    age: int
    friends: list[str]
    address: Address

    @classmethod
    def validate_name(cls, value: str, info: pydantic.ValidationInfo) -> str:
        if len(value) < 3:
            raise ValueError("Name must be at least 3 characters long")
        return value

    @classmethod
    def validate_age(cls, value: int, info: pydantic.ValidationInfo) -> int:
        if value < 0:
            raise ValueError("Age must be a positive number")
        return value
```

This model becomes a part of available Pydantic models in the Phaistos validator, and you can use it to validate data against the schema.

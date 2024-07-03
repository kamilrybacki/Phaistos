## Utilizing transpiled schemas

So, you have transpiled your schemas into Pydantic models. Now what? Well, you can use them to validate data against the defined schemas.

Suppose we have a schema defined in a file named `person.yaml`:

```yaml
person:
  name:
    type: str
    description: The name of the person
  age:
    type: int
    description: The age of the person
    validators: |
        if value < 18:
            raise ValueError("The age must be at least 18")
  email:
    type: str
    description: The email of the person
```

This YAML manifest defines a schema named `person` that has three fields: `name`, `age`, and `email`. The `age` field has a custom validator that checks if the age is at least 18.

Here is a simple example of how you can use the `Validator` object to validate data against the schema:

```python
from phaistos import Validator

# Initialize the Validator
validator = Validator.start()

# Validate data against the schema
data = {
    "name": "John Doe",
    "age": 30,
    "email": "joe@yahoo.com"
}

schema_name = "person"

# Validate the data against the schema
result = validator.against_schema(
    data=data,
    schema_name=schema_name
)
```

As You can see, the `Validator` object is to be instantiated using the `start` method, due to the fact that it is a **singleton** object. This means that you can only have one instance of the `Validator` object in your application.

`phaistos.validator.Validator.start`

::: phaistos.validator.Validator.start

Trying to directly instantiate the `Validator` object will raise an error:

```python
from phaistos import Validator

# This will raise an error
validator = Validator()
```

Below is the signature of the `against_schema` method:

`phaistos.validator.Validator.against_schema`

::: phaistos.validator.Validator.against_schema

## Validation result

After each validation, the `against_schema` method returns a `ValidationResult` object that contains the validation result.

`phaistos.typings.ValidationResult`

::: phaistos.typings.ValidationResult

You can access these attributes to get more information about the validation result:

```python
if result.is_valid:
    print("Data is valid!")
else:
    print("Data is invalid!")
    print("Errors:")
    for error in result.errors:
        print(error)
```

That's it! You have successfully validated data against a schema using the `Validator` object.

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
validator = Validator()

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

## Validation result

After each validation, the `against_schema` method returns a `ValidationResult` object that contains the validation result. The `ValidationResult` object has the following attributes:

- `is_valid`: A boolean that indicates if the data is valid against the schema.
- `errors`: A list of errors that occurred during the validation process. If the data is valid, this list will be empty.
- `schema`: The schema that was used for validation.
- `data`: The data that was validated against the schema.

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

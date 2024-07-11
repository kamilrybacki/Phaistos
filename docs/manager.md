## Utilizing transpiled schemas

So, you have transpiled your schemas into Pydantic models (found under the `PHAISTOS__SCHEMA_PATH` path).

Now what? Well, you can use them to validate data against the defined schemas.

Suppose we have a schema defined in a file named `person.yaml`:

```yaml
person:
  name:
    type: str
    description: The name of the person
  age:
    type: int
    description: The age of the person
    manager: |
        if age < 18:
            raise ValueError("The age must be at least 18")
  email:
    type: str
    description: The email of the person
```

This YAML manifest defines a schema named `person` that has three fields: `name`, `age`, and `email`. The `age` field has a custom manager that checks if the age is at least 18.

Here is a simple example of how you can use the `Manager` object to validate data against the schema:

```python
from phaistos import Manager

# Initialize the Manager
manager = Manager.start()

# Validate data against the schema
data = {
    "name": "John Doe",
    "age": 30,
    "email": "joe@yahoo.com"
}

schema_name = "person"

# Validate the data against the schema
result = manager.validate(
    data=data,
    schema=schema_name
)
```

As You can see, the `Manager` object is to be instantiated using the `start` method, due to the fact that it is a **singleton** object. This means that you can only have one instance of the `Manager` object in your application.

`phaistos.manager.Manager.start`

::: phaistos.manager.Manager.start

Trying to directly instantiate the `Manager` object will raise an error:

```python
from phaistos import Manager

# This will raise an error
manager = Manager()
```

Below is the signature of the `validate` method:

`phaistos.manager.Manager.validate`

::: phaistos.manager.Manager.validate

## Validation result

After each validation, the `validate` method returns a `ValidationResult` object that contains the validation result.

`phaistos.typings.ValidationResults`

::: phaistos.typings.ValidationResults

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

That's it! You have successfully validated data against a schema using the `Manager` object.

### Get the data model factory

If You need to get the Pydantic model for a schema, you can use the `get_factory` method:

```python
from phaistos import Manager

# Initialize the Manager
manager = Manager.start()

schema_name = "person"

# Get the Pydantic model for the schema
model = manager.get_factory(schema_name)
```

**phaistos.manager.Manager.get_factory**

::: phaistos.manager.Manager.get_factory

The `get_factory` method returns a factory object that can be used to create instances of the Pydantic model.

**phaistos.schema.SchemaInstancesFactory**

::: phaistos.schema.SchemaInstancesFactory

This model factory can be then used to create instances of the underlying data classes:

```python
data = {
    "name": "John Doe",
    "age": 30,
    "email": "xxx@yahoo.com"
}

# Create an instance of the Pydantic model using the factory
instance = model_factory.build(**data)
```

This approch is useful when the data is to be used in a more object-oriented way e.g. when creating entries to a database. As it can be seen, the `build` method is used to create an instance of the Pydantic model.

**phaistos.schema.SchemaInstancesFactory.build**

::: phaistos.schema.SchemaInstancesFactory.build

If the data is valid, the constructor of the Pydantic model will not raise any exceptions, and the instance will be created. If the data is invalid, the result will be `None` and the last encountered errors can be then accessed via the `errors` property of the model factory:

```python
factory = manager.get_factory(schema_name)

# Create an instance of the Pydantic model
instance = factory(**data)

if instance is None:
    print(factory.validation_errors)
```

It is worth noting that the `validate` method is also available on the model factory:

```python
data = {
    "name": "John Doe",
    "age": 30,
    "email": "xxx@gmail.com"
}

# Validate the data against the schema
result = model_factory.validate(data)
```

So, why the `validate` method is also included in the `Manager` itself?
It's just a syntactic sugar, as it retrieves the model factory and then calls the `validate` method on it for given data.

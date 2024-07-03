## Main workhorse - Transpiler

The main component of Phaistos is the transpiler, which is responsible for converting the YAML schema into a Pydantic model.

This object is used under-the-hood by the `Validator` class (to be described in a lil' bit) automatically, but there is nothing stopping You from using it
declaratively in Your code. The transpiler is devoid of state, so it can
be directly used in a functional manner.

Below, the main methods of the transpiler are described.

### Schema transpilation

This action is performed by `schema` method and is responsible for converting the YAML schema into a Pydantic model and returns it.

::: phaistos.transpiler.Transpiler.schema

## What are the main features of Phaistos?

**tl;dr**: Python reflections that spit out Pydantic models from YAML schemas.

The main goal of this project is to provide flexibility and utility in defining data models using YAML manifests, that include information about:

* **Data fields and their types**
* **Data field constraints** (in form of validators)
* **Data field descriptions**

These definitions are to be kept as easily versionable and maintainable files, which can be easily read and understood by both developers and non-developers alike.

### Main building blocks 🧱

The two main objects in Phaistos are: **Transpiler** and **Manager**.

The **Transpiler** is responsible for converting the schema manifest into a Pydantic model, which is a Python data validation library that allows you to define data schemas using Python type annotations.

This object is a **stateless** interface, meaning that it does not store any information about the schema, but rather acts as a "pure function" that takes the schema manifest as input and returns the Pydantic model as output.

**Manager** is a manager that automatically discovers and loads custom schemas from a specified directory, and then uses the **Transpiler** to convert them into Pydantic models. Then, it allows used to validate data against these models,
by passing the data to the Pydantic model and the name of the schema to validate against.

### General workflow 🌊

The diagram below illustrates the general workflow of the Phaistos transpiler:

```mermaid
%%{
  init: {
    'themeVariables': {
      'lineColor': '#fff',
      'textColor': '#fff'
    }
  }
}%%
flowchart TD
    A[Parsing schema for custom data types in YAML manifests] --> B[Transpiling properties into Pydantic Field objects]
    B --> C{{Field contains custom data validator?}}
    C -->|Yes| C1[Extract validator code from schema]
    C1 --> C2[Inject into default validator function before return statement]
    C2 --> C3[Shadow critical Python modules e.g. block os module]
    C3 --> C4[Compile validator function and return]
    C -->|No| D[Skip custom code injection]
    C4 --> E[For list-type fields: add validation for each element type]
    D --> E
    E --> F[For dict-type fields: transpile as nested schema]
    F --> |Recursion|B
    F --> G[Create Pydantic model using transpiled data for validation]

classDef blackAndWhite fill:none,stroke:#fff,stroke-width:2px,color:#fff,rx:5px,ry:5px,font-size:13px,font-family:Courier;
class A,B,C,C1,C2,C3,C4,D,E,F,G blackAndWhite;
linkStyle default stroke:#fff,stroke-width:2px;
```

Each of these steps will be described in more detail in the following sections.

### Okay, but why? 🤔

That a valid question, given the fact that there is, for example, a tool
that takes schemas defined in JSON and converts them into Pydantic models
called [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator).

The main reason that Phaistos was created is to provide a more flexible and
customizable way of defining data models, **especially** when it comes
to adding custom validators to data fields. For example, it is nearly impossible
to serialize (e.g. pickle) a Pydantic model that contains a custom validator
or any nested classes.

Using YAML manifests we can quickly share and version data models, and then
use Phaistos to convert them into Pydantic models on the fly. Also, there
are other benefits of using YAML, such as the ability to reuse repetetive
parts of the schema using YAML anchors and references.

So instead of trying to dance around serialization limitations of complex
classes in Python (which is a whole different can of worms), we can
quickly install Phaistos in the project and start using it to validate
data against the defined schemas - which can be leveraged in distributed ETL pipelines (e.g. within Apache Spark workers), APIs, configurations, and more.

#### Minor nitpicks 🤏 and quality-of-life boons

Below is the section that lists little annoyances that Phaistos tries to solve
or things that may be considered as quality-of-life improvements.

1. Normally, Pydantic will **not run** field validators for any attributes
that were used in the previously failed model validator. So, this is slightly
annoying if those two actions can be considered separately. Phaistos
solves this by running all field validators, regardless of the previous
validation results **and** model validator on its own.
2. Instead of referencing model fields in the custom validators by
abstract names, Phaistos allows you to reference them by their actual
names. So, in the custom validator, you can use `name` instead of `value`
for a field that is named ... `name`! This makes the code more readable
and maintainable.
3. You can use logging via the `logger` variable inside **all** custom
validators, which hooks up into the global validation logger. It is
included by default in the transpiled code.

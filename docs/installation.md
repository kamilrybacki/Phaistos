## Basic requirements

Phaistos was written with **Python 3.12** in mind.

Packages used internally, installed automatically as dependencies:

* `PyYAML==6.0.1`,
* `pydantic==2.7.0`.

## Installation via `pip`

To start using Phaistos, you can install it
from the package official repository on PyPI:

```bash
pip install phaistos
```

If You prefer to install from the source code, You can clone the repository
and install it using `pip`:

```bash
git clone https://github.com/kamilrybacki/Phaistos
cd Phaistos
pip install .
```

## Configuration

By default, Phaistos will look for schema files in the directory
pointed by the `PHAISTOS__SCHEMA_PATH` environment variable.

Schema discovery is recursive, so all files with the `.yaml` extension
in the specified directory and its subdirectories will be loaded.

The discovery is performed **during the first initialization** of `Validator`
class.

Want to disable the schema discovery?

Just define the `PHAISTOS__DISABLE_SCHEMA_DISCOVERY` environment variable
with any value. This will be accounted during the aforementioned initialization
and allow You to perform the schema loading manually.

To enable unsafe mode for validators i.e. to allow use of modules such as
`os`, `sys`, etc. in the custom validator code, set the `PHAISTOS__ENABLE_UNSAFE_VALIDATORS` environment variable to any value.

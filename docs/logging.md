## Few words about logging

There is a total of 4 logger included in the Phaistos package:

<!-- TRANSPILATION_LOGGER = phaistos.utils.setup_logger('PHAISTOS (T)')
MANAGER_LOGGER = phaistos.utils.setup_logger('PHAISTOS (M)')
COMPILATION_LOGGER = phaistos.utils.setup_logger('PHAISTOS (C)')
VALIDATION_LOGGER = phaistos.utils.setup_logger('PHAISTOS (V)') -->

1. **PHAISTOS (T)**: This logger is used by the `Transpiler` class to log messages related to the transpilation process.
2. **PHAISTOS (M)**: This logger is used by the `Manager` class to log messages related to the schema management.
3. **PHAISTOS (C)**: This logger is used by the `Compiler` class to log messages related to the compilation process.
4. **PHAISTOS (V)**: This logger is used by the `Manager` class to log messages related to the validation process i.e. things that happen **inside** custom validators.

The logging level for all the loggers is set to `INFO` by default.

Do You want to create a custom logger for Phaistos? You can do it by using the `phaistos.utils.setup_logger` function:

```python
from phaistos import utils

logger = utils.setup_logger('MyLogger', level='DEBUG')
```

This will create a logger named `MyLogger` with the logging level set to `DEBUG`. You can use this logger to log messages in your custom code.

**phaistos.utils.setup_logger**

::: phaistos.utils.setup_logger

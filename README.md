# Phaistos

<img
    src=".github/assets/phaistos.png"
    alt="Phaistos logo"
    height="300"
/>

Transcribing schemas from YAML-infused tablets to magical Pydantic validation models 🧙‍♂️🧙‍♀️

![Linting Status](https://github.com/kamilrybacki/Phaistos/actions/workflows/lint-code.yml/badge.svg)
![Testing Status](https://github.com/kamilrybacki/Phaistos/actions/workflows/code-tests.yml/badge.svg)

## Main Features

The main goal of this project is to provide flexibility and utility in defining data models using YAML manifests,
to enforce data validation of objects such as ETL pipeline payloads, API requests and responses, configurations and more.

These definitions are to be kept as easily versionable and maintainable files, which can be easily read and understood by
both developers and non-developers alike.

The main features of Phaistos are:

* Define data models using YAML manifests for easy readability, versioning and maintainability 🗄️
* Add custom validators to data fields that are automatically injected into Pydantic models 💉

**For installation and usage instructions, please refer to the [documentation](https://phaistos.readthedocs.io/en/latest/).**

### Why Phaistos? (as in - why the name?)

The Phaistos name comes from the [Phaistos Disc](https://en.wikipedia.org/wiki/Phaistos_Disc), a disk of fired clay from the Minoan palace of Phaistos on the island of Crete, possibly dating to the middle or late Minoan Bronze Age (2nd millennium BC). These discs contain a series of symbols that are still undeciphered to this day.

In the show of unprecedented far-reaching, the resulting data models from Phaistos can be viewed as such "discs" containing malleable and abstract data validation dialects that can exist in a variety of forms and can be used to validate a variety of data payloads. Also - we used to burn data into disks 💽, so there's another angle to the name. 🤷‍♂️

## Examples

The directory `examples/` contains scripts and schemas that demonstrate how to use Phaistos to define and validate data models. The examples are written in Python and are intended to be run from the command line.

More information about the examples can be found in the [examples README](examples/README.md).

## Contributing

Thank you for considering contributing to this project! We welcome contributions from everyone. By participating, you agree to abide by the following guidelines:

1. **Fork the Repository**: Start by forking the repository on GitHub.
2. **Clone Your Fork**: Clone your fork to your local machine.

    ```sh
    git clone https://github.com/your-username/your-fork.git
    ```

3. **Create a Branch**: Create a feature branch for your work.

    ```sh
    git checkout -b feature-branch
    ```

4. **Make Your Changes**: Make your changes and commit them with clear and descriptive commit messages.

    ```sh
    git commit -m "Description of your changes"
    ```

5. **Push to Your Fork**: Push your changes to your forked repository.

    ```sh
    git push origin feature-branch
    ```

6. **Submit a Pull Request**: Open a pull request on the original repository with a description of your changes. Please ensure your PR includes any relevant tests and follows the project’s coding conventions and guidelines.

### Issues and Bug Reports

If you encounter any issues or bugs, please [open an issue](https://github.com/your-repository/issues) on GitHub. Be sure to include detailed information about the problem and how to reproduce it.

## License

This project is licensed under the GNU General Public License Version 3 (GPLv3). See the [LICENSE](LICENSE) file for the full text.

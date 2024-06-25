# Phaistos 🐍📜

<img
    src=".github/assets/phaistos.png"
    alt="Phaistos logo"
    height="300"
/>

Transcribing schemas from YAML-infused tablets to magical Pydantic validation models 🧙‍♂️🧙‍♀️

# Main Features

The main goal of this project is to provide flexibility and utility in defining data models using YAML manifests,
to enforce data validation of objects such as ETL pipeline payloads, API requests and responses, configurations and more.

These definitions are to be kept as easily versionable and maintainable files, which can be easily read and understood by
both developers and non-developers alike.

The main features of Phaistos are:

* Define data models using YAML manifests for easy readability, versioning and maintainability 🗄️
* Add custom validators to data fields that are automatically injected into Pydantic models 💉
* Store transcribed models as pickled entities for easy import and use in your Python projects 📦

## Why Phaistos? (as in - why the name?)

The name Phaistos comes from the [Phaistos Disc](https://en.wikipedia.org/wiki/Phaistos_Disc), a disk of fired clay from the Minoan palace of Phaistos on the island of Crete, possibly dating to the middle or late Minoan Bronze Age (2nd millennium BC). These discs contain a series of symbols that are still undeciphered to this day.

In the show of unprecedented far-reaching, the resulting data models from Phaistos can be viewed as such "discs" containing malleable and abstract data validation dialects that can exist in a variety of forms and can be used to validate a variety of data payloads. Also - we used to burn data into disks 💽, so there's another angle to the name. 🤷‍♂️

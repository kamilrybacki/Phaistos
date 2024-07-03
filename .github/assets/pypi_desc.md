# Phaistos

The main goal of this project is to provide flexibility and utility in defining data models using YAML manifests,
to enforce data validation of objects such as ETL pipeline payloads, API requests and responses, configurations and more.

These definitions are to be kept as easily versionable and maintainable files, which can be easily read and understood by
both developers and non-developers alike.

The main features of Phaistos are:

* Define data models using YAML manifests for easy readability, versioning and maintainability
* Add custom validators to data fields that are automatically injected into Pydantic models

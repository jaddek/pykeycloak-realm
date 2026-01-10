
1. [Realm Builder pykeycloak](#pykeycloak-realm-builder)
   - [Special Note](#special-note)
   - [How it works](#how-it-works)
   - [Data directory](#data-directory)
   - [Install](#install)
   - [Dependencies](#dependencies)
   - [Commands](#commands)
   - [Configs](#configs)
   - [Docker](#docker)
   - [Tests](#tests)
2. [Methodology for Defining Realm Configurations](#methodology-for-defining-realm-configurations)
   - [Sections](#sections-envs-vars-realms)
   - [Envs](#envs)
   - [Vars](#vars)
   - [Realms](#realms)


# Pykeycloak Realm Builder

This library allows you to split the configuration and assemble a Keycloak realm configuration.

It is especially useful for local development, when you need a full Keycloak instance running on your local machine for testing, and later upload it to your local Keycloak instance, a containerized Keycloak, or your own Keycloak instance running on a server.

## Special Note

Keycloak validation is weird. When you upload a realm configuration file, you never get a detailed error explaining
what’s wrong. It just reports vague issues like duplicated resources or invalid JSON, even when the JSON file itself is
valid.

`otago.realm.yml` is provided as an example for future realms and **should not be used** in production.

## How it works

1. `./data/realms/templates/otago.realm.yml` - keycloak template

## Data directory

The default structure consists of two main directories for different purposes:

- `templates` - contains all realm configuration templates that need to be uploaded to Keycloak
- `exports` - contains all finalized realm JSON configurations

```markdown

data/
└── realms/
    ├── templates/
    │   └── otago.realm.yml # config as an example
    ├── export/
        └── otago.realm.json # real Keycloak config transformed from templates
```

## Install

```sh

make install
```

## Dependencies

- no specific dependencies

## Commands

**There are multiple options how to run the tool:**

### For shell environment

```sh

PYTHONPATH=src bin/realm_builder --from-realm otago --to-realm otago
```

### For UV

```sh

uv run python src/pykeycloak_realm/realm.py --from-realm=otago --to-realm=otago - will generate a new config
```

### Shortcuts using MAKE

```sh

#build and upload realm (alias for make docker-kc-export-realm-otago)
make otago
```

```sh

# generate new config
make docker-kc-build-realm-%
```

```sh

# generate and export config to Keycloak
make docker-kc-export-realm-%
```

## Configs

All configs here

```text
./src/pykeycloak_realm/config.py
```

You can manage them using system environment variables or .env files.

.env files are supported only via Makefiles (no dotenv dependencies are used); in other cases, they are intended as helper files for environment setup.

```text
.env        # All variables available for configuring
.env.kc     # Docker Keycloak
.env.local  # optional (for local usage)
```

## Docker

```sh

make help
make dup # up docker container with keycloak
make dd  # down docker container
...
```

## Tests

`make tests` - run tests

---

# Methodology for Defining Realm Configurations

## Sections: envs, vars, realms

To make the entire configuration manageable, it is important to separate the configuration into its components.

### envs

The `envs` section is defined at the global scope of the realm and contains clients along with their environment variables (IDs, secrets, etc.).

### vars

The `vars` section contains all configuration variables and presets based on them, which are duplicated or may be duplicated across the configuration.

### realms

The main configuration containing all parameters.

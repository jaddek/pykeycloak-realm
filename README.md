# Pykeycloak Realm Generator

## Install

```sh

make install
```

## Dependencies

- `poe` - as uv doesn't support custom scripts
- `PyYAML`

## Commands

**There are multiple options how to run the tool:**

### For shell environment

```sh

PYTHONPATH=src bin/realm_builder --from-realm otago --to-realm otago
```

### For UV + Poe environment
```sh

uv run poe rb --from-realm=otago --to-realm=otago - will generate a new config
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

You can manage them using system environment or .env files
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

# Pykeycloak Realm Generator

## Commands

**There are multiple options how to run the tool:**

### For shell environment
- PYTHONPATH=src bin/realm_builder --from-realm otago --to-realm otago


### For UV + Poe environment
- uv run poe rb --from-realm=otago --to-realm=otago - will generate a new config

### Shortcuts
- make otago - build and upload realm (alias for make docker-kc-export-realm-otago)
- make docker-kc-build-realm-% - generate new config
- make docker-kc-export-realm-% - generate and export config to Keycloak

## Configs

All configs here
```text
./src/pykeycloak_realm/config.py
```

You can manage them using system environment or .env files
```text
.env - config for tool
.env.kc - Docker Keycloak
.env.local - optional (for local usage)
```

## Docker

```text
make help - help
make dup - up docker container with keycloak
make dd - down docker container
```
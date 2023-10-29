# ...

```bash
poetry install
poetry run pysemu-cli


task help
task validate:fix validate

```

## Using docker devtools

```bash
make -C devtools -B
docker compose build


docker compose run --rm python-devtools task help
docker compose run --rm python-devtools task validate:fix validate

```

## Updating from template base

```bash
pipx run --spec=cruft cruft update
```

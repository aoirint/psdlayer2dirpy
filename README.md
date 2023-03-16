# psdlayer2dirpy

- GitHub: <https://github.com/aoirint/psdlayer2dirpy>
- PyPI: <https://pypi.org/project/aoirint-psdlayer2dirpy/>
- Docker Hub: <https://hub.docker.com/r/aoirint/psdlayer2dirpy>


## Usage

## Binary

Download from [Releases](https://github.com/aoirint/psdlayer2dirpy/releases).

```
./psdlayer2dir image.psd -o output/
```

### PyPI

```shell
pip3 install aoirint_psdlayer2dirpy

psdlayer2dir image.psd -o output/
```

### Docker

```shell
docker pull aoirint/psdlayer2dirpy

docker run --rm -v "$PWD:/work" -w /work aoirint/psdlayer2dirpy image.psd -o output/
```


## Development

This repository uses [Poetry](https://github.com/python-poetry/poetry).

### pyenv + Poetry

```shell
env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.10.10
pyenv local 3.10.10

poetry env remove python
poetry env use python
poetry install
```

### Format code

```shell
poetry run pysen run lint format
```

### Library management

```shell
# Add dependency
poetry add {package_name}
poetry add -G dev {package_name}

# Dump `requirements*.txt`
poetry export --without-hashes -o requirements.txt
poetry export --without-hashes --with dev -o requirements-dev.txt
```

### Docker

```shell
docker build -t psdlayer2dirpy .

docker run --rm -v "./work:/work" -w /work psdlayer2dirpy image.psd -o output/
```


## Dependencies

- psd-tools: [Docs](https://psd-tools.readthedocs.io/en/latest/) [GitHub](https://github.com/psd-tools/psd-tools) [PyPI](https://pypi.org/project/psd-tools/)

# psdlayer2dirpy

- GitHub: <https://github.com/aoirint/psdlayer2dirpy>
- PyPI: <https://pypi.org/project/aoirint-psdlayer2dirpy/>
- Docker Hub: <https://hub.docker.com/r/aoirint/psdlayer2dirpy>

## Installation

### PyPI

```shell
pip3 install aoirint_psdlayer2dirpy
```

### Docker

```shell
docker pull aoirint/psdlayer2dirpy:20220819.3
```

## Usage

### PyPI

```shell
psdlayer2dir file.psd -o output/
```

### Docker

```shell
docker run --rm -v "$PWD:/work" aoirint/psdlayer2dirpy:20220819.3 file.psd -o output/
```

## Dependencies

- psd-tools: [Docs](https://psd-tools.readthedocs.io/en/latest/) [GitHub](https://github.com/psd-tools/psd-tools) [PyPI](https://pypi.org/project/psd-tools/)


## Development

This repository uses [Poetry](https://github.com/python-poetry/poetry).

### pyenv + Poetry

```shell
env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.11.2
pyenv local 3.11.2

poetry env remove python
poetry env use python
poetry install
```

### Library management

To dump `requirements*.txt`,

```shell
poetry export --without-hashes -o requirements.txt
poetry export --without-hashes --with dev -o requirements-dev.txt
```

### Docker

```shell
docker build -t psdlayer2dirpy .

docker run --rm -v "./work:/work" -w /work psdlayer2dirpy image.psd -o output
```

# psdlayer2dirpy

## Installation

### PyPI

```shell
pip3 install aoirint_psdlayer2dirpy
```

### Docker

```shell
docker pull aoirint/psdlayer2dirpy:20220819.1
```

## Usage

### PyPI

```shell
psdlayer2dir file.psd -o output/
```



### Docker

```shell
docker run --rm -v "$PWD:/work" aoirint/psdlayer2dirpy:20220819.1 file.psd -o output/
```

## Dependencies

- psd-tools: [Docs](https://psd-tools.readthedocs.io/en/latest/) [GitHub](https://github.com/psd-tools/psd-tools)

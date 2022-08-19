import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List
from psd_tools import PSDImage
from psd_tools.api.layers import Layer

@dataclass
class LayerPath:
  layer: Layer
  path: List[str]

def _walk_layer_paths(layer_path: LayerPath) -> List[LayerPath]:
  layer_paths = []

  if layer_path.layer.is_group():
    for child_layer in layer_path.layer:
      layer_paths.extend(
        _walk_layer_paths(
          LayerPath(
            layer=child_layer,
            path=layer_path.path + [child_layer.name],
          )
        )
      )
  else:
    layer_paths.append(layer_path)

  return layer_paths

def walk_layer_paths(psd: PSDImage) -> List[LayerPath]:
  layer_paths = []

  for layer in psd:
      layer_paths.extend(
        _walk_layer_paths(
          LayerPath(
            layer=layer,
            path=[layer.name],
          )
        )
      )

  return layer_paths

def replace_unsafe_chars(layer_name: str) -> str:
  unsafe_chars = '<>:"/\\|!?*.'

  for char in unsafe_chars:
    layer_name = layer_name.replace(char, '_')

  return layer_name

def psdlayer2dir(
  psd_path: Path,
  output_path: Path,
):
  if output_path.exists():
    raise Exception(f'Already exists: {output_path}')

  psd = PSDImage.open(psd_path)

  layer_paths = walk_layer_paths(psd)
  for layer_path in layer_paths:
    filtered_path = list(map(replace_unsafe_chars, layer_path.path))
    filtered_path[-1] += '.png'

    relative_save_path = Path(*filtered_path)

    save_path = output_path / relative_save_path
    assert output_path in save_path.parents, f'Unsafe layer name used. Unsafe destination: {save_path}'
    save_path.parent.mkdir(parents=True, exist_ok=True)

    layer_path.layer.visible = True
    layer_path.layer.composite(viewport=psd.bbox).save(save_path)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('psd_file', type=str)
  parser.add_argument('-o', '--output', type=str, default='./')
  args = parser.parse_args()

  psd_path = Path(args.psd_file)
  output_path = Path(args.output)

  psdlayer2dir(
    psd_path=psd_path,
    output_path=output_path,
  )

if __name__ == '__main__':
  main()

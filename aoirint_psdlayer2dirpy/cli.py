import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

from . import __VERSION__ as VERSION

from psd_tools import PSDImage
from psd_tools.api.layers import Layer


@dataclass
class LayerPath:
    layer: Layer
    path: List[str]


def _walk_layer_paths(layer_path: LayerPath) -> List[LayerPath]:
    layer_paths = []

    layer_path.layer.visible = True
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


def replace_psdtool_chars(layer_name: str) -> str:
    """
    PSDToolの独自拡張機能の制御記号を置換する

    ファイルシステム用の置換のみだと手修正する数が多くなるための暫定処理

    https://oov.github.io/psdtool/manual.html#original-feature-asterisk
    """
    # ラジオボタン化
    if layer_name.startswith("*"):
        # layer_name = '(切替) ' + layer_name[1:]
        layer_name = layer_name[1:]

    # 強制表示化
    if layer_name.startswith("!"):
        # layer_name = '(強制) ' + layer_name[1:]
        layer_name = layer_name[1:]

    # 反転レイヤー指定
    # :flipx:flipy のような複数指定を許容
    while True:
        match = re.search(r"^(.+):flip(xy|x|y)$", layer_name)  # 後ろから

        if match:
            prefix = match.group(1)
            # xy = match.group(2)
            suffix = ""
            # if xy == 'xy':
            #   suffix += ' (上下左右反転)'
            # if xy == 'x':
            #   suffix += ' (左右反転)'
            # if xy == 'y':
            #   suffix += ' (上下反転)'

            layer_name = f"{prefix}{suffix}"
        else:
            break

    return layer_name


def replace_unsafe_chars(layer_name: str) -> str:
    """
    ファイルシステムの都合で使えない文字を置換する
    """
    unsafe_chars = '<>:"/\\|!?*.'

    for char in unsafe_chars:
        layer_name = layer_name.replace(char, "_")

    return layer_name


def psdlayer2dir(
    psd_path: Path,
    output_path: Path,
) -> None:
    if output_path.exists():
        raise Exception(f"Already exists: {output_path}")

    psd = PSDImage.open(psd_path)

    layer_paths = walk_layer_paths(psd)
    for layer_path in layer_paths:
        filtered_path = list(
            map(replace_unsafe_chars, map(replace_psdtool_chars, layer_path.path))
        )
        filtered_path[-1] += ".png"

        relative_save_path = Path(*filtered_path)

        save_path = output_path / relative_save_path
        assert (
            output_path in save_path.parents
        ), f"Unsafe layer name used. Unsafe destination: {save_path}"
        save_path.parent.mkdir(parents=True, exist_ok=True)

        layer_path.layer.visible = True
        layer_path.layer.composite(viewport=psd.bbox).save(save_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("psd_file", type=str)
    parser.add_argument("-o", "--output", type=str, default="./")
    parser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
    args = parser.parse_args()

    psd_path = Path(args.psd_file)
    output_path = Path(args.output)

    psdlayer2dir(
        psd_path=psd_path,
        output_path=output_path,
    )

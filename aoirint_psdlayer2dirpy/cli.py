import argparse
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from PIL import Image
from psd_tools import PSDImage
from psd_tools.api.layers import Layer

from . import __VERSION__ as VERSION
from .util.logging_utility import setup_logger

logger = logging.Logger("psdlayer2dir")


@dataclass
class PsdLeafLayer:
    layer: Layer
    path: List[str]


def _find_all_leaf_layers(
    layer: Layer,
    path: List[str],
) -> List[PsdLeafLayer]:
    layer_paths = []

    layer.visible = True
    if layer.is_group():
        for child_layer in layer:
            layer_paths.extend(
                _find_all_leaf_layers(
                    layer=child_layer,
                    path=path + [child_layer.name],
                )
            )
    else:
        layer_paths.append(
            PsdLeafLayer(
                layer=layer,
                path=path,
            )
        )

    return layer_paths


def find_all_leaf_layers(
    psd: PSDImage,
) -> List[PsdLeafLayer]:
    layer_paths = []

    for layer in psd:
        layer_paths.extend(
            _find_all_leaf_layers(
                layer=layer,
                path=[layer.name],
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
    if layer_name.endswith(":flipx"):
        # layer_name = '(左右反転) ' + layer_name[:-6]
        layer_name = layer_name[:-6]

    if layer_name.endswith(":flipy"):
        # layer_name = '(上下反転) ' + layer_name[:-6]
        layer_name = layer_name[:-6]

    if layer_name.endswith(":flipxy"):
        # layer_name = '(上下左右反転) ' + layer_name[:-7]
        layer_name = layer_name[:-7]

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
    output_dir: Path,
    flipx: bool,
    flipy: bool,
) -> None:
    if output_dir.exists():
        raise Exception(f"Already exists: {output_dir}")

    psd = PSDImage.open(psd_path)
    leaf_layer_list = find_all_leaf_layers(psd)
    logger.info(f"{len(leaf_layer_list)} layers found")

    for leaf_layer in leaf_layer_list:
        slashed_layer_name = "/".join(leaf_layer.path)

        filtered_path = list(
            map(replace_unsafe_chars, map(replace_psdtool_chars, leaf_layer.path))
        )
        filtered_path[-1] += ".png"

        relative_save_path = Path(*filtered_path)

        logger.info(f'Saving layer "{slashed_layer_name}" -> {relative_save_path}')

        save_path = output_dir / relative_save_path
        assert (
            output_dir in save_path.parents
        ), f"Unsafe layer name used. Unsafe destination: {save_path}"
        save_path.parent.mkdir(parents=True, exist_ok=True)

        leaf_layer.layer.visible = True

        pil_image = leaf_layer.layer.composite(viewport=psd.bbox)
        assert (
            pil_image is not Image
        ), f"Runtime type of composited layer image is not PIL.Image. This is unexpected."

        if flipx:
            pil_image = pil_image.mirror()

        if flipy:
            pil_image = pil_image.flip()

        pil_image.save(save_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "psd_file",
        type=Path,
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        type=Path,
        default=os.environ.get("PSDLAYER2DIR_OUTPUT_DIR", "./"),
    )
    parser.add_argument(
        "--flipx",
        type="store_true",
    )
    parser.add_argument(
        "--flipy",
        type="store_true",
    )
    parser.add_argument(
        "--flipxy",
        type="store_true",
    )
    parser.add_argument(
        "--log_level",
        type=int,
        default=os.environ.get("PSDLAYER2DIR_LOG_LEVEL", logging.INFO),
    )
    parser.add_argument(
        "--log_file",
        type=str,
        default=os.environ.get("PSDLAYER2DIR_LOG_FILE"),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )
    args = parser.parse_args()
    log_level: int = args.log_level
    log_file: str | None = args.log_file

    logging.basicConfig(level=log_level)
    setup_logger(logger=logger, log_level=log_level, log_file=log_file)

    psd_path: Path = args.psd_file
    output_dir: Path = args.output_dir
    flipx: bool = args.flipx
    flipy: bool = args.flipy
    flipxy: bool = args.flipxy

    psdlayer2dir(
        psd_path=psd_path,
        output_dir=output_dir,
        flipx=flipx or flipxy,
        flipy=flipy or flipxy,
    )

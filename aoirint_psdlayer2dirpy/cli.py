import argparse
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List

from PIL import Image
from psd_tools import PSDImage
from psd_tools.api.layers import Layer

from . import __VERSION__ as VERSION
from .util.iterable_utility import flatten, flatten_with_parent
from .util.logging_utility import setup_logger

logger = logging.Logger("psdlayer2dir")


@dataclass
class PsdLeafLayer:
    layer: Layer
    path: List[str]

    original_layer_name: str
    """ オリジナルのレイヤー名 """

    save_layer_name: str
    """ ファイルに保存するときのレイヤー名 """


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


class PsdParser(ABC):
    @abstractmethod
    def count_leaf_layers(self) -> int:
        ...

    @abstractmethod
    def save_layers(self, flipx: bool, flipy: bool,) -> None:
        ...


class PsdParserPsdTool(PsdParser):
    psd: PSDImage
    bbox: tuple[int, int, int, int]
    root_layers: list[Layer]

    flatten_layers: list[Layer]
    flatten_leaf_layers: list[Layer]

    noflip_flatten_leaf_layers: list[Layer]
    flipx_flatten_leaf_layers: list[Layer]
    flipy_flatten_leaf_layers: list[Layer]
    flipxy_flatten_leaf_layers: list[Layer]

    def __init__(
        self,
        psd: PSDImage,
    ):
        self.psd = psd
        self.bbox = psd.bbox
        self.root_layers = list(psd)

        def _find_all_layer(layer: Layer, flipx: bool, flipy: bool):
            child_layers = list(layer)
            child_layer_name_list = [child_layer.name for child_layer in child_layers]

            for child_layer in child_layers:
                child_layer_name = child_layer.name

                if child_layer_name.endswith(':flipxy'):
                    if flipx and flipy:
                        yield child_layer
                elif child_layer_name.endswith(':flipx'):
                    if flipx:
                        yield child_layer
                elif child_layer_name.endswith(':flipy'):
                    if flipy:
                        yield child_layer

        self.flatten_layers = list(flatten_with_parent(psd))
        self.flatten_leaf_layers = list(flatten(psd))

        noflip_flatten_leaf_layers: list[Layer] = []
        flipx_flatten_leaf_layers: list[Layer] = []
        flipy_flatten_leaf_layers: list[Layer] = []
        flipxy_flatten_leaf_layers: list[Layer] = []

        def any_parent_layer_name_endswith(layer: Layer, word: str) -> bool:
            _parent = layer.parent
            while _parent is not None:
                _parent_layer_name = _parent.name
                if _parent_layer_name.endswith(word):
                    return True
            return False

        for leaf_layer in self.flatten_leaf_layers:
            layer_name: str = leaf_layer.name

            is_flipx = layer_name.endswith(':flipx')
            any_parent_layer_flipx = any_parent_layer_name_endswith(leaf_layer, ':flipx')
            if is_flipx and any_parent_layer_flipx:
                pass

            is_flipy = layer_name.endswith(':flipy')
            any_parent_layer_flipy = any_parent_layer_name_endswith(leaf_layer, ':flipy')
            if is_flipy and any_parent_layer_flipy:
                pass

            is_flipxy = layer_name.endswith(':flipxy')
            any_parent_layer_flipxy = any_parent_layer_name_endswith(leaf_layer, ':flipxy')
            if is_flipxy and any_parent_layer_flipxy:
                pass


        self.layer_dict = layer_dict


    def count_leaf_layers(self) -> int:
        return len(self.flatten_leaf_layers)


    def save_layers(self, flipx: bool, flipy: bool,) -> None:
        pass


def psdlayer2dir(
    psd_path: Path,
    output_dir: Path,
    flipx: bool,
    flipy: bool,
) -> None:
    if output_dir.exists():
        raise Exception(f"Already exists: {output_dir}")

    psd = PSDImage.open(psd_path)
    psd_parser = PsdParserPsdTool(psd=psd)

    layer_count = psd_parser.count_leaf_layers(psd)
    logger.info(f"{layer_count} layers found")

    leaf_layer_list = find_all_leaf_layers(psd)

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
        action="store_true",
    )
    parser.add_argument(
        "--flipy",
        action="store_true",
    )
    parser.add_argument(
        "--flipxy",
        action="store_true",
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

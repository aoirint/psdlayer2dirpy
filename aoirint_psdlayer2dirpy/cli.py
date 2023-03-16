import argparse
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from psd_tools import PSDImage
from psd_tools.api.layers import Layer

from . import __VERSION__ as VERSION
from .util.logging_utility import setup_logger

logger = logging.Logger("psdlayer2dir")


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


def replace_unsafe_chars(layer_name: str) -> str:
    unsafe_chars = '<>:"/\\|!?*.'

    for char in unsafe_chars:
        layer_name = layer_name.replace(char, "_")

    return layer_name


def psdlayer2dir(
    psd_path: Path,
    output_dir: Path,
) -> None:
    if output_dir.exists():
        raise Exception(f"Already exists: {output_dir}")

    psd = PSDImage.open(psd_path)

    layer_path_list = walk_layer_paths(psd)
    logger.info(f"{len(layer_path_list)} layers found")

    for layer_path in layer_path_list:
        slashed_layer_name = "/".join(layer_path.path)

        filtered_path = list(map(replace_unsafe_chars, layer_path.path))
        filtered_path[-1] += ".png"

        relative_save_path = Path(*filtered_path)

        logger.info(f'Saving layer "{slashed_layer_name}" -> {relative_save_path}')

        save_path = output_dir / relative_save_path
        assert (
            output_dir in save_path.parents
        ), f"Unsafe layer name used. Unsafe destination: {save_path}"
        save_path.parent.mkdir(parents=True, exist_ok=True)

        layer_path.layer.visible = True
        layer_path.layer.composite(viewport=psd.bbox).save(save_path)


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

    psdlayer2dir(
        psd_path=psd_path,
        output_dir=output_dir,
    )

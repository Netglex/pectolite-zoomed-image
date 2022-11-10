#!/usr/bin/env python3

import cairo
import enum
import glob
import json
import logging
import os
import sys


# region constants
CONV_FACTOR = 100.0


# endregion


# region classes
class Placement(enum.Enum):
    North = 0
    East = 1
    South = 2
    West = 3


class FitImage(enum.Enum):
    Horizontal = 0
    Vertical = 1


class PathSettings:
    def __init__(self, data):
        self.paths: list[str] = data["paths"]
        self.output_folder: str = data["outputFolder"]


class SubregionSettings:
    def __init__(self, data):
        self.placements: list[Placement] = [
            Placement[placements] for placements in data["placements"]
        ]
        self.main_sizes: list[float] = data["mainSizes"]
        self.cross_size_weigths: list[list[float]] = data["crossSizeWeights"]
        self.centers: list[list[list[float]]] = data["centers"]
        self.zoom_factors: list[list[float]] = data["zoomFactors"]
        self.line_widths: list[list[float]] = data["lineWidths"]
        self.colors: list[list[list[int]]] = data["colors"]


class DrawingSettings:
    def __init__(self, data):
        self.fit_images: list[FitImage] = [
            FitImage[fit_images] for fit_images in data["fitImages"]
        ]
        self.paddings: list[float] = data["paddings"]


class Config:
    def __init__(self, data):
        self.path_settings = PathSettings(data["pathSettings"])
        self.subregion_settings = SubregionSettings(data["subregionSettings"])
        self.drawing_settings = DrawingSettings(data["drawingSettings"])


class Rect:
    def __init__(self, x, y, width, height):
        self.x: float = x
        self.y: float = y
        self.width: float = width
        self.height: float = height

    def __mul__(self, other):
        return Rect(
            self.x * other, self.y * other, self.width * other, self.height * other
        )


# endregion


# region functions
def setup_logger():
    logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.INFO)
    logging.info("Setup logger.")


def read_configs() -> list[Config]:
    logging.info("Read config.")

    paths = ["./config.json"]
    if len(sys.argv) > 1:
        paths = sys.argv[1:]

    configs = []
    for path in paths:
        path = os.path.abspath(path)

        file = open(path)
        data = json.load(file)
        file.close()

        for single_data in data:
            configs.append(Config(single_data))

    return configs


def expand_list(expand_to: int, list: list) -> list:
    for i in range(expand_to - len(list)):
        list.append(list[i])
    return list


def normalize_configs(configs: list[Config]) -> list[Config]:
    logging.info("Normalizing config.")

    for config in configs:
        paths = []
        for path in config.path_settings.paths:
            paths += glob.glob(path, recursive=True)
        config.path_settings.paths = [os.path.abspath(path) for path in paths]
        config.path_settings.output_folder = os.path.abspath(
            config.path_settings.output_folder
        )

        expand_to = len(config.path_settings.paths)
        config.subregion_settings.placements = expand_list(
            expand_to, config.subregion_settings.placements
        )
        config.subregion_settings.main_sizes = expand_list(
            expand_to, config.subregion_settings.main_sizes
        )
        config.subregion_settings.cross_size_weigths = expand_list(
            expand_to, config.subregion_settings.cross_size_weigths
        )
        config.subregion_settings.centers = expand_list(
            expand_to, config.subregion_settings.centers
        )
        config.subregion_settings.zoom_factors = expand_list(
            expand_to, config.subregion_settings.zoom_factors
        )
        config.subregion_settings.line_widths = expand_list(
            expand_to, config.subregion_settings.line_widths
        )
        config.subregion_settings.colors = expand_list(
            expand_to, config.subregion_settings.colors
        )
        config.drawing_settings.fit_images = expand_list(
            expand_to, config.drawing_settings.fit_images
        )
        config.drawing_settings.paddings = expand_list(
            expand_to, config.drawing_settings.paddings
        )

        for i, _ in enumerate(config.path_settings.paths):
            expand_to = max(
                len(config.subregion_settings.cross_size_weigths[i]),
                len(config.subregion_settings.centers[i]),
                len(config.subregion_settings.zoom_factors[i]),
                len(config.subregion_settings.line_widths[i]),
                len(config.subregion_settings.colors[i]),
            )
            config.subregion_settings.cross_size_weigths[i] = expand_list(
                expand_to, config.subregion_settings.cross_size_weigths[i]
            )
            config.subregion_settings.centers[i] = expand_list(
                expand_to, config.subregion_settings.centers[i]
            )
            config.subregion_settings.zoom_factors[i] = expand_list(
                expand_to, config.subregion_settings.zoom_factors[i]
            )
            config.subregion_settings.line_widths[i] = expand_list(
                expand_to, config.subregion_settings.line_widths[i]
            )
            config.subregion_settings.colors[i] = expand_list(
                expand_to, config.subregion_settings.colors[i]
            )

    return configs


def calculate_image_rects(config: Config) -> list[Rect]:
    logging.info("  Calculate rectangle for image.")
    image_rects = []
    for i, path in enumerate(config.path_settings.paths):
        fit_image = config.drawing_settings.fit_images[i]

        with cairo.ImageSurface.create_from_png(path) as surface:
            width = surface.get_width()
            height = surface.get_height()

        width_rect = 1.0
        height_rect = 1.0

        if fit_image == FitImage.Horizontal:
            height_rect *= height / width
        elif fit_image == FitImage.Vertical:
            width_rect *= width / height
        image_rects.append(Rect(0.0, 0.0, width_rect, height_rect))

    return image_rects


def calculate_zoomed_subregion_rects(
    config: Config, image_rects: list[Rect]
) -> list[list[Rect]]:
    logging.info("  Calculate rectangle for zoomed subregions.")
    zoomed_subregion_rects = []
    for i, main_size in enumerate(config.subregion_settings.main_sizes):
        image_rect = image_rects[i]
        placement = config.subregion_settings.placements[i]
        cross_size_weight = config.subregion_settings.cross_size_weigths[i]
        padding = config.drawing_settings.paddings[i]
        cross_size_weight_sum = sum(cross_size_weight)
        zoomed_subregion_rect = []
        placement_pos = [0.0, 0.0]
        rect_width = 0.0
        rect_height = 0.0

        if placement == Placement.North:
            placement_pos[1] = -main_size - padding
            rect_height = main_size
        elif placement == Placement.East:
            placement_pos[0] = image_rect.width + padding
            rect_width = main_size
        elif placement == Placement.South:
            placement_pos[1] = image_rect.height + padding
            rect_height = main_size
        elif placement == Placement.West:
            placement_pos[0] = -main_size - padding
            rect_width = main_size

        for cross_subsize_weight in cross_size_weight:
            cross_subsize = cross_subsize_weight / cross_size_weight_sum
            total_padding = padding * (len(cross_size_weight) - 1)

            if placement == Placement.North or placement == Placement.South:
                rect_width = cross_subsize * (image_rect.width - total_padding)
            elif placement == Placement.East or placement == Placement.West:
                rect_height = cross_subsize * (image_rect.height - total_padding)

            zoomed_subregion_rect.append(
                Rect(placement_pos[0], placement_pos[1], rect_width, rect_height)
            )

            if placement == Placement.North or placement == Placement.South:
                placement_pos[0] = rect_width + padding
            elif placement == Placement.East or placement == Placement.West:
                placement_pos[1] = rect_height + padding

        zoomed_subregion_rects.append(zoomed_subregion_rect)

    return zoomed_subregion_rects


def calculate_subregion_rects(
    config: Config, image_rects: list[Rect], zoomed_subregion_rects: list[list[Rect]]
):
    logging.info("  Calculate rectangle for subregions.")
    subregion_rects = []
    for i, _ in enumerate(config.subregion_settings.centers):
        subregion_rect = []

        for j, subcenter in enumerate(config.subregion_settings.centers[i]):
            image_rect = image_rects[i]
            zoomed_subregion_rect = zoomed_subregion_rects[i][j]
            zoom_factor = config.subregion_settings.zoom_factors[i][j]

            rect_width = zoomed_subregion_rect.width / zoom_factor
            rect_height = zoomed_subregion_rect.height / zoom_factor
            placement_pos = [
                subcenter[0] * image_rect.width - rect_width / 2,
                subcenter[1] * image_rect.height - rect_height / 2,
            ]

            subregion_rect.append(
                Rect(placement_pos[0], placement_pos[1], rect_width, rect_height)
            )

        subregion_rects.append(subregion_rect)

    return subregion_rects


def draw_image(
    context: cairo.Context,
    path: str,
    image_rect: Rect,
    source_rect: Rect,
    target_rect: Rect,
):
    logging.info("    Draw image.")

    # Crop image
    original_img_surface = cairo.ImageSurface.create_from_png(path)

    original_img_width = original_img_surface.get_width()
    original_img_height = original_img_surface.get_height()
    img_width = int(original_img_width * source_rect.width / image_rect.width)
    img_height = int(original_img_height * source_rect.height / image_rect.height)

    img_surface = cairo.ImageSurface(cairo.Format.ARGB32, img_width, img_height)
    img_context = cairo.Context(img_surface)
    img_context.set_source_surface(
        original_img_surface,
        -original_img_width * source_rect.x / image_rect.width,
        -original_img_width * source_rect.y / image_rect.width,
    )
    img_context.paint()

    # Paint image in drawing
    conv_rect = target_rect * CONV_FACTOR

    context.save()
    context.translate(conv_rect.x, conv_rect.y)
    context.scale(
        conv_rect.width / img_width,
        conv_rect.height / img_height,
    )
    context.set_source_surface(img_surface)
    context.paint()
    context.restore()
    pass


def draw_rect(context: cairo.Context, rect: Rect, line_width: float, color: list[int]):
    logging.info("    Draw rectangle.")
    conv_rect = rect * CONV_FACTOR

    context.save()
    context.set_line_width(line_width)
    context.set_source_rgb(color[0] / 255, color[1] / 255, color[2] / 255)

    context.move_to(conv_rect.x, conv_rect.y)
    context.line_to(conv_rect.x, conv_rect.y + conv_rect.height)
    context.line_to(conv_rect.x + conv_rect.width, conv_rect.y + conv_rect.height)
    context.line_to(conv_rect.x + conv_rect.width, conv_rect.y)
    context.line_to(conv_rect.x, conv_rect.y)
    context.close_path()
    context.stroke()
    context.restore()


def create_drawing(
    config: Config, index: int, image_rect: Rect
) -> tuple[cairo.SVGSurface, cairo.Context]:
    logging.info("    Create drawing.")
    path = config.path_settings.paths[index]
    main_size = config.subregion_settings.main_sizes[index]
    placement = config.subregion_settings.placements[index]
    padding = config.drawing_settings.paddings[index]

    file_name = ".".join(os.path.basename(path).split(".")[:-1])
    output_path = os.path.abspath(
        f"{config.path_settings.output_folder}/{file_name}.svg"
    )
    if not os.path.exists(config.path_settings.output_folder):
        os.makedirs(config.path_settings.output_folder)

    viewport_rect = Rect(
        -padding,
        -padding,
        image_rect.width + padding * 2,
        image_rect.height + padding * 2,
    )
    if placement == Placement.North:
        viewport_rect.y -= main_size + padding
        viewport_rect.height += main_size + padding
    elif placement == Placement.East:
        viewport_rect.width += main_size + padding
    elif placement == Placement.South:
        viewport_rect.height += main_size + padding
    elif placement == Placement.West:
        viewport_rect.x -= main_size + padding
        viewport_rect.width += main_size + padding

    viewport_rect = viewport_rect * CONV_FACTOR

    surface = cairo.SVGSurface(output_path, viewport_rect.width, viewport_rect.height)
    context = cairo.Context(surface)
    context.translate(-viewport_rect.x, -viewport_rect.y)
    return surface, context


def finish_drawing(surface: cairo.SVGSurface):
    logging.info("    Flush image.")
    context = cairo.Context(surface)
    context.translate(-50, -50)
    surface.finish()
    surface.flush()


# endregion


def main():
    setup_logger()
    configs = read_configs()
    configs = normalize_configs(configs)

    for i, config in enumerate(configs):
        logging.info(f"Start with configuration {i + 1}.")

        image_rects = calculate_image_rects(config)
        zoomed_subregion_rects = calculate_zoomed_subregion_rects(config, image_rects)
        subregion_rects = calculate_subregion_rects(
            config, image_rects, zoomed_subregion_rects
        )

        for j, path in enumerate(config.path_settings.paths):
            logging.info(f"  Start with drawing {j + 1} of configuration {i + 1}.")
            image_rect = image_rects[j]

            surface, context = create_drawing(config, j, image_rect)
            draw_image(context, path, image_rect, image_rect, image_rect)

            for k, subregion_rect in enumerate(subregion_rects[j]):
                zoomed_subregion_rect = zoomed_subregion_rects[j][k]
                subregion_rect = subregion_rects[j][k]
                line_width = config.subregion_settings.line_widths[j]
                color = config.subregion_settings.colors[j][k]

                draw_image(
                    context, path, image_rect, subregion_rect, zoomed_subregion_rect
                )
                draw_rect(context, zoomed_subregion_rect, line_width[0], color)

                draw_rect(context, subregion_rect, line_width[1], color)

            finish_drawing(surface)
            logging.info(f"  Finish with drawing {j + 1} of configuration {i + 1}.")

        logging.info(f"Finish with configuration {i + 1}.")


if __name__ == "__main__":
    main()

# :framed_picture: Zoomed Areas of Images to SVG

## :scroll: Introduction

This repository contains a Python script to create a specific kind of figure. This script can be used to zoom into specified areas of an image. The zoomed areas will be displayed next to the image. The whole figure will be exported as an SVG file.

Here are some examples which can be made with this script:

![CityExample0](readmeImages/CityExample0.svg)
![CityExample1](readmeImages/CityExample1.svg)  
![FaceExample0](readmeImages/FaceExample0.svg)
![FaceExample1](readmeImages/FaceExample1.svg)


### Requirements

In order to run the script, it is **required to install** the necessary packages with `pip`:

```
pip install -r requirements.txt
```

### Quick Start

There are already images in the folder *./exampleInput* and a configuration file *./config.json* available. These can be used for a quick test run by running the command:

```
py zoomed-image.py
```

> :warning: Only **PNG images** can be currently used with this script.

## :gear: Configuration

There are various settings which can be configured with a JSON file. The file *./config.json* is an example how the structure of the JSON data should look like.

The overall structure of the JSON file is an array consisting of `Config` objects. Each config object must contain three subsettings which will be explained in the following subchapters.

### `pathSettings`

- `paths`: Absolute or relative path to the images. Wildcards like `*` or `**` can be used as well.

  > :information_source: Almost all settings can be indivdually adjusted for each image. This is why these settings are inside nested arrays. If there are less settings available than images, the settings will be automatically extended in a repeating fashion.

- `outputFolder`: Folder which will contain the created SVG files. The folder will be created automatically if it does not exist.

  > :warning: Newly created SVG files will override existing ones.

### `subregionSettings`

- `placements`: Determines where the zoomed areas relative to the image are displayed. Following values are allowed:

  | Keyword | Placement of zoomed areas |
  | ------- | ------------------------- |
  | `North` | Above image               |
  | `East`  | Right of image            |
  | `South` | Below image               |
  | `West`  | Left of image             |

- `mainSizes`: Determines how broad the stripe of the zoomed areas is. The unit is determined by the property `fitImages` in the subsettings `drawSettings`.
- `visibilities`: Determines if a zoomed area should be drawn or not.
- `crossSizeWeights`: Ratio of the width of the zoomed areas.
- `centers`: Determines the center of all areas in the image which will be zoomed. The image size defines the unit size for this property.
- `zoomFactors`: Determines the zoom factor for each area in the image.
- `lineWidths`: Contains two values for an image. The first value is the line width of the border of the zoomed areas on the side. The second value is the line width of the border of the areas inside the image.
- `colors`: Contains the color for each zoomed area of an image. The values are given as three integer values ranging from 0 to 255 in an array.

### `drawingSettings`

- `fitImages`: Fits an image along a specified axis. This also **specifices the unit length**. The image will be scaled accordingly along the other axis.

  | Keyword      | Image fitting                               |
  | ------------ | ------------------------------------------- |
  | `Horizontal` | Image scaled such that width has length 1.  |
  | `Vertical`   | Image scaled such that height has length 1. |

- `paddings`: Padding around the created figure and between images and zoomed areas. The unit is determined by the property `fitImages`.

## :keyboard: Running the Script

The script can be run just as described in the introduction. The script will automatically look for a *config.json* file in that case. It is also possible to run the script with a different or multiple configuration files:
```
py zoomed-image.py config0.json config1.json
```

The paths can be absolute or relative.

## :dart: Afterwords

A close person of mine needed this kind of figures for a scientific paper. As I had some time on hand, I wanted to create this repository so that this person and other researchers can profit from it and have beautiful visualizations. I really hope that it simplifies some of their workflow.

By the way, the people from the examples are not real. There is a great tool to generate nonexistent people: https://thispersondoesnotexist.com/. Amazing stuff :grin:

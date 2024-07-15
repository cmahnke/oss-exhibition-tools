OSS Exhibition tools
====================

# Image2Model

Creates a 3D Model from an PDF file

## Building

```
docker build -f docker/image2model/Dockerfile .
```

## Usage

Print help
```
docker run -it -v `pwd`:`pwd` ghcr.io/cmahnke/oss-exhibition-tools/image2model:latest --help
```

Available options:

```
usage: generate-models.py [-h] (-i [file] | -d [directory] | -s) [-o [directory]] [-z] [-t] [-k] [-p PATTERN]

Generate Collada files from images

options:
  -h, --help            show this help message and exit
  -i [file], --input [file]
                        File to convert
  -d [directory], --directory [directory]
                        Path to collect images from
  -s, --setup           Ensure all required modules are present
  -o [directory], --output [directory]
                        Path to write converted files to
  -z, --zip             Compress results to zip file
  -t, --thumbs          Use thumbnails as textures
  -k, --keep            Keep generated files
  -p PATTERN, --pattern PATTERN
                        File pattern for directories, default is '**/*.jpg,**/*.pdf'
```

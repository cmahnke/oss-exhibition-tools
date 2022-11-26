#!/usr/bin/env python

# TODO:
# * Handle PDF files
# * Create Sweet Home 3D furniture libraries
# * Install required dependencies (Currently termcolor, PIL, pypdfium2)

import re, os, sys
import argparse, pathlib, tempfile, zipfile, atexit
from os.path import exists
import xml.etree.ElementTree as ET
import bpy, addon_utils
from PIL import Image
from termcolor import cprint
import pypdfium2 as pdfium

filePattern = ".*?/jpg/.*\.jpg"
THUMB_MAX_SIZE = (500, 500)
INCH_IN_MM = 25.4
thumbs = False
compress = False
keep = False
cleanup_files = []
namespaces = {'COLLADA': 'http://www.collada.org/2005/11/COLLADASchema'}

# Functions
def new_empty():
    bpy.ops.wm.read_homefile(app_template='')
    objs = bpy.data.objects
    objs.remove(objs["Cube"], do_unlink=True)
    objs.remove(objs["Camera"], do_unlink=True)
    objs.remove(objs["Light"], do_unlink=True)
    bpy.types.UnitSettings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 0.001
    #bpy.types.UnitSettings.scale_length = 0.001

def get_pixel_sizes(img):
    widthPx, heightPx = img.size
    try:
        if img.info['dpi'][0] != img.info['dpi'][1]:
            raise ValueError("Can't handle different DPI for X and Y.")
        dpi = img.info['dpi'][0]
    except KeyError:
        dpi = 0
    return {"width": widthPx, "height": heightPx, "dpi": dpi}

def get_metric_sizes(img):
    sizes = get_pixel_sizes(img)
    if sizes["dpi"] != 0:
        dpi = sizes["dpi"]
    else:
        dpi = 72
    widthMm = round((sizes["width"] / dpi) * INCH_IN_MM, 2)
    heightMm = round((sizes["height"] / dpi) * INCH_IN_MM, 2)
    return {"width": widthMm, "height": heightMm, "dpi": dpi}

def safe_pil(img, format='JPEG', suffix='.jpg', prefix='generate-models.py-'):
    thumb = tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix, delete=False)
    img.save(thumb, format=format)
    cleanup_files.append(thumb.name)
    return thumb.name

def create_thumb(img, size=THUMB_MAX_SIZE, format='JPEG', suffix='.jpg'):
    original_size = get_metric_sizes(img)
    img.thumbnail(THUMB_MAX_SIZE, Image.Resampling.LANCZOS)
    return (safe_pil(img, format=format, suffix=suffix), original_size["width"], original_size["height"])

def convert_to_collada(inputFile, outputFile, size=None):
    # TODO:
    # * Set sizes (size_mode) to calculated for thumbs
    new_empty()
    import_opts = {
        "use_transparency": True,
        "files": [{'name': inputFile}],
        "directory": os.path.dirname(outputFile),
        "relative": True,
        "align_axis": 'X+'
        # These require an unreleades blender version
        #"blend_method": "OPAQUE",
        #"alpha_mode": False
        #"shader": "SHADELESS"
    }
    if size is None:
        import_opts["size_mode"] = 'DPI'
    else:
        import_opts["size_mode"] = 'ABSOLUTE'
        import_opts["height"] = size['height']

    bpy.ops.import_image.to_plane(**import_opts)
    bpy.ops.wm.collada_export(filepath=outputFile, use_texture_copies=True)

def load_pdf(pdfFileName, index=0, dpi=300):
    pdf = pdfium.PdfDocument(str(pdfFileName))
    width, height = pdf.get_page_size(index)
    img = pdf.render_to(
        pdfium.BitmapConv.pil_image,
        page_indices = index,
        scale = dpi/72
    )
    return (safe_pil(next(img)), width, height)

def get_textures(modelFile):
    xpath = './/COLLADA:library_images/COLLADA:image/COLLADA:init_from'
    collada = ET.parse(modelFile).getroot()
    references = collada.findall(xpath, namespaces=namespaces)
    images = []
    for ref in references:
        images.append(os.path.join(os.path.dirname(modelFile), ref.text))
    return images

def process(inputFile, outputDir, thumbs=False, thumb_size=THUMB_MAX_SIZE, compress=False, keep_generated=False):
    filename = os.path.split(inputFile)[1]
    inputfile = os.path.abspath(inputFile)

    outputFile = os.path.abspath(os.path.join(modelDir, "{}.dae".format(os.path.splitext(filename)[0])))

    cprint("Processing {} to {}".format(inputFile, outputFile), 'green')
    size = None
    if os.path.splitext(filename)[1].lower().endswith('pdf'):
        inputFile, pdfWidth, pdfHeight = load_pdf(inputFile)
    if thumbs:
        img = Image.open(inputFile)
        inputFile, width, height = create_thumb(img, size=thumb_size)
        cprint("Generated thumbnail {}".format(inputFile), 'green')
        size = {"width": width, "height": height}
    if os.path.splitext(filename)[1].lower().endswith('pdf'):
        size = {"width": round((pdfWidth / 72) * INCH_IN_MM, 2) , "height": round((pdfHeight / 72) * INCH_IN_MM, 2)}
    if size is not None:
        cprint("Size is {}mm (width) by {}mm (height)".format(size['width'], size['height']), 'yellow')

    convert_to_collada(inputFile, outputFile=outputFile, size=size)
    if compress:
        zipFilename = os.path.abspath(os.path.join(modelDir, "{}.zip".format(os.path.splitext(filename)[0])))
        cprint("Writing contents to Zip file {}".format(zipFilename))
        create_archive(zipFilename, outputFile, keep_input_on_exit=keep_generated)
        cprint("{} written".format(zipFilename), 'green')
        return [zipFilename]
    else:
        cprint("{} written".format(outputFile), 'green')
        return [outputFile] + get_textures(outputFile)

def install_dependencies():
    import pip
    required_modules = ['termcolor', 'Pillow', 'pypdfium2']
    for module in required_modules:
        try:
            module_obj = __import__(module)
            globals()[module] = module_obj
        except ImportError:
            print("Installing {}".format(module))
            pip.main(['install', module])

def create_archive(to_file, modelFile, keep_input_on_exit=False):
    files = get_textures(modelFile)
    files.append(modelFile)
    cprint("Including files '{}' into {}".format(", ".join(files), to_file), 'yellow')
    with zipfile.ZipFile(to_file, mode="w") as archive:
        for file in files:
            archive.write(file)
        archive.close()
    if not keep_input_on_exit:
        cleanup_files.extend(files)

def cleanup():
    for file in cleanup_files:
        pathlib.Path(file).unlink(missing_ok=True)
        cprint("Deleted file {}".format(file), "yellow")

# enable plugins
addon_utils.enable("io_import_images_as_planes")

parser = argparse.ArgumentParser(prog = 'generate-models.py', description = 'Generate Collada files from images')

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-i', '--input', metavar="[file]", type=pathlib.Path, help="File to convert")
group.add_argument('-d', '--directory', metavar="[directory]", type=pathlib.Path, help="Path to collect images from")
parser.add_argument('-o', '--output', metavar="[directory]", type=pathlib.Path, help="Path to write converted files to",required=True)
parser.add_argument('-s', '--setup', help="Ensure all required modules are present", action='store_true')
parser.add_argument('-z', '--zip', help="Compress results to zip file", action='store_true')
parser.add_argument('-t', '--thumbs', help="Use thumbanails as textures", action='store_true')
parser.add_argument('-k', '--keep', help="Keep generated files", action='store_true')
# TODO: More options: File pattern (for PDF)

try:
    dd = sys.argv.index("--")
    args = parser.parse_args(args=sys.argv[dd+1:])
except ValueError as e: # '--' not in the list:
    cprint("-- not found in argument list, use it after Python file name", "red")
    args = parser.parse_args([])

if args.setup is not None and args.setup is True:
    install_dependencies()

if args.thumbs is not None and args.thumbs is True:
    thumbs = True

if args.zip is not None and args.zip is True:
    compress = True
else:
    compress = False

if args.keep is not None and args.keep is True:
    keep = True
else:
    keep = False

# Other init stuff
for prefix, uri in namespaces.items():
    ET.register_namespace(uri, prefix)
atexit.register(cleanup)

if args.output is not None and exists(args.output):
    modelDir = os.path.abspath(args.output)
elif args.output is not None and not exists(args.output):
    raise ValueError("Output directory {} doesn't exists!".format(args.output))
else:
    parent_dir = os.path.dirname(args.input).parent()
    modelDir = os.path.abspath(os.path.join(parent_dir, '..', 'models'))
    pathlib.Path(modelDir).mkdir(parents=True, exist_ok=True)

cprint("Writing Models to {}".format(modelDir), 'green')

if args.directory is not None and exists(args.directory):
    contentPath = args.directory
    cFilePattern = re.compile(filePattern)
    generated_files = []
    for subdir, dirs, files in os.walk(contentPath):
        for file in sorted(files):
            fileMatch = cFilePattern.match(os.path.join(subdir, file))
            if fileMatch:
                generated_files.extend(process(os.path.join(subdir, file), modelDir, thumbs=thumbs, compress=False))
                if compress:
                    zipFilename = os.path.abspath(os.path.join(modelDir, "{}.zip".format(os.path.basename(modelDir))))
                    with zipfile.ZipFile(zipFilename , mode="w") as archive:
                        for file in generated_files:
                            archive.write(file)
                        archive.close()
                    cprint("{} written".format(zipFilename), 'green')
                    if not keep:
                        cleanup_files.extend(generated_files)

elif args.directory is not None and not exists(args.directory):
    raise ValueError("Directory {} doesn't exists!".format(args.directory))
elif args.input is not None and exists(args.input):
    imgFileName = args.input
    process(imgFileName, modelDir, thumbs=thumbs, compress=compress, keep_generated=keep)
elif args.input is not None and not exists(args.input):
    raise ValueError("Input file {} not found!".format(args.input))

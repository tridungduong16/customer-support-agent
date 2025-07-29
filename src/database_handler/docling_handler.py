import base64

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (PdfPipelineOptions,
                                                PictureDescriptionApiOptions)
from docling.document_converter import DocumentConverter, PdfFormatOption

from src.app_config import app_config

# Set up OpenAI API-based image description
openai_picdesc = PictureDescriptionApiOptions(
    kind="api",
    url="https://api.openai.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {app_config.OPENAI_API_KEY}"},
    params={"model": "gpt-4o-2025-04-14"},
    prompt="Describe this image in a few sentences.",
    provenance="gpt-4o-2025-04-14",
)

# Set all pipeline options in a single config instance
pipeline_options = PdfPipelineOptions(
    generate_picture_images=True,
    generate_page_images=True,
    images_scale=2,
    do_picture_classification=True,
    do_picture_description=True,
    picture_description_options=openai_picdesc,
    enable_remote_services=True,  # <--- This enables API calls!
)
converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)
path = "./data/input_brochure/ACFrOgANHVUSe5pu6G3PxQc5Ex4hbIj-j6NKjOwah1Cv21L2MMZHQFlOH6bdtgekxMB4wtxjIFvKQ_kGgcGFZKb_SHXY1Kql5I96Mg_njgZWtjdZPDHMSGFJpWjfC9RXv9voVnKTUqeeiPnluGMDF5A_zdYBi8EGTh30poWm5Q==.pdf"
result = converter.convert(path)
doc = result.document
print(result.document.pictures)
md = result.document.export_to_markdown()
with open("output_md.md", "w") as f:
    f.write(md)

pic = result.document.pictures[0]
img_uri = pic.image.uri
data_uri = str(img_uri)
if data_uri.startswith("data:image"):
    header, encoded = data_uri.split(",", 1)
    ext = header.split("/")[1].split(";")[0]  # e.g., "png"
    img_bytes = base64.b64decode(encoded)
    with open(f"output_image.{ext}", "wb") as f:
        f.write(img_bytes)
    print(f"Saved image as output_image.{ext}")
else:
    print("Image URI is a path or URL:", data_uri)

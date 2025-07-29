import hashlib
import logging
import os
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import boto3
import markdown
import pandas as pd
import pdfplumber
import pymupdf4llm
import PyPDF2
from bs4 import BeautifulSoup
from tabulate import tabulate
from tqdm import tqdm

from src.app_config import app_config
from src.database_handler.chunk_document import (ChunkDocument,
                                                 SemanticChunkingStrategy)
from src.database_handler.image_processor import ImageProcessingAgent


class DocumentParser:
    def __init__(self):
        self.image_processor = ImageProcessingAgent()
        self.chunk_document = ChunkDocument(strategy=SemanticChunkingStrategy())

    @staticmethod
    def generate_doc_id(filename: str, row_index: Optional[int] = None) -> int:
        """Generate a document ID from filename hash.

        Args:
            filename (str): Name of the file
            row_index (Optional[int]): Row index for CSV files

        Returns:
            int: Generated document ID
        """
        identifier = filename
        if row_index is not None:
            identifier += f"_row_{row_index}"
        hash_object = hashlib.md5(identifier.encode())
        return int(hash_object.hexdigest(), 16) % 1000000

    # def random_filename(self, ext):
    #     return f"{uuid.uuid4().hex[:12]}{ext}"

    # def upload_image_to_s3(self, image_path):
    #     object_key = datetime.now().strftime("%Y/%m/%d")
    #     s3 = boto3.client(
    #         "s3",
    #         aws_access_key_id=app_config.AWS_ACCESS_KEY_ID,
    #         aws_secret_access_key=app_config.AWS_SECRET_ACCESS_KEY,
    #         region_name=app_config.AWS_REGION
    #     )
    #     s3.upload_file(image_path, app_config.AWS_BUCKET_NAME, object_key, ExtraArgs={'ACL': 'public-read'})
    #     url = f"https://{app_config.AWS_BUCKET_NAME}.s3.{app_config.AWS_REGION}.amazonaws.com/{object_key}"
    #     return url

    # def shorten_filename(filename, length=12):
    #     ext = os.path.splitext(filename)[1]
    #     hash_str = hashlib.md5(filename.encode()).hexdigest()[:length]
    #     return f"{hash_str}{ext}"

    def random_filename(self, ext: str) -> str:
        return f"{uuid.uuid4().hex[:12]}{ext}"

    def upload_image_to_s3(self, image_path: str) -> str:
        today = datetime.now().strftime("%Y/%m/%d")
        ext = os.path.splitext(image_path)[1]
        short_name = self.random_filename(ext)
        object_key = f"uploads/{today}/{short_name}"
        s3 = boto3.client(
            "s3",
            aws_access_key_id=app_config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=app_config.AWS_SECRET_ACCESS_KEY,
            region_name=app_config.AWS_REGION,
        )
        s3.upload_file(
            image_path,
            app_config.AWS_BUCKET_NAME,
            object_key,
        )
        url = f"https://{app_config.AWS_BUCKET_NAME}.s3.{app_config.AWS_REGION}.amazonaws.com/{object_key}"
        return url

    def _read_markdown_file_and_add_image_description(self, file_path: str) -> dict:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                matches = re.findall(r"!\[([^\]]*)\]\((.*)\)", content)
                image_paths = []
                for alt_text, image_path in tqdm(matches):
                    description = False
                    if description:
                        image_url = self.image_processor.local_file_to_data_url(
                            image_path
                        )
                        image_description = self.image_processor.describe_image(
                            image_url
                        )
                        public_url = self.upload_image_to_s3(image_path)
                        new_md = (
                            f"({public_url}) - Image Description: {image_description}"
                        )
                    else:
                        public_url = self.upload_image_to_s3(image_path)
                        new_md = f"({public_url})"
                    old_md = f"![{alt_text}]({image_path})"
                    content = content.replace(old_md, new_md)
                    image_paths.append(image_path)
                html = markdown.markdown(content)
                soup = BeautifulSoup(html, "html.parser")
                text = soup.get_text()
                return text

        except Exception as e:
            logging.error(f"❌ Error reading file {file_path}: {e}")
            return {"text": "", "images": []}

    def process_markdown_directory(self, directory_path: str) -> List[Dict]:
        points = []
        for filename in os.listdir(directory_path):
            if filename.endswith(".md"):
                file_path = os.path.join(directory_path, filename)
                content = self.read_markdown_file_and_add_image_description(file_path)
                if content:
                    doc_id = self.generate_doc_id(filename)
                    points.append(
                        {
                            "id": doc_id,
                            "vector": None,
                            "payload": {
                                "text": content,
                                "filename": filename,
                                "file_path": file_path,
                                "source_type": "markdown",
                            },
                        }
                    )
        return points

    def split_markdown_on_standalone_bold(
        self, md_text: str, topic: str = ""
    ) -> List[Dict]:
        """Splits markdown text into sections based on standalone bold headings.

        Args:
            md_text (str): Markdown text to split
            topic (str): Optional topic to prepend to section titles

        Returns:
            List[Dict]: List of sections with titles and content
        """
        bold_heading_pattern = re.compile(r"^\s*\*\*(.+?)\*\*\s*[:：]?\s*$")
        lines = md_text.splitlines()
        chunks = []
        current_chunk = {"title": "Introduction", "content": []}

        for line in lines:
            stripped = line.strip()
            match = bold_heading_pattern.match(stripped)
            if match and not stripped.startswith(("-", "•")):
                if current_chunk["content"]:
                    chunks.append(
                        {
                            "title": current_chunk["title"],
                            "content": "\n".join(current_chunk["content"]).strip(),
                        }
                    )
                heading_text = match.group(1).strip()
                title = (
                    f"**{topic} {heading_text}**" if topic else f"**{heading_text}**"
                )
                current_chunk = {"title": title, "content": []}
            else:
                current_chunk["content"].append(line)

        if current_chunk["content"]:
            chunks.append(
                {
                    "title": current_chunk["title"],
                    "content": "\n".join(current_chunk["content"]).strip(),
                }
            )

        return chunks

    def _pdf_to_markdown(
        self,
        pdf_path: str,
        md_path: str,
        images_dir: str,
    ) -> None:
        md_text = pymupdf4llm.to_markdown(
            pdf_path, write_images=True, image_path=images_dir
        )
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_text)

    def process_pdf_directory(
        self, input_path: str, output_path: str
    ) -> List[Tuple[str, str]]:
        """Process all PDF files in a directory.

        Args:
            input_path (str): Directory containing PDF files
            output_path (str): Directory to save processed files

        Returns:
            List[Tuple[str, str]]: List of (markdown_directory, filename) tuples
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"❌ Input path not found: {input_path}")

        os.makedirs(output_path, exist_ok=True)
        all_md_paths = []

        for filename in os.listdir(input_path):
            if filename.lower().endswith(".pdf"):
                file_name = os.path.splitext(filename)[0]
                pdf_path = os.path.join(input_path, filename)
                md_dir = os.path.join(output_path, f"{file_name}_md")
                images_dir = os.path.join(output_path, f"{file_name}_images")

                logging.info(f"🔍 Processing: {filename}")
                self.pdf_to_markdown(pdf_path, filename, md_dir, images_dir, file_name)
                all_md_paths.append((md_dir, file_name))

        return all_md_paths

    def _extract_tables_from_pdf(
        self, pdf_path: str
    ) -> List[Tuple[int, int, List[List[str]]]]:
        with pdfplumber.open(pdf_path) as pdf:
            all_tables = []
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                for table_index, table in enumerate(tables):
                    # print(table_index, table)
                    # print("--------------------------------")
                    if table:
                        all_tables.append((page_num, table_index, table))
            # import pdb; pdb.set_trace()
            return all_tables

    def table_to_markdown(self, table: List[List[str]]) -> str:
        headers = table[0]
        rows = table[1:]
        return tabulate(rows, headers=headers, tablefmt="github")

    def parse_pdf_and_extract_tables_to_markdown(self, pdf_path: str) -> str:
        result = ""
        tables = self._extract_tables_from_pdf(pdf_path)
        for page_num, table_index, table in tables:
            logging.info(
                f"\n--- Table found on Page {page_num}, Table {table_index} ---\n"
            )
            print(f"\n--- Table found on Page {page_num}, Table {table_index} ---\n")
            md = self.table_to_markdown(table)
            result += md + "\n\n"
        print(result)
        return result.strip()

    def parse_pdf(
        self, pdf_path: str, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[str]:
        if not os.path.exists(pdf_path) or not pdf_path.lower().endswith(".pdf"):
            raise ValueError(f"Invalid PDF file: {pdf_path}")
        try:
            text_content = ""
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content += f"\n\n--- Page {page_num + 1} ---\n\n"
                            text_content += page_text
                    except Exception as e:
                        logging.warning(
                            f"Error extracting text from page {page_num + 1}: {e}"
                        )
                        continue
            if not text_content.strip():
                return []
            text_content = self._clean_pdf_text(text_content)
            chunks = self._chunk_text(text_content, chunk_size, chunk_overlap)
            logging.info(
                f"Successfully parsed PDF '{pdf_path}' into {len(chunks)} chunks"
            )
            return chunks
        except Exception as e:
            logging.error(f"Error parsing PDF document '{pdf_path}': {e}")
            raise

    def _clean_pdf_text(self, text: str) -> str:
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"---\s*Page\s+\d+\s*---", "", text)
        lines = text.split("\n")
        markdown_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                markdown_lines.append("")
                continue
            if len(line) < 80 and not line.endswith((".", ",")):
                if line.isupper():
                    markdown_lines.append(f"# {line}")
                elif line.istitle():
                    markdown_lines.append(f"## {line}")
                else:
                    markdown_lines.append(line)
            else:
                markdown_lines.append(line)
        return "\n".join(markdown_lines)

    def _chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        return self.chunk_document.chunk_text(text, chunk_size, chunk_overlap)

    def read_pdf_path_add_image_description_and_table_convert_to_mardown(
        self, pdf_path: str, md_path: str, images_dir: str
    ) -> str:
        self._pdf_to_markdown(
            pdf_path=pdf_path,
            md_path=md_path,
            images_dir=images_dir,
        )
        content_with_image = self._read_markdown_file_and_add_image_description(md_path)
        table_content = self.parse_pdf_and_extract_tables_to_markdown(pdf_path)
        final_content = content_with_image + "\n\n" + table_content
        with open(md_path, "w", encoding="utf-8") as md_file:
            md_file.write(final_content)
        return final_content

    def read_markdown_file(self, file_path: str) -> str:
        """Read and parse markdown file content."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                html = markdown.markdown(content)
                soup = BeautifulSoup(html, "html.parser")
                return soup.get_text()
        except Exception as e:
            logging.error(f"❌ Error reading file {file_path}: {e}")
            return ""

    def convert_pdf_folder_to_markdown_and_add_image_description_and_table(
        self,
        pdf_folder_path: str,
        md_folder_path: str,
        images_dir: str,
    ) -> str:
        for filename in os.listdir(pdf_folder_path):
            print(f"Processing {filename}")
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(pdf_folder_path, filename)
                md_path = os.path.join(md_folder_path, filename.replace(".pdf", ".md"))
                self.read_pdf_path_add_image_description_and_table_convert_to_mardown(
                    pdf_path, md_path, images_dir
                )
        return


# if __name__ == "__main__":
# document_parser = DocumentParser()
# pdf_path = "./data/input_brochure/ACFrOgANHVUSe5pu6G3PxQc5Ex4hbIj-j6NKjOwah1Cv21L2MMZHQFlOH6bdtgekxMB4wtxjIFvKQ_kGgcGFZKb_SHXY1Kql5I96Mg_njgZWtjdZPDHMSGFJpWjfC9RXv9voVnKTUqeeiPnluGMDF5A_zdYBi8EGTh30poWm5Q==.pdf"
# md_path = "./data/input_brochure/ACFrOgANHVUSe5pu6G3PxQc5Ex4hbIj-j6NKjOwah1Cv21L2MMZHQFlOH6bdtgekxMB4wtxjIFvKQ_kGgcGFZKb_SHXY1Kql5I96Mg_njgZWtjdZPDHMSGFJpWjfC9RXv9voVnKTUqeeiPnluGMDF5A_zdYBi8EGTh30poWm5Q==.md"
# images_dir = "./data/output_brochure/ACF/images"
# res = document_parser.read_pdf_path_add_image_description_and_table(pdf_path, md_path, images_dir)
# print(res)
# import pdb; pdb.set_trace()
# document_parser.pdf_to_markdown(
#     pdf_path=pdf_path,
#     md_path=md_path,
#     images_dir=images_dir,
# )
# import pdb; pdb.set_trace()
# res = document_parser.read_markdown_file_and_add_image_description(md_path)
# res = document_parser.parse_pdf_and_extract_tables_to_markdown(pdf_path)
# print(res)
# import pdb; pdb.set_trace()
# document_parser.process_markdown_directory(md_dir)
# print(res)

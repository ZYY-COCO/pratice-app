from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader
from rapidocr_onnxruntime import RapidOCR


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PDF = PROJECT_ROOT / "data" / "logic_sources" / "logic_7_lessons_part_001.pdf"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "logic_sources" / "logic_7_lessons_part_001_ocr"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OCR scanned logic PDF pages into per-page text files.")
    parser.add_argument("--pdf", default=str(DEFAULT_PDF), help="Source PDF path.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for OCR text files.")
    parser.add_argument("--start-page", type=int, default=1, help="1-based first page to OCR.")
    parser.add_argument("--end-page", type=int, default=None, help="1-based last page to OCR.")
    parser.add_argument("--max-width", type=int, default=1000, help="Downscale page image width for faster OCR.")
    parser.add_argument("--force", action="store_true", help="Re-OCR pages even if output text already exists.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf_path = Path(args.pdf).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(pdf_path))
    page_count = len(reader.pages)
    start_page = max(1, args.start_page)
    end_page = min(args.end_page or page_count, page_count)
    ocr = RapidOCR()

    for page_no in range(start_page, end_page + 1):
      output_path = output_dir / f"page_{page_no:03d}.txt"
      if output_path.exists() and not args.force:
          print(f"[SKIP] page {page_no}/{page_count}: {output_path.name}")
          continue

      page = reader.pages[page_no - 1]
      images = list(page.images)
      if not images:
          output_path.write_text("", encoding="utf-8")
          print(f"[EMPTY] page {page_no}/{page_count}: no image")
          continue

      image = images[0].image.convert("RGB")
      if image.width > args.max_width:
          ratio = args.max_width / image.width
          image = image.resize((args.max_width, int(image.height * ratio)))

      result, _ = ocr(image)
      lines = [item[1].strip() for item in (result or []) if item and len(item) > 1 and item[1].strip()]
      output_path.write_text("\n".join(lines), encoding="utf-8")
      print(f"[OK] page {page_no}/{page_count}: {len(lines)} lines")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

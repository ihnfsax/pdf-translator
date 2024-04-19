import argparse
import translator
from dotenv import load_dotenv
from handler import PDFHandler
from cjk_formatter import CHSFormatter

if __name__ == "__main__":
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="file path of input pdf")
    parser.add_argument(
        "-o",
        "--output",
        metavar="file",
        action="store",
        type=str,
        help="file path of output pdf",
    )
    args = parser.parse_args()

    handler = PDFHandler(translator.OpenAITranslator("en", "zh"), CHSFormatter())
    # handler = PDFHandler(translator.OpenAITranslator("en", "zh"), CHSFormatter())
    handler.handle(args.file, args.output)

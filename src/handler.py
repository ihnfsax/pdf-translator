import os
import fitz
from translator import Translator
from cjk_formatter import CJKFormatter


def dec_to_rgb_float(dec):
    hex_val = format(dec, "06x")
    r = int(hex_val[0:2], 16)
    g = int(hex_val[2:4], 16)
    b = int(hex_val[4:6], 16)
    return round(r / 255, 4), round(g / 255, 4), round(b / 255, 4)


def dec_to_rgb(dec):
    hex_val = format(dec, "06x")
    r = int(hex_val[0:2], 16)
    g = int(hex_val[2:4], 16)
    b = int(hex_val[4:6], 16)
    return r, g, b


HTML = """
    <div><p>%s</p></div>
"""

CSS = """
    @font-face {font-family: MiSans; src: url(MiSans-Regular.ttf);}
    div {
        overflow-wrap: break-word;
    }
    p {
        font-family: %s;
        font-size: %spx;
        line-height: %s%%;
        color: rgb(%s, %s, %s);
    }
"""

MAX_LINE_HEIGHT = 200

BASIC_LINE_HEIGHT = 100


class PDFHandler:
    def __init__(
        self,
        translator: Translator,
        formatter: CJKFormatter,
    ):
        self.translator = translator
        self.formatter = formatter
        self.arch = fitz.Archive("./fonts/")

    def handle(self, input_file: str, output_file=None):
        if not os.path.exists(input_file):
            raise FileNotFoundError("File does not exist: {}".format(input_file))
        self.input_file = input_file
        self.output_file = output_file
        if self.output_file == None:
            self.output_file = os.path.join(
                os.path.dirname(input_file),
                "translated_" + os.path.basename(input_file),
            )
        self.__handle()

    def __suitable_fontsize(self, block):
        count = {}
        for lines in block["lines"]:
            for span in lines["spans"]:
                fontsize = round(span["size"])
                count[fontsize] = count.get(fontsize, 0) + 1
        return max(count, key=count.get)

    def __handle(self):
        doc = fitz.open(self.input_file)
        try:
            for i, page in enumerate(doc):
                print(f"Translating page {i+1}: ", end="")
                blks = page.get_text("blocks")
                blks = [blk for blk in blks if blk[6] != 1]
                new_blks = []
                for j, blk in enumerate(blks):
                    blk_dict = page.get_text("dict", flags=11)["blocks"][blk[5]]
                    style = blk_dict["lines"][0]["spans"][0]
                    new_blks.append({})
                    new_blks[-1]["fontsize"] = self.__suitable_fontsize(blk_dict)
                    new_blks[-1]["rect"] = blk[:4]
                    new_blks[-1]["color"] = style["color"]
                    new_blks[-1]["text"] = blk[4].strip()
                    # if style["flags"] & 2**4:
                    #     new_blks[-1]["fontname"] = "MiSans-Semibold"
                    #     new_blks[-1]["fontfile"] = "./fonts/MiSans-Semibold.ttf"
                    # else:
                    #     new_blks[-1]["fontname"] = "MiSans"
                    #     new_blks[-1]["fontfile"] = "./fonts/MiSans-Regular.ttf"
                    page.add_redact_annot(blk[:4])
                page.apply_redactions()

                for j, new_blk in enumerate(new_blks):
                    print(f"{j+1}/{len(blks)}", flush=True)
                    print(new_blk["text"])
                    success, text = self.translator.translate(new_blk["text"])
                    if not success:
                        print("Failed to translate.")
                        break
                    text = self.formatter.format(text)
                    print("==============")
                    print(text)
                    r, g, b = dec_to_rgb(new_blk["color"])
                    line_height = MAX_LINE_HEIGHT
                    rt = -1
                    while rt < 0:
                        rt, _ = page.insert_htmlbox(
                            new_blk["rect"],
                            HTML % text,
                            css=CSS
                            % ("MiSans", new_blk["fontsize"], line_height, r, g, b),
                            archive=self.arch,
                        )
                        if line_height > BASIC_LINE_HEIGHT:
                            line_height = max(BASIC_LINE_HEIGHT, line_height - 20)
                        else:
                            new_blk["fontsize"] -= 0.5
                if not success:
                    break
                print("")
        except Exception as error:
            print("Exception:\n", error)
        while os.path.exists(self.output_file):
            print("The output file already exists.")
            self.output_file = input("New path: ").strip()
            if len(self.output_file) == 0:
                print("Ignore output.")
                return
        doc.subset_fonts(verbose=True)
        doc.save(self.output_file, garbage=3, deflate=True)

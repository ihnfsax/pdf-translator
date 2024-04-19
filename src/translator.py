import os
import httpx
import re
import html
import requests
import urllib.request
import urllib.parse
from openai import OpenAI

ISO639 = {
    "af": "Afrikaans",
    "sq": "Albanian",
    "am": "Amharic",
    "ar": "Arabic",
    "hy": "Armenian",
    "as": "Assamese",
    "ay": "Aymara",
    "az": "Azerbaijani",
    "bm": "Bambara",
    "eu": "Basque",
    "be": "Belarusian",
    "bn": "Bengali",
    "bho": "Bhojpuri",
    "bs": "Bosnian",
    "bg": "Bulgarian",
    "ca": "Catalan",
    "ceb": "Cebuano",
    "zh-CN": "Simplified Chinese",
    "zh": "Simplified Chinese",
    "zh-TW": "Traditional Chinese",
    "co": "Corsican",
    "hr": "Croatian",
    "cs": "Czech",
    "da": "Danish",
    "dv": "Dhivehi",
    "doi": "Dogri",
    "nl": "Dutch",
    "en": "English",
    "eo": "Esperanto",
    "et": "Estonian",
    "ee": "Ewe",
    "fil": "Filipino(Tagalog)",
    "fi": "Finnish",
    "fr": "French",
    "fy": "Frisian",
    "gl": "Galician",
    "ka": "Georgian",
    "de": "German",
    "el": "Greek",
    "gn": "Guarani",
    "gu": "Gujarati",
    "ht": "HaitianCreole",
    "ha": "Hausa",
    "haw": "Hawaiian",
    "he": "Hebrew",
    "iw": "Hebrew",
    "hi": "Hindi",
    "mn": "Hmong",
    "hu": "Hungarian",
    "is": "Icelandic",
    "ig": "Igbo",
    "lo": "Ilocano",
    "id": "Indonesian",
    "ga": "Irish",
    "it": "Italian",
    "ja": "Japanese",
    "jv": "Javanese",
    "jw": "Javanese",
    "kn": "Kannada",
    "kk": "Kazakh",
    "km": "Khmer",
    "rw": "Kinyarwanda",
    "om": "Konkani	",
    "ko": "Korean",
    "kri": "Krio",
    "ku": "Kurdish",
    "ckb": "Kurdish(Sorani)",
    "ky": "Kyrgyz",
    "lo": "Lao",
    "la": "Latin",
    "lv": "Latvian",
    "ln": "Lingala",
    "lt": "Lithuanian",
    "lg": "Luganda",
    "lb": "Luxembourgish",
    "mk": "Macedonian",
    "mai": "Maithili",
    "mg": "Malagasy",
    "ms": "Malay",
    "ml": "Malayalam",
    "mt": "Maltese",
    "mi": "Maori",
    "mr": "Marathi",
    "mni-Mtei": "Meiteilon(Manipuri)",
    "us": "Mizo",
    "mn": "Mongolian",
    "my": "Myanmar(Burmese)",
    "ne": "Nepali",
    "no": "Norwegian",
    "ny": "Nyanja(Chichewa)",
    "or": "Odia(Oria)",
    "om": "Oromo",
    "ps": "Pashto",
    "fa": "Persian",
    "pl": "Polish",
    "pt": "Portuguese(Portugal,Brazil)",
    "pa": "Punjabi",
    "qu": "Quechua",
    "ro": "Romanian",
    "ru": "Russian",
    "sm": "Samoan",
    "sa": "Sanskrit",
    "gd": "ScotsGaelic",
    "so": "Sepedi",
    "sr": "Serbian",
    "st": "Sesotho",
    "sn": "Shona",
    "sd": "Sindhi",
    "si": "Sinhala(Sinhalese)",
    "sk": "Slovak",
    "sl": "Slovenian",
    "so": "Somali",
    "es": "Spanish",
    "su": "Sundanese",
    "sw": "Swahili",
    "sv": "Swedish",
    "tl": "Tagalog(Filipino)",
    "tg": "Tajik",
    "ta": "Tamil",
    "tt": "Tatar",
    "te": "Telugu",
    "th": "Thai",
    "ti": "Tigrinya",
    "ts": "Tsonga",
    "tr": "Turkish",
    "tk": "Turkmen",
    "ak": "Twi(Akan)",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "ug": "Uyghur",
    "uz": "Uzbek",
    "vi": "Vietnamese",
    "cy": "Welsh",
    "xh": "Xhosa",
    "yi": "Yiddish",
    "yo": "Yoruba",
    "zu": "Zulu",
}

RETRY_LIMIT = 3

OPANAI_USER_PROMPT = """
You are a professional translator. So, you must obey the following rules:

1. Do not translate person's name, like Jack Smith.
2. Do not translate specific terms, like ACID.
3. Do not translate programming code, like print("Hello, World!").
4. Do not translate arabic numerals, like 123.
5. Never apologize. For content you can't translate, just keep it as it is.

Here are two good examples of English to Chinese translation:

Good Example 1:
Text to translate:
Jack Smith came up with ACID in 1972.

What you should return:
Jack Smith 在 1972 年提出了 ACID。

Good Example 2:
Text to translate:
We can use pip install command to install Python packages.

What you should return:
我们可以使用 pip install 命令来安装 Python 包。

Here are two bad examples of English to Chinese translation:
Bad Example 1:
Text to translate:
8

What you should return:
Sorry, I can't translate arabic numerals.

Explain:
Don't apologize. You should keep the arabic numerals as it is. Just return 8 is enough.

Bad Example 2:
Text to translate:
ls

What you should return:
ls (不需要翻译)

Explain:
Never add unrelated content like "(不需要翻译)". If there is no need to translate it, just keep the original text.

Now, you should translate the following text from %s to %s.
Text to translate:
%s
Your translation:
"""


class Translator:
    def __init__(self, src_lang, tgt_lang):
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang

    # Return (success, translated_text)
    def translate(self, text):
        return True, text


class OpenAITranslator(Translator):
    def __init__(self, src_lang, tgt_lang):
        if src_lang == "auto":
            self.src_lang = "Any Language"
        else:
            if src_lang not in ISO639:
                raise ValueError(f"Unsupported language: {src_lang}")
            self.src_lang = ISO639[src_lang]
        if tgt_lang not in ISO639:
            raise ValueError(f"Unsupported language: {tgt_lang}")
        self.tgt_lang = ISO639[tgt_lang]

        if "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        api_key = os.environ["OPENAI_API_KEY"]
        base_url = "https://api.openai.com/v1/"
        if "OPENAI_API_BASE" in os.environ:
            base_url = os.environ["OPENAI_API_BASE"]
        if "OPENAI_PROXY" in os.environ:
            self.openai = OpenAI(
                http_client=httpx.Client(proxy=os.environ["OPENAI_PROXY"]),
                api_key=api_key,
                base_url=base_url,
            )
        else:
            self.openai = OpenAI(api_key=api_key, base_url=base_url)

        self.messages = [
            {
                "role": "system",
                "content": "You are a professional translator.",
            },
        ]

    def translate(self, text):
        prompt = OPANAI_USER_PROMPT % (self.src_lang, self.tgt_lang, text)
        self.messages.append({"role": "user", "content": prompt})
        reach_limit = False
        request_count = 0
        while True:
            request_count += 1
            try:
                response = self.openai.chat.completions.create(
                    model="gpt-3.5-turbo", messages=self.messages
                )
                break
            except Exception as e:
                print(f"OpenAITranslator exception: {e}")
                if request_count >= RETRY_LIMIT:
                    print("Reach retry limit.")
                    reach_limit = True
                    break
        del self.messages[1]
        if reach_limit:
            return False, text
        return True, response.choices[0].message.content.strip()


class GoogleTranslator(Translator):
    def __init__(self, src_lang, tgt_lang, merge_lines=True):
        if src_lang != "auto" and src_lang not in ISO639:
            raise ValueError(f"Unsupported language: {src_lang}")
        if tgt_lang not in ISO639:
            raise ValueError(f"Unsupported language: {tgt_lang}")
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.merge_lines = merge_lines

    def translate(self, text):
        base_link = (
            "https://clients5.google.com/translate_a/t?client=at&sl=%s&tl=%s&q=%s"
        )
        if self.merge_lines:
            text = text.replace("\n", " ")
        to_translate = urllib.parse.quote(text)
        link = base_link % (self.src_lang, self.tgt_lang, to_translate)
        reach_limit = False
        request_count = 0
        while True:
            request_count += 1
            try:
                res = requests.get(link).json()[0]
                if len(res) == 0:
                    raise ValueError("No translation found")
                break
            except Exception as e:
                print(f"GoogleTranslator exception: {e}")
                if request_count >= RETRY_LIMIT:
                    print("Reach retry limit.")
                    reach_limit = True
                    break
        if reach_limit:
            return True, text
        return True, res

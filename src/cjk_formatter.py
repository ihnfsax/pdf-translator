import re


class CJKFormatter:
    def __init__(self):
        pass

    def format(self, text):
        return text


class CHSFormatter(CJKFormatter):
    def __init__(self):
        pass

    def is_cjk(self, word):
        for ch in word:
            if "\u4e00" <= ch <= "\u9fff":
                return True
        return False

    def format(self, text):
        text = self.__format(text, r"([\u4e00-\u9fff]+)")
        return text

    def __format(self, text, pattern):
        spliter = re.compile(pattern)
        phrases = spliter.split(text)
        result = ""
        for i, phrase in enumerate(phrases):
            if "\n" == phrase:
                result += phrase
                continue
            s = phrase.strip()
            if len(s) == 0:
                continue
            if s[-1].isascii():
                s += " "
            if i != 0 and s[0].isascii():
                s = " " + s
            result += s
        return result

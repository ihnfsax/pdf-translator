# PDF 翻译器

## 使用说明

在 `src` 目录下添加 `.env` 文件，设置 OpenAI 参数：

```bash
OPENAI_API_KEY='sk-xxxxxxx'
OPENAI_API_BASE='https://api.openai.com/v1'
OPENAI_PROXY='http://xxx.xxx.xxx.xxx:xxxx'
```

运行：

```bash
python3 ./src/main.py ./test.pdf
```
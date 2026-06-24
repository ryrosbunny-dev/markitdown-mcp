from mcp.server.fastmcp import FastMCP
from markitdown import MarkItDown
import httpx, tempfile, os
from pathlib import Path

mcp = FastMCP(
    "markitdown",
    stateless_http=True,
)
md = MarkItDown()


@mcp.tool()
def convert_url(url: str) -> str:
    """Скачивает файл по URL и конвертирует в Markdown."""
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        r = client.get(url)
        r.raise_for_status()

    content_type = r.headers.get("content-type", "")
    ext = _ext_from_ct(content_type) or Path(url).suffix or ".bin"

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(r.content)
        tmp_path = f.name

    try:
        result = md.convert(tmp_path)
        return result.text_content
    finally:
        os.unlink(tmp_path)


@mcp.tool()
def convert_base64(filename: str, base64_data: str) -> str:
    """Принимает файл как base64-строку и конвертирует в Markdown."""
    import base64
    ext = Path(filename).suffix or ".bin"
    data = base64.b64decode(base64_data)

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(data)
        tmp_path = f.name

    try:
        result = md.convert(tmp_path)
        return result.text_content
    finally:
        os.unlink(tmp_path)


def _ext_from_ct(ct: str) -> str:
    mapping = {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "application/msword": ".doc",
    }
    for k, v in mapping.items():
        if k in ct:
            return v
    return ""


if __name__ == "__main__":
    import uvicorn
    app = mcp.streamable_http_app()
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

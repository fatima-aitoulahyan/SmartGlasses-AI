import httpx
import time
from schemas import AnalyzeResponse


async def route_request(
    mode: str,
    image_bytes: bytes,
    filename: str,
    content_type: str,
    urls: dict
) -> AnalyzeResponse:

    start = time.time()
    files = {"file": (filename, image_bytes, content_type)}

    url_map = {
        "obstacle": (urls["obstacle"], "/detect"),
        "ocr":      (urls["ocr"],      "/read"),
        "money":    (urls["money"],    "/recognize"),
    }

    if mode not in url_map:
        return AnalyzeResponse(
            mode=mode,
            result={},
            success=False,
            error=f"Invalid mode '{mode}'. Use: obstacle | ocr | money",
            processing_time_ms=0.0
        )

    base_url, path = url_map[mode]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}{path}",
                files=files
            )
            response.raise_for_status()

        elapsed = (time.time() - start) * 1000

        return AnalyzeResponse(
            mode=mode,
            result=response.json(),
            success=True,
            processing_time_ms=round(elapsed, 2)
        )

    except httpx.ConnectError:
        return AnalyzeResponse(
            mode=mode,
            result={},
            success=False,
            error=f"Service '{mode}' is unreachable",
            processing_time_ms=0.0
        )
    except Exception as e:
        return AnalyzeResponse(
            mode=mode,
            result={},
            success=False,
            error=str(e),
            processing_time_ms=0.0
        )

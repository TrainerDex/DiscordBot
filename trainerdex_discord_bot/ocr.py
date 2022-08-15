import os
from typing import ClassVar, Dict

import aiohttp
from discord import Attachment


class OCRClient:

    HOST: ClassVar[str] = os.environ.get("TRAINERDEX_HOST", "https://trainerdex.app")

    @classmethod
    async def request_activity_view_scan(cls, image: Attachment) -> Dict[str, float]:
        async with aiohttp.ClientSession() as session:
            headers = {"Content-Disposition": f"attachment; filename={image.filename}"}
            async with session.put(
                f"{cls.HOST}/api/ocr/activity-view/", data=await image.read(), headers=headers
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

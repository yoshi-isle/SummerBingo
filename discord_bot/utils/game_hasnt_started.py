from constants import ApiUrls

async def game_hasnt_started(session) -> bool:
    async with session.get(ApiUrls.GAME_IS_RUNNING) as running:
        running = await running.json()
        return not running["running"]
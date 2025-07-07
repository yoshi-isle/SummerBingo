
                     
from constants import ApiUrls

async def get_team_from_id(session, user_id) -> bool:
    try:
        async with session.get(ApiUrls.TEAM_BY_ID.format(id=user_id)) as resp:
            if resp.status == 200:
                team_data = await resp.json()
                return team_data
    except Exception as e:
        print(e)
        return None
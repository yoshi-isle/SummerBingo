class DiscordIDs:
    PENDING_SUBMISSIONS_CHANNEL_ID = 1379165881518522408
    APPROVED_SUBMISSIONS_CHANNEL_ID = 1379165982391533588
    GUILD_ID = 1367922296764891246
    TANGY_DISCORD_ID = 726237123857874975

class ApiUrls:
    BASE_URL = "http://game_service_api:5000"
    TEAM = f"{BASE_URL}/teams"
    TEAM_BY_ID = f"{BASE_URL}/teams/discord/{{id}}"
    TEAM_CURRENT_TILE = f"{BASE_URL}/teams/discord/{{id}}/current_tile"
    SUBMISSION = f"{BASE_URL}/submission/{{id}}"
    CREATE_SUBMISSION = f"{BASE_URL}/submission"
    APPROVE_SUBMISSION = f"{BASE_URL}/submission/approve/{{id}}"
    TEAM_ADVANCE_TILE = f"{BASE_URL}/teams/{{id}}/advance_tile"
    IMAGE_BOARD = f"{BASE_URL}/image/user/{{id}}"
    IMAGE_GET = f"{BASE_URL}/images/{{url}}"

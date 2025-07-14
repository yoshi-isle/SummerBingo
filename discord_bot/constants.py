class Emojis:
    TRIAL_COMPLETE="<:trial_complete:1391972435170951319>"
    TRIAL_INCOMPLETE="<:trial_incomplete:1392530655761535147>"
    DUNGEON="<:dungeon:1389648812355748051>"
    OLMLET="<:Olmlet:1389757224963801229>"
    SKW_LOGO="https://i.imgur.com/KHEg8dQ.png"

    WORLD_MAP="<:World_map_icon:1393651056507879464>"
    SUBMISSIONS="<:200pxPoll_icon:1393651395273555998>"
    SKIP="<:Agility_shortcut_balance:1393651820047634534>"
    CHECKMARK_GIF="<a:check:1393652924756005055>"
    TROPHY="<:Trailblazer_reloaded_dragon_trop:1394184136939274362>"

    VARLAMORE_FLAG="<:240pxBanner_Varlamore:1393657344763756755>"
    RALOS="<:Tonalztics_of_ralos:1393657151855005918>"

    ANCIENT_ICON="<:Ancient_icon:1393667207887847494>"
    ZCB="<:Zaryte_crossbow:1393667503967699155>"

    FIRE="<:fire:1393662791835193444>"

    BLOOD_RUNE="<:Blood_rune:1394108157076177020>"
    
    TRIAL_W1_1="<:any_cox_purple:1391970457217007677>"
    TRIAL_W1_2="<:Crystal_tool_seed:1391971507365740555>"
    TRIAL_W1_3="<:Burning_claw:1391971831681912964>"
    TRIAL_W1_4="<:Bryophyta27s_essence:1391971963378860093>"
    TRIAL_W1_5="<:Clue_scroll_28elite29:1391972076545511464>"

    TRIAL_ICON_W1="<:Ancient_remnant:1392604921190289530>"

    TRIAL_W2_1="<:Golden_tench:1392602820737368220>"
    TRIAL_W2_2="<:Obsidian_platebody:1392603054955696199>"
    TRIAL_W2_3="<:Uncut_onyx:1392603338293379202>"
    TRIAL_W2_4="<:Primordial_crystal:1392603490328776774>"
    TRIAL_W2_5="<:Elidinis27_ward:1392603633907929228>"

    TRIAL_W4_1="<:Holy_elixir:1392977427025629194>"
    TRIAL_W4_2="<:Amulet_of_eternal_glory:1392977534517379242>"
    TRIAL_W4_3="<:Sanguinesti_staff:1392977699957510215>"
    TRIAL_W4_4="<:Nightmare_staff:1392977819436318810>"
    TRIAL_W4_5="<:Crystal_armour_seed:1392977899111579758>"


    TWISTED_BOW="<:Twisted_bow:1392562692472176641>"

    ADMIN="<:admin:1392259079497584844>"
    

class DiscordIDs:
    PENDING_SUBMISSIONS_CHANNEL_ID = 1379165881518522408
    APPROVED_SUBMISSIONS_CHANNEL_ID = 1379165982391533588
    DENIED_SUBMISSIONS_CHANNEL_ID = 1386546724935307475
    GUILD_ID = 1367922296764891246
    TANGY_DISCORD_ID = 726237123857874975

class ApiUrls:
    BASE_URL = "http://game_service_api:5000"

    # Game state
    GAME_IS_RUNNING = f"{BASE_URL}/game_started"
    # Teams
    TEAM = f"{BASE_URL}/teams"
    TEAM_ALL = f"{BASE_URL}/teams"
    TEAM_BY_ID = f"{BASE_URL}/teams/discord/{{id}}"
    TEAM_BY_ID_WITHOUT_DISCORD = f"{BASE_URL}/teams/id/{{id}}"
    TEAM_CURRENT_TILE = f"{BASE_URL}/teams/{{id}}/current_tile"
    TEAM_ADVANCE_TILE = f"{BASE_URL}/teams/{{id}}/advance_tile"
    TEAM_LEVEL_NUMBER = f"{BASE_URL}/teams/{{id}}/world_level"
    TEAM_LEVEL_NUMBER_WITHOUT_DISCORD = f"{BASE_URL}/teams/id/{{id}}/world_level"
    TEAM_BOARD_INFORMATION = f"{BASE_URL}/teams/id/{{id}}/board_information"
    ADVANCE_TO_BOSS_TILE = f"{BASE_URL}/teams/{{id}}/boss_tile"
    ADVANCE_TO_NEXT_WORLD = f"{BASE_URL}/teams/{{id}}/next_world"
    TEAM_LAST_ROLLED = f"{BASE_URL}/teams/{{id}}/last_rolled"

    TEAM_TRAVERSE_W2_TRIAL = f"{BASE_URL}/teams/{{id}}/{{option}}/w2_trial_traverse_path"
    
    TEAM_COMPLETE_W2_TRIAL = f"{BASE_URL}/teams/{{id}}/complete_w2_trial"
    TEAM_COMPLETE_W3_TRIAL = f"{BASE_URL}/teams/{{id}}/{{brazier_number}}/complete_w3_trial"
    TEAM_ITERATE_W4_TRIAL = f"{BASE_URL}/teams/{{id}}/update_w4_trial_iteration"
    TEAM_COMPLETE_W4_TRIAL = f"{BASE_URL}/teams/{{id}}/complete_w4_trial"

    TEAM_PLACEMENT = f"{BASE_URL}/teams/{{id}}/placement"

    # Submissions
    SUBMISSION = f"{BASE_URL}/submission/{{id}}"
    KEY_SUBMISSION = f"{BASE_URL}/key_submission/{{id}}"
    BOSS_SUBMISSION = f"{BASE_URL}/boss_submission/{{id}}"
    CREATE_SUBMISSION = f"{BASE_URL}/submission"
    CREATE_KEY_SUBMISSION = f"{BASE_URL}/key_submission"
    CREATE_BOSS_SUBMISSION = f"{BASE_URL}/boss_submission"
    APPROVE_SUBMISSION = f"{BASE_URL}/submission/approve/{{id}}"
    APPROVE_KEY_SUBMISSION = f"{BASE_URL}/submission/approve_key/{{key_id}}/{{id}}"
    APPROVE_BOSS_SUBMISSION = f"{BASE_URL}/submission/approve_boss/{{id}}"
    DENY_SUBMISSION = f"{BASE_URL}/submission/deny/{{id}}"

    # Images
    IMAGE_BOARD = f"{BASE_URL}/image/team/{{id}}"
    IMAGE_GET = f"{BASE_URL}/images/{{url}}"

WORLD_NAMES = {
    1: "Mystic Cove",
    2: "Tumeken's Oasis",
    3: "Withering Frostlands",
    4: "The Void",
}
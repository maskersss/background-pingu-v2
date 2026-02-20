LINK_PATTERN = r"https:\/\/(?:api\.)?(?:pastee\.dev|paste.ee)\/.\/\w+|https://(?:api\.)?mclo\.gs/(?:1/raw/)?\w+|https?:\/\/[\w\-_\/.]+\.(?:json|txt|log|tdump)\?ex=[^&]+&is=[^&]+&hm=[^&]+&|https?:\/\/[\w\-_\/.]+\.(?:json|txt|log|tdump)"

MAX_STARTING_LOG_LINES = 3500
MAX_ENDING_LOG_LINES = 6000

SERVER_SUPPORT_BOT_CHANNEL_IDS = [
    # server id         , support channel id , bot cmds channel id
    (83066801105145856  , 727673359860760627 , 433058639956410383 ), # javacord
    (1056779246728658984, 1074385256070791269, 1074343944822992966), # rankedcord
    (1262887973154848828, 1262901524619595887, 1271835972912545904), # seedqueuecord
    (1472102343381352539, 1472103453806563484, 1472498007877484724), # toolscreencord
    (1062467800641306696, 1062467804877561878, None               ), # jinglecord
    (1095808506239651942, 1424239180313264250, None               ), # resetticord
    (933654537057738812 , 933914673437368380 , 1123664786341773432), # fsgcord
    (1033677387143061574, 1033763530798800908, None               ), # srigtcord
    (781169188550869022 , 1071138999604891729, None               ), # for testing
]

IGNORED_USERS = [
    473868086773153793,    # zeppelin
    1110166332059697222,   # pingu
    834848683697635328,    # test
]


DOMAIN = "enphase_cloud_things"

CONF_SITE_ID = "site_id"
CONF_SITE_NAME = "site_name"
CONF_SERIALS = "serials"
CONF_EAUTH = "e_auth_token"
CONF_ACCESS_TOKEN = "access_token"
CONF_COOKIE = "cookie"
CONF_SESSION_ID = "session_id"
CONF_TOKEN_EXPIRES_AT = "token_expires_at"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_REMEMBER_PASSWORD = "remember_password"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_VPP_PROGRAM_ID = "vpp_program_id"
DEFAULT_SCAN_INTERVAL = 30

# Option keys
OPT_FAST_POLL_INTERVAL = "fast_poll_interval"
OPT_SLOW_POLL_INTERVAL = "slow_poll_interval"
OPT_FAST_WHILE_STREAMING = "fast_while_streaming"
OPT_NOMINAL_VOLTAGE = "nominal_voltage"
OPT_ENABLE_MONETARY_DEVICE = "enable_monetary_device"
OPT_ENABLE_VPP_DEVICE = "enable_vpp_device"

BASE_URL = "https://enlighten.enphaseenergy.com"
ENTREZ_URL = "https://entrez.enphaseenergy.com"
LOGIN_URL = f"{BASE_URL}/login/login.json"
DEFAULT_AUTH_TIMEOUT = 15
DEFAULT_API_TIMEOUT = 15
OPT_API_TIMEOUT = "api_timeout"
DEFAULT_NOMINAL_VOLTAGE = 240

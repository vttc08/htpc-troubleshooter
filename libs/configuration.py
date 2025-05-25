import dotenv
import os
import logging

dotenv.load_dotenv(".env")
logging_level = os.getenv("logging_level", "INFO")
language = os.getenv("language", "en")
logging.basicConfig(level=logging_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(filename)s")
logger = logging.getLogger(__name__)
aiologger = logging.getLogger("asyncio")
aiologger.setLevel(logging.ERROR)
aiohttp_logger = logging.getLogger("aiohttp_client")
aiohttp_logger.setLevel(logging.ERROR)

hass_port = os.getenv("hass_port", 8123)
hass_host = os.getenv("hass_host", "localhost")
hass_token = os.getenv("hass_token", "")

jf_url = os.getenv("jf_url", "http://localhost:8080")
jf_key = os.getenv("jf_key", "")

avr_host = os.getenv("avr_host", "localhost")
avr_port = os.getenv("avr_port", 60128)

hass_http_url = f"http://{hass_host}:{hass_port}/api"
hass_websocket_url = f"ws://{hass_host}:{hass_port}/api/websocket"

ha_debug=os.getenv("ha_debug", "False")

if ha_debug == "True":
    logger.debug("Loading dummy Home Assistant entities.")
    ha_mp_tv="input_boolean.tv"
    ha_mp_avr="input_boolean.avr"
    ha_mp_atv="input_boolean.android"
    ha_domain="input_boolean"
else:
    ha_mp_tv=os.getenv("ha_mp_tv", "media_player.samsung_tv")
    ha_mp_avr=os.getenv("ha_mp_avr", "media_player.denon_avr")
    ha_mp_atv=os.getenv("ha_mp_atv", "media_player.android")
    ha_mp_adb=os.getenv("ha_mp_adb", "media_player.android_tv")
    ha_domain="media_player"
    logger.debug("Loading Home Assistant entities.")

ffm_debug=os.getenv("ffm_debug", "False")

apprise_url = os.getenv("apprise_url")

subdl_api_key = os.getenv("subdl_api_key")

coreelec_host = os.getenv("coreelec_host", "localhost")
coreelec_user = os.getenv("coreelec_user", "root")
coreelec_password = os.getenv("coreelec_password", "coreelec")

logger.debug("Configuration loaded.")


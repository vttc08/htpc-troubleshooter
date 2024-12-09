from libs.configuration import *
from libs.homeassistant import HASync

import logging
aiohttp_logger = logging.getLogger("aiohttp_client_cache")
aiohttp_logger.setLevel(logging.WARNING)

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi_and_babel.translator import FastAPIAndBabel
from fastapi_and_babel import gettext as _
from homeassistant_api import State

logger = logging.getLogger(__name__)

def lifespan(app: FastAPI):
    app.haclient = HASync(hass_http_url, hass_token)
    pass
    yield
    app.haclient.close()

app = FastAPI(lifespan=lifespan)
print(language)
translator = FastAPIAndBabel(__file__, app, default_locale=language, translation_dir="lang")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.globals['_'] = _ # Important for Jinja2 to use _

# Main route
@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request
    })

# Volume too low route
@app.get("/volume_too_low")
async def volume_too_low(request: Request):
    onkyo = await app.haclient.async_get_state_check(domain=ha_domain, entity_id=ha_mp_avr)
    onkyo = State(**onkyo)
    vol = onkyo.attributes.get("volume_level", 0)
    if vol < 0.48: # 43%  = -39 db 53% = -29 db
        custom_msg = _("The receiver volume is too low or is not turned on. The system will attempt to raise the volume.")
        await app.haclient.async_trigger_service(ha_domain, "volume_set", entity_id=ha_mp_avr, volume_level=0.53)
    else:
        custom_msg = _("The receiver volume is at good level. If the sound is still low or there is no sound, there may be another issue. Click the link below for more information.")

    return templates.TemplateResponse("partial/volume_too_low.html", {
        "request": request,
        "custom_msg": custom_msg
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
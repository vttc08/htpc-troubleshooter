from libs.configuration import *
from libs.homeassistant import HASync
from libs.jellyfin import JellyfinAsyncClient, filter_activity, check_zh_sub
from libs.affmpeg import AudioCodec, probe

import logging
import asyncio
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi_and_babel.translator import FastAPIAndBabel
from fastapi_and_babel import gettext as _
from homeassistant_api import State

logger = logging.getLogger(__name__)

error_codes = ["bluescreen", "volume_too_low", "just_player_error", "buffering","audio_desync","no_zh_sub","sub_desync"]

def lifespan(app: FastAPI):
    app.haclient = HASync(hass_http_url, hass_token)
    app.jfclient = JellyfinAsyncClient(jf_url, jf_key)
    app.counter = 0
    pass
    yield
    app.haclient.close()

app = FastAPI(lifespan=lifespan)
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
    vol = onkyo.attributes.get("volume_level", 0)
    if vol < 0.48: # 43%  = -39 db 53% = -29 db
        custom_msg = _("The receiver volume is too low or is not turned on. The system will attempt to raise the volume.")
        await app.haclient.async_trigger_service(ha_domain, "volume_set", entity_id=ha_mp_avr, volume_level=0.53)
    else:
        custom_msg = _("The receiver volume is at good level. If the sound is still low or there is no sound, there may be another issue. Click the link below for more information.")
    return templates.TemplateResponse("partial/custom_help.html", {
        "request": request,
        "custom_msg": custom_msg,
        "event": "volume_too_low"
    })

@app.get("/bluescreen")
async def bluescreen(request: Request):
    onkyo = await app.haclient.async_get_state_check(domain=ha_domain, entity_id=ha_mp_avr)
    avr_input = onkyo.attributes.get("source", None)
    # Bluray - Bluray - Windows HTPC
    # Game - Video 3 - Homatics
    allowed_inputs = ["Video 3", "Game"]
    if avr_input not in allowed_inputs:
        custom_msg = _("The receiver input is not set to the correct input. The system will attempt to switch to the correct input.")
        await app.haclient.async_trigger_service(ha_domain, "select_source", entity_id=ha_mp_avr, source="Game")
    else:
        custom_msg = _("The receiver input is set to the correct input. If the screen is still blue, there may be another issue. Click the link below for more information.")
    return templates.TemplateResponse("partial/custom_help.html", {
        "request": request,
        "custom_msg": custom_msg,
        "event": "bluescreen"
    })

@app.get("/mediachooser")
async def mediachooser(request: Request, errtype: str):
    next_action = "subsync" if errtype == "sub_desync" else "mediachecker"
    media_list = await app.jfclient.get_activities()
    tasks = []
    for media in media_list:
        task = asyncio.create_task(app.jfclient.get_item(media))
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    media_list = []
    for result in results:
        media_list.append(result)
    return templates.TemplateResponse("media_chooser.html", {
        "request": request,
        "media_list": media_list,
        "err_type": errtype,
        "jf_url": jf_url,
        "next_action": next_action
    })

@app.get("/reboot_wait")
async def reboot_wait(request: Request, item_id: str):
    logger.info("simulating Android box rebooting")
    app.counter += 1
    if app.counter >= 2:
        pass # set playback progress 5s forward if playback repeatedly crashes
    item_info = await app.jfclient.get_item(item_id)
    return templates.TemplateResponse("reboot.html", {
        "request": request,
        "item_info": item_info,
        "times": app.counter
    })

async def sse_generator(original_title):
    logger.info("Simulating opening Jellyfin")
    yield "data: Opening Jellyfin\n\n"
    await asyncio.sleep(1)
    logger.info("Simulating clicking the search box")
    yield "data: Clicking the search box\n\n"
    await asyncio.sleep(1)
    logger.info(f"Simulating typing the title {original_title}")
    yield f"data: Typing the title {original_title}\n\n"
    yield "event: stop\ndata: done\n\n"

@app.get("/automate_jf")
async def automate_jf(request: Request, original_title: Optional[str] = None):
    """Automate opening of Jellyfin on Android box"""
    return StreamingResponse(sse_generator(original_title), media_type="text/event-stream")

@app.get("/post-reboot")
async def show_sse(request: Request,item_id: Optional[str] = None, original_title: Optional[str] = None):
    """For HTMX"""
    if item_id is not None and original_title is None:
        item_info = await app.jfclient.get_item(item_id)
        original_title = item_info.get("OriginalTitle", None)
    print(original_title)
    return templates.TemplateResponse("post-reboot.html", {
        "request": request,
        "original_title": original_title
    })

@app.get("/mediachecker")
async def mediachecker(request: Request, response: Response, item_id: Optional[str], errtype: Optional[str]):
    item_info = await app.jfclient.get_item(item_id)
    # src_codec, is_p7, is_atmos = await probe(item_info.get("Path"))
    # Example data
    src_codec = AudioCodec("truehd", False)
    is_p7 = False
    is_atmos = False
    if errtype == "no_zh_sub":
        response.headers['HX-Redirect'] = "/zh_sub?item_id=" + item_id

    elif errtype == "buffering":
        pass # Will implement later, show networking info
        response.headers['HX-Redirect'] = "https://www.facebook.com"
    elif errtype == "just_player_error" and is_p7 == True:
        pass # Will implement later, show CoreELEC not implemented help
        response.headers['HX-Redirect'] = "https://www.youtube.com"
    else:
        response.headers['HX-Redirect'] = "/reboot_wait?item_id=" + item_id

@app.get("/zh_sub")
async def zh_sub(request: Request, item_id: Optional[str]):
    item_info = await app.jfclient.get_item(item_id)
    has_zh_sub, display_title = check_zh_sub(item_info.get("MediaStreams"))
    if not has_zh_sub:
        await asyncio.sleep(5)
        pass # implement downloading later
    return templates.TemplateResponse("zh_sub.html", {
        "request": request,
        "has_zh_sub": has_zh_sub,
        "display_title": display_title,
    })

@app.get("/test") # test fastAPI endpoint as standalone functions
async def test(request: Request, response: Response):
    item_id="258ea53c4473b40df5b6d09f679f762b"
    rebooted = await reboot_wait(request, item_id)
    async for result in sse_generator("The Matrix"):
        pass
    response.headers['HX-Redirect'] = "/mediachooser?errtype=bluescreen"

@app.post('/jfwebhook')
async def data(data: Dict[str, Any]):
    ClientName = data.get("ClientName", None)
    DeviceName = data.get("DeviceName", None)
    item_id = data.get("ItemID", None)
    item_data = await app.jfclient.get_item(item_id)
    # ac, is_p7, is_atmos = await probe(item_data.get("Path"))
    if data.get("NotificationType", None) == "PlaybackStart":
        print("PlaybackStart")
    elif data.get("NotificationType", None) == "PlaybackStop":
        print("Stop PlaybackStart")
    else:
        print("Unknown")

    return data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
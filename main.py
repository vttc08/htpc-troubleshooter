from libs.configuration import *
from libs.homeassistant import HASync
from libs.jellyfin import JellyfinAsyncClient, filter_activity, check_zh_sub
from libs.affmpeg import AudioCodec, probe
from libs.aonkyo import run_task, ReceiverController
from libs.helper import keyevent, send_keys, tap, package
from libs.pyapprise import apprise_obj
from libs.subtitles import subtitle_providers

import logging
import sys
import asyncio
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi_and_babel.translator import FastAPIAndBabel
from fastapi_and_babel import gettext as _

logger = logging.getLogger(__name__)

error_codes = ["bluescreen", "volume_too_low", "just_player_error", "buffering","audio_desync","no_zh_sub","sub_desync"]

docs_lang = '/' if language == 'en' else '/zh/'

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def lifespan(app: FastAPI):
    app.haclient = HASync(hass_http_url, hass_token)
    app.jfclient = JellyfinAsyncClient(jf_url, jf_key)
    app.counter = 0
    app.jf_automation_counter = 0
    app.onkyo_check = False
    yield
    # app.haclient.close()

app = FastAPI(lifespan=lifespan)
translator = FastAPIAndBabel(__file__, app, default_locale=language, translation_dir="lang")
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
app.mount("/support", StaticFiles(directory="support", html=True), name="support")
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
    await app.haclient.adb(entity_id=ha_mp_adb, command="reboot")
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
    sleep_time = 1 if app.jf_automation_counter > 0 else 1 
    logger.info("Simulating opening Jellyfin")
    # await app.haclient.adb(entity_id=ha_mp_adb, command=package(True, "org.jellyfin.androidtv"))
    yield "data: Opening Jellyfin\n\n"
    await asyncio.sleep(sleep_time)
    logger.info("Simulating clicking the search box")
    yield "data: Clicking the search box\n\n"
    await asyncio.sleep(sleep_time)
    logger.info(f"Simulating typing the title {original_title}")
    msg = _("Typing the title")
    yield f"data: {msg}: {original_title}\n\n"
    # yield f"data: Typing the title {original_title}\n\n"
    await asyncio.sleep(sleep_time)
    yield f"data: ==========================\n\n"
    msg = _("The troubleshooter has opened the media on Jellyfin for you.")
    yield f"data: {msg}\n\n"
    msg = _("If the media does not appear on the TV, you can refresh the page for the troubleshooter to try again.")
    yield f"data: {msg}\n\n"
    msg = _("Please proceed to play the media on your TV or return to the main page.")
    yield f"data: {msg}\n\n"
    yield "event: stop\ndata: done\n\n"
    app.jf_automation_counter += 1

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
    src_codec, is_p7, is_atmos = await probe(item_info.get("Path"))
    # Example data
    if errtype == "no_zh_sub":
        response.headers['HX-Redirect'] = "/zh_sub?item_id=" + item_id

    elif errtype == "buffering":
        pass # Will implement later, show networking info
        response.headers['HX-Redirect'] = f"/support{docs_lang}posts/av/networking/buffering"
    elif errtype == "just_player_error" and is_p7 == True:
        pass # Will implement later, show CoreELEC not implemented help
        response.headers['HX-Redirect'] = f"/support{docs_lang}posts/tvbox/coreelec"
    else:
        response.headers['HX-Redirect'] = "/reboot_wait?item_id=" + item_id

@app.get("/zh_sub")
async def zh_sub(request: Request, item_id: Optional[str]):
    item_info = await app.jfclient.get_item(item_id)
    has_zh_sub, display_title = check_zh_sub(item_info.get("MediaStreams"))
    if not has_zh_sub:
        apprise_obj.notify(
            body=f"Jellyfin item does not have Chinese subtitles. URL: {item_info.get('ServerURL')}",
            title="Jellyfin item without Chinese subtitles",
        )
        # await asyncio.sleep(5)
        pass # implement downloading later
    return templates.TemplateResponse("zh_sub.html", {
        "request": request,
        "has_zh_sub": has_zh_sub,
        "display_title": display_title,
        "item_id": item_id,
    })

async def zhsubdl_sse(item_id: Optional[str]):
    item_info = await app.jfclient.get_item(item_id)
    provider_ids = item_info.get("ProviderIds", None)
    tmdb_id = provider_ids.get("Tmdb", None)
    if not tmdb_id:
        msg = _("The media does not have a TMDB ID. Please check the media on Jellyfin.")
        yield f"data: {msg}\n\n"
        yield "event: stop\ndata: done\n\n"
        return
    msg = _("Attempting to download subtitles")
    yield f"data: {msg}\n\n"
    for provider in subtitle_providers:
        logger.info(f"Attempting to download subtitles from {provider.__class__.__name__}")
        try:
            srtfile = provider.subtitle(tmdb_id=tmdb_id)
            if srtfile:
                break
        except Exception as e:
            apprise_obj.notify(body=f"Error downloading subtitles: {e}", title="Subtitle download error")
            if type(e).__name__ == "NoSubtitleFound":
                msg = _("No subtitles found for the media")
                yield f"data: <h3 style='color:red;'>{msg}</h3>\n\n"
                yield "event: stop\ndata: done\n\n"
                return
            else:
                msg = _("An error occurred while downloading subtitles")
                yield f"data: <h3 style='color:red;'>{msg}</h3>\n\n"
                yield "event: stop\ndata: done\n\n"
                return

    await asyncio.sleep(1)
    msg = _("Subtitles downloaded successfully")
    yield f"data: <h3 style='color:green;'>{msg}</h3>\n\n"
    await app.jfclient.upload_subtitle(item_info.get("Id"), srtfile)
    yield f"data: 12312312\n\n"
    yield "event: stop\ndata: done\n\n"

@app.get("/zhsubdl")
async def zhsubdl(request: Request, item_id: Optional[str] = None):
    return StreamingResponse(zhsubdl_sse(item_id), media_type="text/event-stream")



@app.get("/test") # test fastAPI endpoint as standalone functions
async def test(request: Request, response: Response):
    item_id="258ea53c4473b40df5b6d09f679f762b"
    rebooted = await reboot_wait(request, item_id)
    async for result in sse_generator("The Matrix"):
        pass
    response.headers['HX-Redirect'] = "/mediachooser?errtype=bluescreen"

@app.get("/reboot2ce")
async def reboot2ce(request: Request):
    """Reboot to CoreELEC, need to check if USB is inserted before rebooting"""
    logger.info("Simulating rebooting to CoreELEC")
    await app.haclient.adb(entity_id=ha_mp_adb, command="reboot update")
    custom_msg = _("The system has attempted to reboot to CoreELEC. If the system does not reboot, please check if the USB is inserted and try again. Otherwise, you can close this page.")
    return templates.TemplateResponse("partial/custom_help.html", {
        "request": request,
        "custom_msg": custom_msg,
        "event": "reboot2ce"
    })

@app.post('/jfwebhook')
async def data(data: Dict[str, Any]):
    DeviceName = data.get("DeviceName", None)
    if DeviceName.lower().startswith("box r"):
        item_id = data.get("ItemId", None)
        item_data = await app.jfclient.get_item(item_id)
        controller = ReceiverController(avr_host)
        if data.get("NotificationType", None) == "PlaybackStart":
            app.onkyo_check = True
            result = await run_task()
            receiver_ac = AudioCodec(result.get("Input", "dts"),False) # assign the highest AC score to prevent random reboots
            ac, _, _ = await probe(item_data.get("Path"))
        elif data.get("NotificationType", None) == "PlaybackStop":
            app.onkyo_check = False
            ac, receiver_ac = 0, 0
    if receiver_ac < ac and app.onkyo_check == True:
        logger.error(f"Restart box intiated because the receive is playing {receiver_ac} but the media is {ac}.")
        logger.debug(f"The problematic file is {item_data.get('Path')}")
        app.haclient.adb(entity_id=ha_mp_adb, command="reboot")
    return data.get("NotificationType", None)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
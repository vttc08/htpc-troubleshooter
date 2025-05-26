import asyncio
from eiscp import eISCP
from eiscp.core import Receiver
from libs.configuration import *
import logging

logger = logging.getLogger(__name__)
eiscp_logger = logging.getLogger("eiscp")
eiscp_logger.setLevel(logging.WARNING)

class ReceiverController:
    def __init__(self, host, port=60128):
        self.host = host
        self.port = port
        self.eiscp_instance = None
        self.receiver = None

    async def connect(self):
        self.eiscp_instance = eISCP(self.host, self.port)
        self.receiver = Receiver(self.host, self.port)
        logging.info(f"Connecting to Receiver {self.host}:{self.port}")

    async def disconnect(self):
        if self.receiver is not None:
            try:
                self.receiver.disconnect()
            except AttributeError:
                response = await asyncio.to_thread(self.receiver.command, "audio-information query")
                self.receiver.disconnect()
            self.receiver = None
            logging.info(f"Disconnected from Receiver {self.host}:{self.port}")
        else:
            logging.debug(f"Receiver {self.host}:{self.port} is already disconnected")

    def message_received(self, message):
        return message

    async def query_audio_information(self):
        if not self.receiver:
            logging.error("Receiver is not connected.")
        self.receiver.on_message = self.message_received
        response = await asyncio.to_thread(self.receiver.command, "audio-information query")
        keys = ["HDMI", "Input"]
        values = response[1].split(",")
        fmt_response = dict(zip(keys, values))
        fmt_response['debug'] = response[1]
        return fmt_response

    async def query(self):
        done = False
        while not done:
            result = await self.query_audio_information()
            if result.get("Input", "").lower() != "pcm" and result.get("Input", "").lower() != "":
                await self.disconnect()
                done = True
            await asyncio.sleep(1)
        return result

async def run_task():
    controller = ReceiverController(avr_host)
    await controller.connect()
    try:
        result = await asyncio.wait_for(controller.query(), timeout=15)
        logging.info(f"{result}")
    except asyncio.TimeoutError:
        logging.info("Receive input remains PCM after playback.")
        result = await controller.query_audio_information()
    await controller.disconnect()
    return result

if __name__ == "__main__":
    result = asyncio.run(run_task())
    print(result)

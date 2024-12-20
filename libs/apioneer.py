# dannytriago/onkyo-eiscp
import asyncio
# from eiscp import eISCP
# from eiscp.core import Receiver
from fastapi import FastAPI

avr_host = "10.10.120.66"
avr_port = 60128


async def lifespan(app: FastAPI):
    
    # app.eiscp_instance = eISCP(avr_host, avr_port)
    # app.receiver = Receiver(avr_host, avr_port)
    yield
    if app.receiver != None:
        await app.receiver.disconnect()

    

app = FastAPI(lifespan=lifespan)
app.receiver = None

@app.get("/connect")
async def connect():
    app.eiscp_instance = eISCP(avr_host, avr_port)
    app.receiver = Receiver(avr_host, avr_port)
    return {"status": "connected"}

@app.get("/disconnect")
async def disconnect():
    if app.receiver != None:
        try:
            app.receiver.disconnect()
        except AttributeError:
            response = await asyncio.to_thread(app.receiver.command, "audio-information query") # I don't know how to explain this but it works
            app.receiver.disconnect()
        app.receiver = None
        return {"status": "disconnected"}
    else:
        return {"status": "not connected"}

def message_received(message):
    return message

async def query_audio_information(host, port=60128):
    # Initialize the eISCP object
    eiscp_instance = eISCP(host, port)
    
    # Initialize the Receiver object with host and port
    receiver = Receiver(host, port)

    # Set the message received callback
    receiver.on_message = message_received

    # Send the command to query audio information
    response = await asyncio.to_thread(receiver.command, "audio-information query")

    # Return the response
    return response

async def query():
    done = False
    while not done:
        result = await audio()
        if result.get("Input", "").lower() != "pcm":
            await apioneer.disconnect()
            done = True
        await asyncio.sleep(1)
    return result

async def api_query_audio():
    if not app.receiver:
        return {"error": "Not connected to the receiver"}
    app.receiver.on_message = message_received
    response = await asyncio.to_thread(app.receiver.command, "audio-information query")
    # Format the response
    keys = ["HDMI", "Input"]
    values = response[1].split(",")
    fmt_response = dict(zip(keys, values))
    print(fmt_response)
    fmt_response['debug'] = response[1]

    return fmt_response

@app.get("/audio")
async def audio():
    response = await api_query_audio()
    return response

async def run_task():
    await connect()
    try:
        result = await asyncio.wait_for(query(), timeout=3)
    except asyncio.TimeoutError:
        print("Timeout occurred, cancelling the query task...")
        result = await audio()
        await disconnect()
    return result
        

if __name__ == "__main__":
    result = asyncio.run(run_task())
    print(result)
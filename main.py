
import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

load_dotenv()

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")

if not TELNYX_API_KEY:
    raise RuntimeError("Missing TELNYX_API_KEY in .env")

app = FastAPI(title="Jarvis Phone System")

TELNYX_API_URL = "https://api.telnyx.com/v2"


def telnyx_command(call_control_id, action, body=None):
    url = f"{TELNYX_API_URL}/calls/{call_control_id}/actions/{action}"

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {TELNYX_API_KEY}",
            "Content-Type": "application/json"
        },
        json=body or {},
        timeout=10
    )

    print(f"TELNYX {action.upper()} RESPONSE:", response.status_code)
    print(response.text)

    response.raise_for_status()
    return response.json()


@app.get("/")
def home():
    return {"status": "Jarvis phone server online"}


@app.post("/")
@app.post("/webhook")
async def telnyx_webhook(request: Request):
    event = await request.json()

    data = event.get("data", {})
    event_type = data.get("event_type")
    payload = data.get("payload", {})

    call_control_id = payload.get("call_control_id")

    print("\nTELNYX EVENT:", event_type)

    if not call_control_id:
        return JSONResponse({"received": True})

    try:
        if event_type == "call.initiated":
            if payload.get("direction") == "incoming":
                print("JARVIS IS ANSWERING THE CALL")
                telnyx_command(call_control_id, "answer")

        elif event_type == "call.answered":
            print("JARVIS IS SPEAKING")

            telnyx_command(
                call_control_id,
                "speak",
                {
                    "payload": "Hello. Jarvis systems are online. How can I help you?",
                    "payload_type": "text",
                    "voice": "female",
                    "language": "en-US"
                }
            )

        elif event_type == "call.hangup":
            print("CALL ENDED")

    except Exception as error:
        print("CALL CONTROL ERROR:", str(error))

    return JSONResponse({"received": True})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

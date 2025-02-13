import asyncio
import json
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx

class Setting(BaseModel):
    label: str
    type: str
    required: bool
    default: str


class MonitorPayload(BaseModel):
    channel_id: str
    return_url: str
    settings: List[Setting]


app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://staging.telextest.im", "http://telextest.im", "https://staging.telex.im", "https://telex.im"], # NB: telextest is a local url
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

@app.get("/logo")
def get_logo():
    return FileResponse("uptime.png")

@app.get("/integration.json")
def get_integration_json(request: Request):
    base_url = str(request.base_url).rstrip("/")

    integration_json = {
        "data": {
            "date": {"created_at": "2025-02-09", "updated_at": "2025-02-09"},
            "descriptions": {
                "app_name": "Uptime Monitor",
                "app_description": "A local uptime monitor",
                "app_logo": "https://i.imgur.com/lZqvffp.png",
                "app_url": base_url,
                "background_color": "#fff",
            },
            "is_active": False,
            "integration_type": "interval",
            "key_features": ["- monitors websites"],
            "category": "Monitoring",
            "author": "Osinachi Chukwujama",
            "website": base_url,
            "settings": [
                {"label": "site-1", "type": "text", "required": True, "default": ""},
                {"label": "site-2", "type": "text", "required": True, "default": ""},
                {
                    "label": "interval",
                    "type": "text",
                    "required": True,
                    "default": "* * * * *",
                },
            ],
            "target_url": "",
            "tick_url": f"{base_url}/tick"
        }
    }

    return integration_json




async def check_site_status(site: str, max_retries: int = 3, timeout: float = 10.0) -> Optional[str]:
    transport = httpx.AsyncHTTPTransport(retries=max_retries)

    # Configure client with retry transport
    async with httpx.AsyncClient(
        transport=transport,
        timeout=timeout,
        follow_redirects=True
    ) as client:
        try:
            response = await client.get(site)
            
            # Check if response indicates success
            if 200 <= response.status_code < 400:
                return None  # Site is up
                
            return f"Site {site} is down (HTTP {response.status_code})"
            
        except httpx.TimeoutException:
            return f"Site {site} timed out after {timeout} seconds"
            
        except httpx.HTTPError as e:
            return f"Site {site} is down (HTTP Error: {str(e)})"
            
        except httpx.TransportError as e:
            return f"Site {site} is down (Transport Error: {str(e)})"
            
        except Exception as e:
            return f"Site {site} is down (Unexpected Error: {str(e)})"


async def monitor_task(payload: MonitorPayload):
    """Background task to monitor sites and send results."""
    sites = []

    for setting in payload.settings:
        if setting.label.startswith("site"):
            sites.append(setting.default)

    results = await asyncio.gather(*(check_site_status(site) for site in sites))

    results = "\n".join([res for res in results if isinstance(res, str)])
    
    telex_format = {
        "message": results, 
        "username": "Uptime Monitor", 
        "event_name": "Uptime Check", 
        "status": "error"
    }

    headers = {"Content-Type": "application/json"}

    print(payload)
    if results:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                payload.return_url, json=telex_format, headers=headers
            )


@app.post("/tick", status_code=202)
def monitor(payload: MonitorPayload, background_tasks: BackgroundTasks):
    """Immediately returns 202 and runs monitoring in the background."""
    background_tasks.add_task(monitor_task, payload)
    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

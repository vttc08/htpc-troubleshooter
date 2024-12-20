import logging
import httpx
from homeassistant_api import State

logger = logging.getLogger(__name__)
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)
httpcore_logger = logging.getLogger("httpcore")
httpcore_logger.setLevel(logging.WARNING)

class HASync():
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self.client = httpx.AsyncClient(headers={"Authorization": f"Bearer {self.token}"})
    def __aenter__(self):
        return self
    async def async_trigger_service(self, domain: str, service: str, **kwargs):
        response = await self.client.post(f"{self.url}/services/{domain}/{service}", json=kwargs)
        return State(**response.json())
    async def async_get_state(self, entity_id: str):
        response = await self.client.get(f"{self.url}/states/{entity_id}")
        return State(**response.json())
    
    def decorator_dev_must_be_on(func):
        async def wrapper(self, *args, **kwargs):
            dev_state = await self.async_get_state(entity_id=kwargs.get("entity_id"))
            if dev_state.state == "off":
                try:
                    await self.async_trigger_service(service="turn_on", *args, **kwargs)
                except Exception as e:
                    logger.warning(f"The device {dev_state.entity_id} is not turned on and cannot be turned on. {e}")
                return await func(self, *args, **kwargs)
            return await func(self, *args, **kwargs)
        return wrapper
    @decorator_dev_must_be_on
    async def async_trigger_service_check(self, domain: str, service: str, **kwargs):
        response = await self.client.post(f"{self.url}/services/{domain}/{service}", json=kwargs)
        return State(**response.json())
    @decorator_dev_must_be_on
    async def async_get_state_check(self, domain: str, entity_id: str):
        response = await self.client.get(f"{self.url}/states/{entity_id}")
        return State(**response.json())
            
    async def close(self):
        await self.client.aclose()
import httpx

from core.settings import settings


class TermiiClient:
    def __init__(self):
        self.base_url = settings.TERMII_BASE_URL
        self.api_key = settings.TERMII_API_KEY
        self.async_client: httpx.AsyncClient | None = None
        self.sync_client: httpx.Client | None = None

    def sync_connect(self):
        self.sync_client = httpx.Client(
            base_url=self.base_url,
            timeout=10,
        )

    def sync_close(self):
        if self.sync_client:
            self.sync_client.close()

    async def async_connect(self):
        self.async_client = await httpx.AsyncClient(base_url=self.base_url, timeout=10)

    async def async_close(self):
        if self.async_client:
            await self.async_client.aclose()

    async def ping(self):
        if not self.async_client:
            raise RuntimeError("Termii client not connected")

        try:
            test_payload = {
                "to": "2340000000000",
                "from": settings.TERMII_SENDER_ID,
                "sms": "Ping test",
                "type": "plain",
                "channel": "generic",
                "api_key": self.api_key,
            }
            response = await self.async_client.post("/api/sms/send", json=test_payload)
            if response.status_code == 200:
                print("Termii API ping successful!")
                return True
            else:
                print(
                    f"Termii API ping returned {response.status_code}:",
                    response.json(),
                )
                return False
        except Exception as e:
            print("Termii ping error:", e)
            return False

    def normalize_phone(self, phone: str):
        phone = phone.strip()

        if phone.startswith("0"):
            phone = "234" + phone[1:]

        if phone.startswith("+234"):
            phone = phone.replace("+", "")

        return phone

    def send_otp_sms(
        self,
        to: str,
        otp: str | None = None,
        message: str | None = None,
        name: str | None = None,
        sender_id=settings.TERMII_SENDER_ID,
    ):
        try:
            self.sync_connect()
            if not message:
                if name:
                    message = (
                        f"Hello {name}, your OTP is {otp}. "
                        "This code expires in 5 minutes. Do not share it with anyone."
                    )
                else:
                    message = (
                        f"Your OTP is {otp}. "
                        "This code expires in 5 minutes. Do not share it with anyone."
                    )

            payload = {
                "to": self.normalize_phone(to),
                "from": sender_id,
                "sms": message,
                "type": "plain",
                "channel": "generic",
                "api_key": self.api_key,
            }

            if not self.sync_client:
                raise RuntimeError("Termii client not connected")

            response = self.sync_client.post("/api/sms/send", json=payload)
            if response.status_code != 200:

                return {
                    "error": f"Termii error {response.status_code}: {response.text}"
                }
            return response.json()
        finally:
            self.sync_close()
send_sms=TermiiClient()
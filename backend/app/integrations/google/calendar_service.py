from datetime import datetime, timedelta, timezone
from app.integrations.google.calendar_client import GoogleCalendarClient


class CalendarService:
    def __init__(self, access_token: str):
        self.client = GoogleCalendarClient(access_token)

    @staticmethod
    def _overlaps(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
        return max(start_a, start_b) < min(end_a, end_b)

    async def get_available_slots(
        self,
        participants_emails: list[str],
        start_time: datetime,
        end_time: datetime,
        slot_minutes: int = 30,
    ) -> list[dict[str, str]]:
        freebusy = await self.client.freebusy(
            participants_emails=participants_emails,
            start_time_iso=start_time.astimezone(timezone.utc).isoformat(),
            end_time_iso=end_time.astimezone(timezone.utc).isoformat(),
        )

        busy_windows: list[tuple[datetime, datetime]] = []
        for calendar in freebusy.get("calendars", {}).values():
            for busy in calendar.get("busy", []):
                busy_start = datetime.fromisoformat(busy["start"].replace("Z", "+00:00"))
                busy_end = datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))
                busy_windows.append((busy_start, busy_end))

        slot_delta = timedelta(minutes=slot_minutes)
        cursor = start_time.astimezone(timezone.utc)
        final = end_time.astimezone(timezone.utc)
        slots: list[dict[str, str]] = []

        while cursor + slot_delta <= final:
            candidate_end = cursor + slot_delta
            if not any(self._overlaps(cursor, candidate_end, busy_start, busy_end) for busy_start, busy_end in busy_windows):
                slots.append({"start": cursor.isoformat(), "end": candidate_end.isoformat()})
            cursor = candidate_end

        return slots

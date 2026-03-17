import asyncio
from uuid import uuid4
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.config import get_settings

settings = get_settings()


class GoogleCalendarAuthError(Exception):
    pass


class GoogleCalendarAPIError(Exception):
    pass


class GoogleCalendarClient:
    def __init__(self, access_token: str):
        # Accept comma or whitespace-delimited scope strings from environment configuration.
        scopes = [
            scope.strip()
            for scope in settings.GOOGLE_CALENDAR_SCOPES.replace(",", " ").split()
            if scope.strip()
        ]
        credentials = Credentials(token=access_token, scopes=scopes)
        self.service = build("calendar", "v3", credentials=credentials, cache_discovery=False)

    async def freebusy(self, participants_emails: list[str], start_time_iso: str, end_time_iso: str) -> dict:
        body = {
            "timeMin": start_time_iso,
            "timeMax": end_time_iso,
            "items": [{"id": email} for email in participants_emails],
        }
        try:
            return await asyncio.to_thread(
                self.service.freebusy().query(body=body).execute,
            )
        except HttpError as exc:
            if exc.resp.status in {401, 403}:
                raise GoogleCalendarAuthError("Google calendar authorization failed") from exc
            if exc.resp.status == 429:
                raise GoogleCalendarAPIError("Google calendar rate limit exceeded") from exc
            raise GoogleCalendarAPIError("Google calendar freebusy request failed") from exc
        except Exception as exc:
            raise GoogleCalendarAPIError("Network or Google API failure") from exc

    async def create_event(
        self,
        title: str,
        description: str | None,
        start_time_iso: str,
        end_time_iso: str,
        participants: list[str],
    ) -> dict:
        event = {
            "summary": title,
            "description": description or "",
            "start": {"dateTime": start_time_iso},
            "end": {"dateTime": end_time_iso},
            "attendees": [{"email": email} for email in participants],
            "conferenceData": {
                "createRequest": {
                    "requestId": str(uuid4()),
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
        }

        try:
            return await asyncio.to_thread(
                self.service.events()
                .insert(
                    calendarId="primary",
                    body=event,
                    conferenceDataVersion=1,
                    sendUpdates="all",
                )
                .execute,
            )
        except HttpError as exc:
            if exc.resp.status in {401, 403}:
                raise GoogleCalendarAuthError("Google calendar authorization failed") from exc
            if exc.resp.status == 429:
                raise GoogleCalendarAPIError("Google calendar rate limit exceeded") from exc
            raise GoogleCalendarAPIError("Google calendar create event failed") from exc
        except Exception as exc:
            raise GoogleCalendarAPIError("Network or Google API failure") from exc

    async def update_event(
        self,
        google_event_id: str,
        title: str | None,
        description: str | None,
        start_time_iso: str | None,
        end_time_iso: str | None,
        participants: list[str] | None,
    ) -> dict:
        try:
            current_event = await asyncio.to_thread(
                self.service.events().get(calendarId="primary", eventId=google_event_id).execute,
            )
            if title is not None:
                current_event["summary"] = title
            if description is not None:
                current_event["description"] = description
            if start_time_iso is not None:
                current_event["start"] = {"dateTime": start_time_iso}
            if end_time_iso is not None:
                current_event["end"] = {"dateTime": end_time_iso}
            if participants is not None:
                current_event["attendees"] = [{"email": email} for email in participants]

            return await asyncio.to_thread(
                self.service.events()
                .update(
                    calendarId="primary",
                    eventId=google_event_id,
                    body=current_event,
                    conferenceDataVersion=1,
                    sendUpdates="all",
                )
                .execute,
            )
        except HttpError as exc:
            if exc.resp.status in {401, 403}:
                raise GoogleCalendarAuthError("Google calendar authorization failed") from exc
            if exc.resp.status == 404:
                raise GoogleCalendarAPIError("Google calendar event not found") from exc
            if exc.resp.status == 429:
                raise GoogleCalendarAPIError("Google calendar rate limit exceeded") from exc
            raise GoogleCalendarAPIError("Google calendar update event failed") from exc
        except Exception as exc:
            raise GoogleCalendarAPIError("Network or Google API failure") from exc

    async def delete_event(self, google_event_id: str) -> None:
        try:
            await asyncio.to_thread(
                self.service.events().delete(calendarId="primary", eventId=google_event_id, sendUpdates="all").execute,
            )
        except HttpError as exc:
            if exc.resp.status in {401, 403}:
                raise GoogleCalendarAuthError("Google calendar authorization failed") from exc
            if exc.resp.status == 404:
                return
            if exc.resp.status == 429:
                raise GoogleCalendarAPIError("Google calendar rate limit exceeded") from exc
            raise GoogleCalendarAPIError("Google calendar delete event failed") from exc
        except Exception as exc:
            raise GoogleCalendarAPIError("Network or Google API failure") from exc

    async def get_event(self, google_event_id: str) -> dict:
        try:
            return await asyncio.to_thread(
                self.service.events().get(calendarId="primary", eventId=google_event_id).execute,
            )
        except HttpError as exc:
            if exc.resp.status in {401, 403}:
                raise GoogleCalendarAuthError("Google calendar authorization failed") from exc
            if exc.resp.status == 404:
                raise GoogleCalendarAPIError("Google calendar event not found") from exc
            if exc.resp.status == 429:
                raise GoogleCalendarAPIError("Google calendar rate limit exceeded") from exc
            raise GoogleCalendarAPIError("Google calendar get event failed") from exc
        except Exception as exc:
            raise GoogleCalendarAPIError("Network or Google API failure") from exc

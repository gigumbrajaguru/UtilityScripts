from datetime import datetime
import re
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

chrome_options = Options()
chrome_options.headless = True
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--dns-prefetch-disable")


class _GoogleConnect:
    def __init__(self):
        __SCOPES = ["https://www.googleapis.com/auth/calendar"]
        __CLIENT_SECRET_FILE = "important/caledareventsmanagement.json"
        __API_VERSION = "v3"
        __API_NAME = "calendar"
        self.credentials = service_account.Credentials.from_service_account_file(
            filename=__CLIENT_SECRET_FILE, scopes=__SCOPES
        )
        self.service = build(__API_NAME, __API_VERSION, credentials=self.credentials)


class EventHandle:
    def __init__(self):
        self._obj_calendar = _GoogleConnect()
        _calendar_list = self._obj_calendar.service.calendarList().list().execute()
        self.items = _calendar_list.get("items", [])
        if not self.items:
            self.get_calendar_id = self.insert_calendar()
        else:
            self.get_calendar_id = [
                item["id"] for item in self.items if item["summary"] == "Electricity"
            ]

    def insert_calendar(
        self, calendar_name="initiated", time_zone="America/Los_Angeles"
    ):
        calendar = {"summary": calendar_name, "timeZone": time_zone}
        created_calendar = (
            self._obj_calendar.service.calendars().insert(body=calendar).execute()
        )
        self.insert_rules(created_calendar["id"])

        return created_calendar["id"]

    def insert_rules(
        self,
        calendar_id=None,
        type_role="user",
        email="gigumbrajaguru@gmail.com",
        role="owner",
    ):
        role_permission = (
            True if role == "owner" and email == "gigumbrajaguru@gmail.com" else False
        )
        if calendar_id and role_permission:
            rule = {
                "scope": {
                    "type": type_role,
                    "value": email,
                },
                "role": role,
            }
            self._obj_calendar.service.acl().insert(
                calendarId=calendar_id, body=rule
            ).execute()

    def make_time(self, input_time: str) -> str:
        time_input = datetime.strptime(input_time, "%I:%M %p")
        return datetime.strftime(time_input, "%H:%M:%S")

    def create_event(self, summary="power_drop"):
        event_list = []
        time_slots = ScrapCEB().get_time_slot()
        for index, time_slot in enumerate(time_slots, start=1):
            start_time, end_time = time_slot.split(" - ")
            start_time = re.sub(r"(\d+)([ap]m)", r"\1 \2", start_time)
            start_time = self.make_time(start_time)
            end_time = re.sub(r"(\d+)([ap]m)", r"\1 \2", end_time)
            end_time = self.make_time(end_time)
            date_time = datetime.now()
            start_time = f'{date_time.strftime("%Y-%m-%d")}T{start_time}+05:30'
            end_time = f'{date_time.strftime("%Y-%m-%d")}T{end_time}+05:30'
            event = {
                "summary": f"Power Drop {index}",
                "start": {
                    "dateTime": start_time,
                    "timeZone": "Asia/Colombo",
                },
                "end": {
                    "dateTime": end_time,
                    "timeZone": "Asia/Colombo",
                },
            }
            event = (
                self._obj_calendar.service.events()
                .insert(calendarId=self.get_calendar_id[0], body=event)
                .execute()
            )
            event_list.append(event["id"])
        return event_list


class ScrapCEB:
    def __init__(self):
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            chrome_options=chrome_options,
        )
        self.time_slot_list = []
        view_location = "https://cebcare.ceb.lk/Incognito/DemandMgmtSchedule"
        try:
            driver.get(view_location)
        except TimeoutException as ex:
            print(ex)
            driver.refresh()
            driver.close()
            driver.quit()
        time.sleep(5)
        elements = driver.find_elements(
            By.CSS_SELECTOR, "a.fc-time-grid-event .fc-content"
        )
        for element in elements:
            title_item = element.find_element(By.CSS_SELECTOR, ".fc-title")
            if title_item.get_attribute("innerText") == "R":
                time_slot = element.find_element(
                    By.CSS_SELECTOR, ".fc-time"
                ).get_attribute("data-full")
                self.time_slot_list.append(time_slot)
        driver.close()
        driver.quit()

    def get_time_slot(self):
        return self.time_slot_list

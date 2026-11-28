"""Unit tests for the Garbage Calendar plugin, against a fake Domoticz.

Run from the repository root:  python3 -m unittest discover -s tests -v
No extra packages are needed. The plugin is copied to a temporary folder
for each test, because it writes config.txt and its cache next to plugin.py.
"""
import builtins
import datetime
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(TESTS_DIR)
sys.path.insert(0, TESTS_DIR)

import Domoticz  # noqa: E402  (the fake module in this folder)

TODAY = datetime.date.today()


def load_plugin(folder):
    spec = importlib.util.spec_from_file_location("garbage_plugin", os.path.join(folder, "plugin.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ddmmyyyy(days_from_today):
    d = TODAY + datetime.timedelta(days=days_from_today)
    return f"{d.day:02d}-{d.month:02d}-{d.year}"


class PluginTestCase(unittest.TestCase):

    def setUp(self):
        Domoticz.reset()
        self.folder = tempfile.mkdtemp()
        for name in ("plugin.py", "config.example.txt", "Garbage.zip"):
            shutil.copy(os.path.join(REPO_DIR, name), self.folder)
        self.csv = os.path.join(self.folder, "calendar.csv")
        self.write_csv([(0, "GFT"), (1, "PMD"), (1, "Papier"), (5, "Restafval")])
        builtins.Parameters = {
            "Provider": "15", "ExtraValue": self.csv, "Zipcode": "1234AB", "HouseNumber": "5",
            "Suffix": "", "Notification": "true", "EnableDebug": "false", "HardwareID": "3",
        }
        self.plugin = load_plugin(self.folder)
        self.p = self.plugin._plugin

    def tearDown(self):
        self.plugin.onStop()
        shutil.rmtree(self.folder, ignore_errors=True)

    def write_csv(self, rows):
        with open(self.csv, "w", encoding="utf-8") as fh:
            for offset, waste in rows:
                fh.write(f"{ddmmyyyy(offset)};{waste}\n")

    def start(self):
        self.plugin.onStart()
        self.p._thread.join(5)
        self.plugin.onHeartbeat()


class StartAndDevicesTest(PluginTestCase):

    def test_config_created_from_example(self):
        self.start()
        self.assertTrue(os.path.isfile(os.path.join(self.folder, "config.txt")))
        self.assertEqual(self.p._label_today, "Vandaag")
        self.assertEqual(self.p._today_to_min, 14 * 60)

    def test_calendar_device(self):
        self.start()
        text = Devices[1].sValue
        self.assertIn("Vandaag", text)
        self.assertIn("Morgen", text)
        self.assertIn("GFT", text)
        self.assertNotIn("<img", text)
        self.assertEqual(Devices[1].Image, 7)

    def test_fetch_thread_never_touches_devices(self):
        self.start()
        self.assertEqual(Domoticz.OFF_THREAD, [])

    def test_cache_written_on_main_thread(self):
        self.plugin.onStart()
        self.p._thread.join(5)
        self.assertFalse(os.path.exists(self.p._cache_file))  # not by the fetch thread
        self.plugin.onHeartbeat()
        with open(self.p._cache_file, encoding="utf-8") as fh:
            cache = json.load(fh)
        self.assertEqual(len(cache["results"]), 4)
        self.assertTrue(all(set(r) == {"type", "date"} for r in cache["results"]))

    def test_cache_restored_when_provider_fails(self):
        self.start()
        self.plugin.onStop()
        os.remove(self.csv)   # provider now "unreachable"
        Domoticz.reset()
        plugin2 = load_plugin(self.folder)
        plugin2.onStart()
        plugin2._plugin._thread.join(5)
        plugin2.onHeartbeat()
        self.assertIn("GFT", Devices[1].sValue)
        plugin2.onStop()

    def test_old_cache_with_icon_url_still_loads(self):
        self.plugin.onStart()
        self.p._thread.join(5)
        with open(self.p._cache_file, "w", encoding="utf-8") as fh:
            json.dump({"key": self.p._cache_key, "notify_sent": "",
                       "results": [{"type": "GFT", "date": TODAY.isoformat(), "icon_url": "https://x/y.png"}]}, fh)
        self.p._load_cache()
        self.assertEqual(self.p._cached_results, [{"type": "GFT", "date": TODAY}])


class ContainerAndNotificationTest(PluginTestCase):

    def test_two_types_tomorrow_are_combined(self):
        self.write_csv([(1, "PMD"), (1, "Papier")])
        self.start()
        self.p._tomorrow_until_min = 0
        self.plugin.onHeartbeat()
        self.assertIn("PMD + Papier", Devices[2].sValue)

    def test_notification_sent_once_per_day(self):
        self.start()
        self.p._notify_time_min = 0
        self.plugin.onHeartbeat()
        self.plugin.onHeartbeat()
        self.assertEqual(len(Domoticz.NOTIFICATIONS), 1)
        self.assertEqual(Domoticz.NOTIFICATIONS[0]["Subject"], "Vandaag: GFT")


class HelperTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Domoticz.reset()
        cls.folder = tempfile.mkdtemp()
        shutil.copy(os.path.join(REPO_DIR, "plugin.py"), cls.folder)
        cls.m = load_plugin(cls.folder)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.folder, ignore_errors=True)

    def test_format_date(self):
        self.assertEqual(self.m.format_date(datetime.date(2026, 11, 24)), "di 24 nov")

    def test_month_names(self):
        for name, month in (("nov", 11), ("november", 11), ("maart", 3), ("mrt", 3), ("Mei.", 5)):
            self.assertEqual(self.m.month_from_name(name), month, name)

    def test_parse_dutch_date(self):
        year = TODAY.year + 1
        self.assertEqual(self.m.parse_dutch_date(f"25 november {year}"), datetime.date(year, 11, 25))
        d = self.m.parse_dutch_date("dinsdag 25 november")
        self.assertEqual((d.month, d.day), (11, 25))
        self.assertGreaterEqual(d, TODAY)

    def test_type_alias(self):
        self.assertEqual(self.m.apply_type_alias("Groente-, fruit- en tuinafval"), "GFT")
        self.assertEqual(self.m.apply_type_alias("Plastic, metaal en drankkartons"), "PMD")
        self.assertEqual(self.m.apply_type_alias("Oud papier en karton"), "Papier")
        self.assertEqual(self.m.apply_type_alias("Drankkartons"), "PMD")
        self.assertEqual(self.m.apply_type_alias("Iets anders"), "Iets anders")

    def test_url_for_log_hides_address_and_query(self):
        self.m.set_log_redact_values("1234AB", "5")
        logged = self.m.url_for_log("https://host/nl/1234AB/5?apikey=secret")
        self.assertNotIn("1234AB", logged)
        self.assertNotIn("secret", logged)
        self.assertTrue(logged.startswith("https://host/nl/"))

    def test_redact_url(self):
        self.m.set_log_redact_values()
        self.assertEqual(self.m.redact_url("https://h/p?postcode=1234AB&x=1"), "https://h/p?postcode=***&x=1")

    def test_pick_opzet_bag_id(self):
        records = [{"bagId": "1", "huisletter": "A"}, {"bagId": "2"}, {"bagId": "3", "toevoeging": "bis"}]
        self.assertEqual(self.m.pick_opzet_bag_id(records, ""), ("2", True))
        self.assertEqual(self.m.pick_opzet_bag_id(records, "a"), ("1", True))
        self.assertEqual(self.m.pick_opzet_bag_id(records, "BIS"), ("3", True))
        self.assertEqual(self.m.pick_opzet_bag_id(records, "Z"), ("1", False))

    def test_parse_ical_events(self):
        d = TODAY + datetime.timedelta(days=3)
        ical = ("BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nDTSTART;VALUE=DATE:" + d.strftime("%Y%m%d") +
                "\r\nSUMMARY:GFT\r\n  inzameling\r\nEND:VEVENT\r\nBEGIN:VEVENT\r\nDTSTART:20000101\r\n"
                "SUMMARY:Oud\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n")
        events = self.m.parse_ical_events(ical, TODAY, strip_suffix=r"\s+inzameling")
        self.assertEqual(events, [{"type": "GFT", "date": d}])

    def test_opzet_api_without_icons(self):
        day = (TODAY + datetime.timedelta(days=2)).isoformat()

        def fake_get(url, headers=None, timeout=0):
            if "/rest/adressen/1234AB-5" in url:
                return json.dumps([{"bagId": "0123"}])
            if url.endswith("/afvalstromen"):
                return json.dumps([{"id": 1, "title": "GFT", "icon": "/gft.png"}])
            if url.endswith(f"/kalender/{TODAY.year}"):
                return json.dumps([{"afvalstroom_id": 1, "ophaaldatum": day}])
            return ""

        original = self.m.http_get
        self.m.http_get = fake_get
        try:
            result = self.m.OpzetApiModule().fetch("1234AB", "5", "", "host.example")
        finally:
            self.m.http_get = original
        self.assertEqual(result, [{"type": "GFT", "date": TODAY + datetime.timedelta(days=2)}])

    def test_every_provider_is_registered(self):
        self.assertEqual(sorted(self.m.MODULES, key=int), [str(i) for i in range(1, 19)])


if __name__ == "__main__":
    unittest.main()

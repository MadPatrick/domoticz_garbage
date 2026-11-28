# Domoticz Garbage Calendar Plugin

A Domoticz Python plugin that retrieves your garbage/waste collection schedule and displays upcoming pickup dates in a Domoticz Text device.  
Supports 18 different waste-collection data sources used in the Netherlands and Belgium.

**Originaly based on the LUA script made by JvdZ

https://forum.domoticz.com/viewtopic.php?t=31295**

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Plugin parameters](#plugin-parameters)
  - [config.txt settings](#configtxt-settings)
  - [Module-specific notes](#module-specific-notes)
- [Supported modules](#supported-modules)
- [Waste types](#waste-types)
- [Notification device](#notification-device)
- [Troubleshooting](#troubleshooting)

---

## Requirements

- [Domoticz](https://www.domoticz.com/) with Python plugin support enabled  
- Python 3.6 or higher  
- Module **9 (omrin)** additionally requires the `cryptography` Python package:
  ```
  pip install cryptography
  ```

---

## Installation

1. Clone the repository into the plugins directory of your Domoticz installation:
   ```bash
   cd <domoticz>/plugins
   git clone https://github.com/MadPatrick/domoticz_garbage GarbageCalendar
   ```
   Without git, copy `plugin.py`, `Garbage.zip` (the icons) and `config.example.txt` into `<domoticz>/plugins/GarbageCalendar/`.
2. Update later with `git pull` in that directory. Your settings in `config.txt` are not part of the repository, so they are kept.
3. Restart Domoticz:
   ```bash
   sudo systemctl restart domoticz
   ```
4. In the Domoticz web interface go to **Setup → Hardware**, click **Add**, and choose **GarbageCalendar** from the type list.
5. Fill in the parameters (see [Configuration](#configuration)) and click **Add**.

Domoticz will create two **Text** devices (Domoticz puts the hardware name in front, e.g. `Garbage - Calendar`):

| Device name | Description |
|---|---|
| **Calendar** | Shows the next upcoming pickup dates |
| **Container** | Shows a "Today / Tomorrow" reminder (see [Notification device](#notification-device)) |

The last successfully fetched calendar is stored in `gc_cache_<hardware id>.json` in the plugin folder, so the devices keep showing data after a restart even when the provider is temporarily unreachable.

---

## Configuration

### Plugin parameters

These parameters are set in the Domoticz hardware setup UI:

| Label | Description | Default |
|---|---|---|
| **Provider** | Data source / waste provider (see [Supported modules](#supported-modules)) | `2` |
| **Extra** | Provider-specific extra value (see [Module-specific notes](#module-specific-notes)) | *(empty)* |
| **Zipcode** | Your postal code (e.g. `1234AB`) | *(empty)* |
| **House number** | House number | *(empty)* |
| **Suffix** | House number addition (e.g. `A`, `bis`) | *(empty)* |
| **Notification** | Send a push/e-mail notification on pickup days (`Yes` / `No`) | `No` |
| **Debug logging** | Extra log output for troubleshooting | off |

### config.txt settings

Advanced settings are configured by editing `config.txt` in the plugin directory. On the first start the plugin creates it from `config.example.txt`.

> **Updating from 1.3.x:** `config.txt` used to be in the repository. If you changed it, `git pull` stops with *"local changes would be overwritten"*. Keep your settings like this:
> ```bash
> cp config.txt config.txt.bak && git checkout config.txt && git pull && mv config.txt.bak config.txt
> ```

The plugin re-reads this file on every restart (no Domoticz restart required — just restart the plugin via **Setup → Hardware**).

| Key | Description | Default |
|---|---|---|
| `UpdateTime` | Time of day to refresh the schedule (HH:MM) | `02:30` |
| `ShowEvents` | Number of upcoming pickups to display | `3` |
| `TodayTime` | Until what time the "Today" label is shown (HH:MM) | `14:00` |
| `TomorrowTime` | From what time the "Tomorrow" label is shown (HH:MM) | `16:00` |
| `NotifyTime` | Time at which the notification is sent on the pickup day or the day before (HH:MM) | `07:00` |
| `NotifyLevel` | Priority of the notification (`-2`=very low … `2`=emergency) | `1` |
| `NotifySubSystem` | Send only via this notification subsystem (e.g. `telegram`); empty = all | *(empty)* |
| `LabelToday` | Label used when the pickup is today | `Today` |
| `LabelTomorrow` | Label used when the pickup is tomorrow | `Tomorrow` |
| `LabelNoData` | Text shown when no upcoming pickup data is available | `No collection data available` |

> **Note:** Enabling or disabling notifications is done via the **Notification** dropdown in the Domoticz hardware configuration panel, not in `config.txt`.
Pickup dates are always displayed in the format **`wd dd mmm`** (e.g. `ma 07 apr`).

### Module-specific notes

| Module | Extra field value |
|---|---|
| `1` – mijnafvalwijzer (HTML) | *(optional)* Custom hostname (default: `www.mijnafvalwijzer.nl`) |
| `2` – mijnafvalwijzer_api | *(optional)* Custom API hostname (default: `api.mijnafvalwijzer.nl`) |
| `3` – ximmio | **Required.** Company code. Open your municipality's website, press F12, search `controller.js` for `companyCode`. |
| `6` – opzet (iCal) | **Required.** Hostname (e.g. `inzamelkalender.hvcgroep.nl`) |
| `7` – opzet_api | **Required.** Hostname |
| `18` – hvc_api | Leave empty (uses `inzamelkalender.hvcgroep.nl`) |
| `8` – recycleapp-be | **Required.** Street name |
| `10` – burgerportaal | **Required.** BPName: `assen`, `bar`, or `rmn` |
| `15` – csv_file | **Required.** Full path to the local CSV file |
| `16` – afvalinfo | **Required.** Municipality name (e.g. `sliedrecht`, `papendrecht`) |
| `17` – reinis | **Required (one-time).** Calendar link: open reinis.nl/kalender, enter your address, click **Toevoegen aan agenda** → **Link kopiëren** and paste the link here. The link does not expire. |
| All others | Leave **Extra** empty |

---

## Supported modules

| # | Name | Method | Country |
|---|---|---|---|
| 1 | mijnafvalwijzer | HTML scraping | 🇳🇱 NL |
| 2 | mijnafvalwijzer_api | JSON API | 🇳🇱 NL |
| 3 | ximmio | Ximmio waste API | 🇳🇱 NL |
| 4 | rova_api | Rova waste API | 🇳🇱 NL |
| 5 | rd4_api | RD4 waste API | 🇳🇱 NL |
| 6 | opzet | Opzet iCal | 🇳🇱 NL |
| 7 | opzet_api | Opzet REST API | 🇳🇱 NL |
| 8 | recycleapp-be | RecycleApp REST API | 🇧🇪 BE |
| 9 | omrin | Omrin API (requires `cryptography`) | 🇳🇱 NL |
| 10 | burgerportaal | Firebase-based portal | 🇳🇱 NL |
| 11 | rmn | RMN via burgerportaal (kept for existing setups; for new ones use 10 with `rmn`) | 🇳🇱 NL |
| 12 | deafvalapp | De Afval App | 🇳🇱 NL |
| 13 | zuidlimburg | ZuidLimburg HTML scraping | 🇳🇱 NL |
| 14 | montferland | Montferland REST API | 🇳🇱 NL |
| 15 | csv_file | Local CSV file | Any |
| 16 | afvalinfo | afvalinfo.nl via trashapi | 🇳🇱 NL |
| 17 | reinis | reinis.nl address lookup + iCal feed | 🇳🇱 NL |
| 18 | hvc_api | HVC Groep inzamelkalender (Opzet engine) | 🇳🇱 NL |

---

## Waste types

The plugin normalises raw waste type names from the provider into standard display names and renders them with a colour-coded HTML label in the Domoticz Text device:

| Display name | Colour | Includes |
|---|---|---|
| **GFT** | 🟢 Green | groente, gft |
| **Papier** | 🔵 Blue | papier, oud papier, karton |
| **Restafval** | ⚫ Grey | restafval |
| **PMD** | 🟠 Orange | pmd, plastic |
| **Glas** | 🔵 Cyan | glas |
| **Textiel** | 🟣 Purple | textiel |
| **Kerstbomen** | 🟢 Dark green | kerstbomen |

Unknown waste types are displayed as-is.

---

## Notification device

The plugin automatically creates a second Text device called **"Container"** that shows a short reminder. When several types are collected on the same day they are combined, e.g. `Tomorrow : GFT + PMD`.

| Situation | Text shown |
|---|---|
| Collection day, before `TodayTime` | `<LabelToday> <type>` (e.g. `Today Restafval`) |
| Day before collection, from `TomorrowTime` | `<LabelTomorrow> <type>` (e.g. `Tomorrow PMD`) |
| Outside these windows | *(empty)* |

The reminder times and labels can be adjusted in `config.txt` (see [config.txt settings](#configtxt-settings)).  
No additional scripts or dzVents rules are needed — the plugin updates both devices automatically.

### E-mail / push notifications

Enable notifications via the **Notification** dropdown in the Domoticz hardware configuration panel (**Setup → Hardware → [plugin] → Edit**). The plugin will then send a notification via **all configured Domoticz notification channels** (e-mail, Pushover, Telegram, etc.) at the time specified by `NotifyTime`:

| Situation | Notification sent |
|---|---|
| Collection day, at or after `NotifyTime` | `<LabelToday>: <type>` (e.g. `Today: Restafval`) |
| Day before collection, at or after `NotifyTime` | `<LabelTomorrow>: <type>` (e.g. `Tomorrow: PMD`) |

The notification is sent only once per day (also across plugin restarts). It needs a Domoticz build that offers `Domoticz.SendNotification()` to Python plugins; on older builds the plugin logs this once at start and disables notifications. To use e-mail notifications, configure your e-mail settings in Domoticz under **Setup → Settings → Notifications**.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Device shows nothing | Check the Domoticz log (**Setup → Log**) for `[GC/...]` error messages. |
| Wrong data / empty response | Verify that your postcode and house number are correct for the selected module. |
| Module 9 (omrin) fails to import | Install the `cryptography` package: `pip install cryptography`. |
| ximmio returns no data | Find the correct `companyCode` for your municipality (see [Module-specific notes](#module-specific-notes)). |
| "Container" device not updating | Check `TodayTime` and `TomorrowTime` in `config.txt`; restart the plugin after saving. |
| No e-mail / push notification received | Enable notifications via the **Notification** dropdown in the hardware panel and verify `NotifyTime` in `config.txt`. Also check that notification channels are configured under **Setup → Settings → Notifications** in Domoticz. |

---

## Tests

The tests run the plugin against a fake Domoticz module, so no Domoticz or internet connection is needed:

```bash
python3 -m unittest discover -s tests -v
```

They also run on GitHub for every pull request.

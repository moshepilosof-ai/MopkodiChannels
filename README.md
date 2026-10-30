# MopkodiChannels

ערוצי שידור חי (טלוויזיה ורדיו) וקטלוגי VOD (תוכניות ופרקים) בפורמט JSON, שמתרעננים אוטומטית ב-GitHub.
המקור לכל הנתונים הוא תוסף הקודי "עידן+" של Fishenzon. אפליקציית הטלוויזיה MopPlus (סמסונג / LG) קוראת את הקבצים האלה ישירות.

המקור הוא טבלת הערוצים של תוסף הקודי "עידן+" של Fishenzon
(`https://github.com/Fishenzon/repo`, הקובץ `plugin.video.idanplus/channels.json`).
הסקריפט `mopchannels.py` מוריד את הטבלה, פותר כל קישור לכתובת השידור בפועל (דף, API או קישור ישיר),
בודק שהכתובת עונה, וכותב שני קבצים:

| קובץ | מה יש בו |
|---|---|
| `channels.json` | כל 84 הערוצים: מזהה, שם, סוג (tv/radio), לוגו, כתובת שידור, headers נדרשים, מצב, זמן בדיקה |
| `channel.json` | אותם ערוצים בפורמט של MopTV (קטגוריות > תת-קטגוריות > ערוצים), בלי ערוצים שדורשים טיקט |

## VOD: תוכניות ופרקים

`idanvod.py` מריץ את התוסף של Fishenzon עצמו, בלי Kodi: `addonloader.py` מוריד את הגרסה האחרונה של התוסף
מהריפו שלו, `kodishim\` מחליף את המודולים של Kodi (`xbmc`, `xbmcgui`...), והסקריפט עובר על תפריטי ה-VOD של
התוסף כמו שקודי היה עובר: ספק > תוכנית > עונה > פרק. כל תיקון שפישנזון מעלה לתוסף מגיע לקטלוג בריצה הבאה.

| קובץ | מה יש בו |
|---|---|
| `vod.json` | אינדקס: תוכנית אחת בכל שורה (שם, ספק, קובץ, מספר פרקים ועונות, תאריך הפרק החדש) |
| `vod/<ספק>_<מזהה>.json` | תוכנית אחת בפורמט של MopVOD: עונות ובתוכן פרקים עם שם, לוגו, כתובת ניגון, תאריך ותקציר |

ספקים: רשת 13, עכשיו 14, ערוץ 9, i24news (עברית), ספורט 5, ספורט 1.
לא נסרקים: מאקו (קשת 12 / ערוץ 24: טיקט לכל צפייה) וכאן (כבר נמצא בריפו MopVOD).

כתובות הניגון: ערוץ 14 / 9 / i24 נותנים כתובת זרם ישירה; ספורט 5 מקודד אותה בפרמטר; לרשת 13 נבנית כתובת Kaltura קבועה
(הכתובת שהתוסף פותר נושאת חתימה שפגה אחרי יום); ספורט 1 נפתר דרך התוסף פעם אחת ונזכר.

## כתובות לקריאה

```
https://raw.githubusercontent.com/moshepilosof-ai/MopkodiChannels/main/channels.json
https://raw.githubusercontent.com/moshepilosof-ai/MopkodiChannels/main/channel.json
https://raw.githubusercontent.com/moshepilosof-ai/MopkodiChannels/main/vod.json
https://raw.githubusercontent.com/moshepilosof-ai/MopkodiChannels/main/vod/<קובץ>
```

## מצב הערוץ (`status` ב-channels.json)

| מצב | משמעות |
|---|---|
| `ok` | הכתובת נפתרה וענתה בבדיקה |
| `unreachable` | הכתובת נפתרה אבל לא ענתה מהשרת של GitHub (ייתכן חסימה גיאוגרפית או שידור כבוי) |
| `needs_ticket` | ערוצי מאקו (קשת 12, ערוץ 24 ועוד). מאקו מנפיקה "טיקט" לכל צפייה, לזמן קצר ורק מישראל, ולכן הכתובת לבד לא מתנגנת. הקישור הבסיסי נשמר, המנגנון לא נעקף |
| `stale` | הפתרון נכשל בריצה הזו, נשמרה הכתובת מהריצה הקודמת |
| `failed` | הפתרון נכשל ואין כתובת קודמת |

## רענון

- **ערוצים**: `.github/workflows/update.yml` מריץ את `mopchannels.py` 4 פעמים ביום (2:15, 8:15, 14:15, 20:15 שעון ישראל בחורף).
- **VOD**: `.github/workflows/vod.yml` מריץ את `idanvod.py` פעמיים ביום (4:40 ו-16:40).
- **יזום**: לשונית **Actions** בריפו > **Update channels** או **Update VOD** > **Run workflow**.
- **מקומי**: `pip install -r requirements.txt` ואז `python mopchannels.py` או `python idanvod.py` (`--limit 2` לבדיקה מהירה).
  `python mopchannels.py --offline` בונה מחדש את `channel.json` מתוך `channels.json` בלי רשת.

## מה הסקריפט לא עושה

לא עוקף טיקטים, DRM או חסימות של אתרי השידור. ערוץ שדורש אימות בזמן ניגון מסומן ונשאר לא פתור.

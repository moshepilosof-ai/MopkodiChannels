# MopChannels

רשימת ערוצי שידור חי (טלוויזיה ורדיו) בפורמט JSON, שמתרעננת אוטומטית ב-GitHub.

המקור הוא טבלת הערוצים של תוסף הקודי "עידן+" של Fishenzon
(`https://github.com/Fishenzon/repo`, הקובץ `plugin.video.idanplus/channels.json`).
הסקריפט `mopchannels.py` מוריד את הטבלה, פותר כל קישור לכתובת השידור בפועל (דף, API או קישור ישיר),
בודק שהכתובת עונה, וכותב שני קבצים:

| קובץ | מה יש בו |
|---|---|
| `channels.json` | כל 84 הערוצים: מזהה, שם, סוג (tv/radio), לוגו, כתובת שידור, headers נדרשים, מצב, זמן בדיקה |
| `channel.json` | אותם ערוצים בפורמט של MopTV (קטגוריות > תת-קטגוריות > ערוצים), בלי ערוצים שדורשים טיקט |

## כתובות לקריאה

```
https://raw.githubusercontent.com/moshepilosof-ai/MopChannels/main/channels.json
https://raw.githubusercontent.com/moshepilosof-ai/MopChannels/main/channel.json
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

- **אוטומטי**: GitHub Actions (`.github/workflows/update.yml`) מריץ את הסקריפט 4 פעמים ביום
  (2:15, 8:15, 14:15, 20:15 שעון ישראל בחורף) ושומר את השינויים לריפו.
- **יזום**: לשונית **Actions** בריפו > **Update channels** > **Run workflow**.
- **מקומי**: `pip install -r requirements.txt` ואז `python mopchannels.py`.
  `python mopchannels.py --offline` בונה מחדש את `channel.json` מתוך `channels.json` בלי רשת.

## מה הסקריפט לא עושה

לא עוקף טיקטים, DRM או חסימות של אתרי השידור. ערוץ שדורש אימות בזמן ניגון מסומן ונשאר לא פתור.

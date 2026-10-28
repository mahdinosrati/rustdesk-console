# راهنمای تصویری راه‌اندازی

[راهنمای اصلی](README-FA.md) · [دستورهای نصب و نگهداری](enhancements-FA.md)

شکل‌های زیر **شماتیک آموزشی** هستند، نه اسکرین‌شات پنل. نام فیلدهای انگلیسی برای تطبیق با نسخهٔ اصلی کنار توضیح فارسی آمده است.

## مسیر اتصال

```mermaid
flowchart LR
    browser["مرورگر شما"] -->|HTTPS :443| caddy["Caddy / گواهی خودکار"]
    caddy --> web["رابط وب کنسول"]
    web --> api["API و SQLite"]
    api -->|"شبکه داخلی :21120"| hbbs["hbbs / شناسه و مدیریت"]
    clientA["کلاینت مبدأ"] --> hbbs
    clientB["کلاینت مقصد"] --> hbbs
    clientA <-->|":21117"| hbbr["hbbr / رله"]
    hbbr <--> clientB
```

HTTPS مربوط به پنل است. برای اتصال RustDesk، پورت‌های شناسه و رله نیز لازم‌اند.

## مرحلهٔ اول: ورود به پنل

```mermaid
flowchart TD
    url["باز کردن https://console.example.com"] --> user["Username: databk"]
    user --> pass["Password: مقدار ADMIN_PASSWORD در فایل .env"]
    pass --> login["Login / ورود"]
    login --> language["منوی زبان ← فارسی، در ساخت فارسی"]
```

رمز و توکن واقعی را در تصویر راهنما یا پیام عمومی قرار ندهید. رمز تصادفی با این دستور دیده می‌شود: `sudo cat /opt/rustdesk-console-compose/.env`.

## مرحلهٔ دوم: معرفی سرور در پنل

```mermaid
flowchart TD
    settings["Settings / تنظیمات"] --> management["Server management / مدیریت سرور"]
    management --> url["Management API URL = http://hbbs:21120"]
    url --> token["Management Token = SERVER_MANAGEMENT_TOKEN از .env"]
    token --> id["Node ID = primary"]
    id --> name["Node Name = سرور اصلی"]
    name --> save["Save / ذخیره"]
    save --> result["بررسی نمایش primary و relay-1"]
```

آدرس `http://hbbs:21120` داخل Docker استفاده می‌شود؛ قرار نیست آن را در مرورگر باز کنید. شناسهٔ نود اصلی را `relay-1` نگذارید.

## مرحلهٔ سوم: تنظیم دو کلاینت

```mermaid
flowchart TD
    network["RustDesk ← Settings ← Network ← ID/Relay server"] --> id["ID server = rd.example.com:21116"]
    id --> relay["Relay server = rd.example.com:21117"]
    relay --> api["API server = https://console.example.com"]
    api --> key["Key = محتوای id_ed25519.pub"]
    key --> both["همین تنظیمات روی مبدأ و مقصد"]
    both --> connect["اتصال آزمایشی با ID مقصد"]
```

کلید را با `sudo cat /opt/rustdesk-console-compose/data/server/id_ed25519.pub` بخوانید. فایل بدون پسوند `.pub` خصوصی است و نباید در کلاینت وارد شود.

## مسیر انتخاب هنگام خطا

```mermaid
flowchart TD
    problem["مشکل اتصال"] --> panel{"پنل باز می‌شود؟"}
    panel -->|"خیر"| caddy["بررسی DNS، پورت 443 و لاگ caddy/web"]
    panel -->|"بله"| nodes{"نودها دیده می‌شوند؟"}
    nodes -->|"خیر"| token["بررسی URL و توکن مدیریت"]
    nodes -->|"بله"| clients["بررسی Key، ID server و پورت‌های RustDesk"]
```

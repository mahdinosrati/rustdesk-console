# HTTPS، پیش‌بررسی، بکاپ و رابط فارسی

[راهنمای اصلی](README-FA.md) · [نصب Docker قدم‌به‌قدم](docker-FA.md) · [راهنمای تصویری](visual-FA.md)

## نصب تازه با HTTPS خودکار

ابتدا رکوردهای DNS دامنه‌های `rd.example.com` و `console.example.com` را به IP سرور اشاره دهید. رکورد AAAA نیز در صورت وجود باید درست باشد. پورت‌های TCP 80 و 443 باید از اینترنت به سرور برسند؛ فایروال دیتاسنتر و NAT را خودتان تنظیم کنید. برای پروتکل RustDesk، رکورد DNS را بدون پراکسی HTTP استفاده کنید.

روی Ubuntu/Debian:

```sh
sudo apt-get update && sudo apt-get install -y curl ca-certificates openssl python3
curl -fsSL https://raw.githubusercontent.com/mahdinosrati/rustdesk-console/main/deployment/install-compose.sh -o /tmp/rustdesk-console-install.sh
sudo sh /tmp/rustdesk-console-install.sh --host rd.example.com --https-domain console.example.com
```

دامنه‌های نمونه را جایگزین کنید. در این حالت Caddy به Compose اضافه می‌شود، گواهی معتبر می‌گیرد و تمدید می‌کند؛ پنل از شبکهٔ داخلی Docker در دسترس Caddy است و پورت 21114 روی میزبان منتشر نمی‌شود. نشانی ورود `https://console.example.com` است. پورت‌های RustDesk مستقل از HTTPS هستند. رفتار گواهی و نیازمندی‌های DNS طبق [مستندات رسمی Caddy](https://caddyserver.com/docs/automatic-https) است.

نصاب در پایان اتصال TLS محلی را با نام دامنه و اعتبارسنجی گواهی بررسی می‌کند؛ هیچ گزینهٔ نادیده گرفتن گواهی ندارد. اگر گواهی آماده نشد، سرویس‌ها را حذف نمی‌کند و خطا می‌دهد. برای بررسی:

```sh
cd /opt/rustdesk-console-compose
sudo docker compose logs --tail 100 caddy
curl -I https://console.example.com
```

این گزینه برای **نصب تازه** است. روی نصب ثبت‌شده، افزودن Caddy یا تغییر Compose می‌تواند ثبت updater را نامعتبر کند؛ نصاب عمداً نصب قبلی را تغییر نمی‌دهد. بدون `--https-domain` مسیر نصب HTTP قبلی حفظ می‌شود.

## بررسی قبل از نصب

بدون نصب Docker یا ایجاد پوشهٔ برنامه:

```sh
sudo sh /tmp/rustdesk-console-install.sh --host rd.example.com --https-domain console.example.com --check
```

این بررسی معماری، فضای دیسک، پاسخ DNS، پورت‌های اشغال TCP/UDP، کانتینرهای قبلی `hbbs/hbbr`، اتصال به مخزن فایل‌ها و رجیستری، و در صورت وجود Docker، daemon و Compose را بررسی می‌کند. فایل بررسی در پوشهٔ موقت دانلود و پس از اجرا حذف می‌شود. اگر Docker نصب نیست، حالت بررسی آن را نصب نمی‌کند؛ نصب واقعی در Debian/Ubuntu آن را آماده می‌کند.

پاسخ DNS تضمین نمی‌کند که IP متعلق به همین سرور است و آزمون محلی پورت تضمین دسترسی از اینترنت نیست. این دو مورد را از بیرون سرور نیز بررسی کنید. فضای لازم برای ساخت رابط فارسی از نصب با ایمیج آماده بیشتر است؛ برای ساخت حداقل ۴ گیگابایت RAM و ۵ گیگابایت فضای آزاد در نظر بگیرید.

## نصب با پنل فارسی

برای نصب تازهٔ پنل فارسی همراه HTTPS و سرور:

```sh
sudo sh /tmp/rustdesk-console-install.sh --host rd.example.com --https-domain console.example.com --persian-web
```

نصاب رابط وب را از commit مشخص در [فورک رابط وب](https://github.com/mahdinosrati/rustdesk-console-web) با Docker می‌سازد. اولین ساخت نسبت به دریافت ایمیج زمان و منابع بیشتری نیاز دارد. پس از ورود از منوی زبان، **فارسی** را انتخاب کنید. کاتالوگ انگلیسی ترجمه شده و راست‌به‌چپ از طریق سامانهٔ زبان موجود فعال می‌شود؛ پیام‌های مستقیم سرور یا متن‌های خارج از سامانهٔ ترجمه ممکن است همچنان انگلیسی باشند.

**این نصب به‌روزرسانی دستی دارد:** updater رسمی برای نسخهٔ سفارشی فارسی اجرا نمی‌شود؛ بنابراین از کنترل «Update system» برای آن استفاده نکنید. نسخهٔ عادی بدون `--persian-web` همچنان updater اصلی را دارد. برای تغییر نسخهٔ فارسی، ابتدا بکاپ بگیرید، commit سازگار جدید را در `build.context` بررسی و ثبت کنید و سپس فقط رابط وب را بسازید:

```sh
cd /opt/rustdesk-console-compose
sudo docker compose build rustdesk-console-web
sudo docker compose up -d --no-deps rustdesk-console-web
```

برای ادامهٔ نصب اولیهٔ فارسی پس از خطای دانلود، همان `build` را تکرار کنید، سپس `sudo docker compose pull --ignore-buildable` و `sudo docker compose up -d --wait` اجرا کنید. دیتابیس و `.env` را دوباره تولید نکنید.

## بکاپ با یک دستور

نصب جدید فایل `console-backup.py` را در پوشهٔ نصب می‌گذارد. برای نصب قدیمی، ابزار را مستقل دریافت کنید (اجرای نصاب لازم نیست):

```sh
curl -fsSL https://raw.githubusercontent.com/mahdinosrati/rustdesk-console/main/deployment/console-backup.py -o /tmp/console-backup.py
```

سپس:

```sh
sudo python3 /tmp/console-backup.py backup /root/rustdesk-console-backup.tar.gz
```

یا در نصب جدید، به‌جای `/tmp/console-backup.py` مسیر `/opt/rustdesk-console-compose/console-backup.py` را بدهید. فایل خروجی از قبل نباید وجود داشته باشد. ابزار فقط SQLite را پشتیبانی می‌کند؛ MySQL خارجی به بکاپ مستقل نیاز دارد.

ابزار قفل اجرای updater را می‌گیرد، عملیات ناتمام یا maintenance فعال را رد می‌کند، سرویس‌های در حال اجرا را موقتاً متوقف می‌کند، کل پوشهٔ نصب را آرشیو می‌کند و همان سرویس‌ها را دوباره شروع می‌کند. بنابراین اتصال‌های فعال قطع می‌شوند. برای نصب مدیریت‌شده، ثبت اولیهٔ updater باید کامل شده باشد. در صورت شکست بکاپ، آرشیو ناقص حذف می‌شود.

دیتابیس، کلیدهای سرور، تنظیمات، دادهٔ Caddy و state مربوط به updater در بکاپ قرار می‌گیرند؛ ایمیج‌های Docker داخل آن نیستند. فایل خروجی شامل رمزها و کلید خصوصی است، با دسترسی 600 ایجاد می‌شود و باید در محل امن دیگری نیز نگهداری شود. فایل‌های لینک‌شده یا ویژه پشتیبانی نمی‌شوند؛ خطای آن‌ها را با حذف داده رفع نکنید.

## بازیابی با یک دستور

روی میزبان تازه با Docker/Compose و Python 3.10 یا جدیدتر، فایل بکاپ و ابزار بالا را قرار دهید. مسیر `/opt/rustdesk-console-compose` و کانتینرهای نصب قبلی نباید وجود داشته باشند:

```sh
sudo python3 /tmp/console-backup.py restore /root/rustdesk-console-backup.tar.gz
```

ابزار مسیرهای خروج از آرشیو، لینک‌ها و فایل‌های ویژه را رد می‌کند، ابتدا در پوشهٔ موقت استخراج می‌کند و سپس در مسیر استاندارد قرار می‌دهد. روی دادهٔ موجود بازنویسی نمی‌کند و سرویس‌ها را خودکار روشن نمی‌کند. فقط از بکاپ مورد اعتماد خودتان استفاده کنید؛ Compose و کد داخل بکاپ هنگام راه‌اندازی اجرا می‌شوند.

پس از بررسی فایل‌ها و DNS:

```sh
cd /opt/rustdesk-console-compose
sudo docker compose config --quiet
sudo docker compose up -d --build --wait --wait-timeout 180
```

برای نصب فارسی، بازسازی رابط به اینترنت نیاز دارد؛ نسخهٔ عادی نیز باید بتواند digestهای ایمیج‌های ثبت‌شده را دریافت کند. در پایان ورود به پنل و اتصال دو کلاینت را آزمایش کنید. بازیابی روی همان میزبان دارای نصب قبلی، نیاز به برنامهٔ مهاجرت و بکاپ مستقل دارد؛ ابزار آن را خودکار پاک نمی‌کند.

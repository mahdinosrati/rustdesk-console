# راهنمای فارسی RustDesk Console

[صفحهٔ اصلی](../README.md) · [مخزن این نسخه](https://github.com/mahdinosrati/rustdesk-console)

**[آموزش قدم‌به‌قدم نصب با Docker Compose](docker-FA.md)** — از نصب Docker تا تنظیم سرور و اتصال اولین کلاینت.

RustDesk Console پنل وب مدیریت کاربران، دستگاه‌ها، دفترچهٔ آدرس، سیاست‌های دسترسی و گزارش‌های RustDesk است. برای اتصال دسکتاپ از راه دور به دو سرویس `hbbs` (شناسه و هماهنگی اتصال) و `hbbr` (رله) نیز نیاز دارید. نصب کامل زیر هر دو را در کنار پنل راه‌اندازی می‌کند.

این راهنما مستندات را فارسی می‌کند؛ زبان رابط وب را تغییر نمی‌دهد. نصب Docker از ایمیج‌های منتشرشدهٔ پروژهٔ اصلی `databk` استفاده می‌کند و کد این فورک را نمی‌سازد.

## پیش‌نیازها

- سرور لینوکسی با دسترسی `root` یا `sudo`؛ برای نصب خودکار Docker از Debian یا Ubuntu استفاده کنید.
- معماری `amd64` یا `arm64`، اینترنت و دسترسی به GitHub، مخازن Docker و Docker Hub.
- یک IP قابل‌دسترسی یا دامنه مانند `rd.example.com` که به سرور اشاره کند. در صورت استفاده از Cloudflare، رکورد مربوط به پروتکل RustDesk باید DNS only باشد.
- بسته‌های `curl`، `ca-certificates` و `openssl`. در Debian/Ubuntu، اگر موجود نیستند:

```sh
sudo apt-get update && sudo apt-get install -y curl ca-certificates openssl
```

نصاب برای نصب تازه است. مسیر ثابت آن `/opt/rustdesk-console-compose` است و اگر این مسیر از قبل وجود داشته باشد، بدون بازنویسی خارج می‌شود. Docker موجود را ارتقا نمی‌دهد؛ اگر Docker نصب نباشد، اسکریپت رسمی `get.docker.com` را اجرا می‌کند. روی سایر توزیع‌ها ابتدا Docker Engine و افزونهٔ Compose v2 را نصب کنید. Docker باید محلی، فعال و بدون حالت rootless باشد؛ Docker Desktop ویندوز هدف این نصاب نیست.

## نصب کامل با یک دستور

دستور زیر را روی سرور اجرا کنید. به جای `rd.example.com` دامنه یا IPv4 سرور خود را بنویسید؛ `https://` و شمارهٔ پورت را وارد نکنید.

```sh
curl -fsSL https://raw.githubusercontent.com/mahdinosrati/rustdesk-console/main/deployment/install-compose.sh -o /tmp/rustdesk-console-install.sh && sudo sh /tmp/rustdesk-console-install.sh --host rd.example.com
```

اگر سورس را دریافت کرده‌اید، همین نصب بدون نیاز به انتشار نصاب نیز قابل اجراست:

```sh
sudo sh deployment/install-compose.sh --host rd.example.com
```

نصاب فایل‌های Compose را از یک commit مشخص دریافت می‌کند، رمز مدیر و کلیدهای تصادفی می‌سازد، تنظیمات را با دسترسی محدود ذخیره می‌کند، ایمیج‌ها را می‌گیرد و سرویس‌ها را اجرا می‌کند. دریافت ایمیج‌ها بسته به اینترنت زمان می‌برد. موفقیت دستور به معنی آماده بودن کانتینرهاست؛ ثبت updater را جداگانه از بخش «بررسی نصب» بررسی کنید.

اگر از قبل سرور RustDesk دارید و فقط پنل می‌خواهید:

```sh
sudo sh deployment/install-compose.sh --console-only
```

این حالت فقط backend، رابط وب و updater را اجرا می‌کند. برای مدیریت سرور موجود از داخل پنل، آن سرور باید API مدیریتی سازگار داشته باشد؛ هر نسخهٔ معمولی `hbbs/hbbr` الزاماً این قابلیت را ندارد.

## ورود اولیه و مدیریت سرور

۱. در مرورگر آدرس `http://SERVER_IP:21114` را باز کنید. نام کاربری اولیه `databk` است. رمز تصادفی در فایل زیر، مقابل `ADMIN_PASSWORD` قرار دارد:

```sh
sudo cat /opt/rustdesk-console-compose/.env
```

این فایل شامل اطلاعات محرمانه است؛ خروجی آن را در پیام، تیکت یا تصویر عمومی قرار ندهید. تغییر `ADMIN_PASSWORD` در فایل، رمز حساب موجود را عوض نمی‌کند؛ تغییر رمز بعدی را از پنل انجام دهید.

۲. در نصب کامل، در **Settings → Server management** اطلاعات زیر را ثبت کنید:

| گزینه | مقدار |
| --- | --- |
| نشانی مدیریتی hbbs | `http://hbbs:21120` |
| توکن | مقدار `SERVER_MANAGEMENT_TOKEN` از `.env` |
| شناسهٔ نود اصلی | مثلاً `primary`؛ متفاوت از `relay-1` |
| نام نود | نام دلخواه، مثلاً «سرور اصلی» |

۳. وضعیت نود اصلی و رلهٔ `relay-1` را بررسی کنید. نصب کانتینرها این فرم را خودکار پر نمی‌کند. جزئیات بیشتر: [مدیریت سرور](server-management.md).

## اتصال برنامهٔ RustDesk

کلید عمومی سرور را بخوانید:

```sh
sudo cat /opt/rustdesk-console-compose/data/server/id_ed25519.pub
```

در تنظیمات شبکهٔ RustDesk روی دستگاه‌های مبدأ و مقصد، قسمت ID/Relay server را تنظیم کنید:

| فیلد | مقدار نمونه |
| --- | --- |
| ID server | `rd.example.com:21116` |
| Relay server | `rd.example.com:21117` |
| API server | `https://console.example.com` پس از تنظیم HTTPS، یا `http://SERVER_IP:21114` برای آزمایش در شبکهٔ مورد اعتماد |
| Key | متن کامل فایل `id_ed25519.pub` |

از فایل خصوصی `id_ed25519` استفاده نکنید. تنظیمات را روی هر دو دستگاه اعمال کنید، آماده شدن اتصال را بررسی کنید و سپس با شناسهٔ دستگاه مقصد متصل شوید. اتصال دسکتاپ و ورود به حساب کنسول دو بخش جدا هستند؛ برای امکانات حساب و دفترچهٔ آدرس، ورود کاربر از طریق API نیز باید کار کند.

## پورت‌ها و HTTPS

| پورت | پروتکل | کاربرد |
| --- | --- | --- |
| 21114 | TCP | پنل وب و API |
| 21115 | TCP | تشخیص NAT |
| 21116 | TCP و UDP | سرویس شناسه و هماهنگی اتصال |
| 21117 | TCP | رله |
| 21118 و 21119 | TCP | WebSocket برای کلاینت وب |
| 21120 | داخلی شبکهٔ Docker | API مدیریت؛ در Compose روی میزبان منتشر نمی‌شود |

در فایروال دیتاسنتر و NAT، پورت‌های موردنیاز را برای همین سرور مجاز کنید. نصاب فایروال را تغییر نمی‌دهد. برای نمونه، پس از اطمینان از باز بودن SSH، روی میزبانی که UFW فعال دارد:

```sh
sudo ufw allow 21115:21119/tcp
sudo ufw allow 21116/udp
```

برای استفادهٔ عمومی، پنل را پشت reverse proxy با HTTPS قرار دهید؛ ورود با HTTP برای شبکهٔ عمومی مناسب نیست. مثلاً روی reverse proxy میزبان، این Caddyfile را با دامنهٔ واقعی استفاده کنید؛ Caddy باید جداگانه نصب شود و پورت‌های 80 و 443 و DNS درست باشند:

```caddyfile
console.example.com {
    reverse_proxy 127.0.0.1:21114
}
```

Compose استاندارد، پورت 21114 را روی همهٔ رابط‌ها منتشر می‌کند. با فایروال بیرونی یا قواعد مناسب Docker، دسترسی مستقیم عمومی به آن را محدود کنید؛ تنها وجود UFW به معنی بسته بودن پورت منتشرشدهٔ Docker نیست. اگر به اتصال صرفاً localhost نیاز دارید، **پیش از اولین اجرا** در نصب دستی زیر، مقدار `'21114:80'` را به `'127.0.0.1:21114:80'` تغییر دهید. تغییر Compose بعد از ثبت updater ممکن است به `CONFIGURATION_DRIFT` منجر شود.

## نصب دستی یا تنظیمات سفارشی

برای پورت سفارشی، MySQL یا بررسی فایل‌ها پیش از اجرا، از [روش استاندارد README](../README.md#-quick-start) استفاده کنید: فایل‌های `docker-compose.yml`، `docker-compose.override.yml` و `.env.example` را در یک پوشهٔ اختصاصی روی میزبان قرار دهید، سپس:

```sh
cp .env.example .env
chmod 600 .env
openssl rand -hex 32
```

در `.env`، کلید `JWT_SECRET` و رمز `ADMIN_PASSWORD` را با مقادیر مستقل و تصادفی تنظیم کنید؛ `CONSOLE_INSTALL_DIR` باید مسیر مطلق واقعی همان پوشه باشد. برای نصب کامل، `COMPOSE_PROFILES=server`، `RUSTDESK_RELAY_ADDRESS=rd.example.com:21117` و یک `SERVER_MANAGEMENT_TOKEN` تصادفی با حداقل ۳۲ کاراکتر را نیز وارد کنید. سپس در همان پوشه:

```sh
sudo docker compose config --quiet
sudo docker compose up -d --wait --wait-timeout 180
```

فایل `docker-compose.override.yml` مخصوص digestهای updater است؛ تنظیمات شخصی را در آن ننویسید. SQLite پیش‌فرض است؛ MySQL نیاز به دیتابیس جدا و تنظیمات توضیح‌داده‌شده در [راهنمای به‌روزرسانی](system-update.md) دارد.

## بررسی نصب و رفع خطا

دستورهای مدیریتی نصب خودکار را از پوشهٔ ثابت اجرا کنید:

```sh
cd /opt/rustdesk-console-compose
sudo docker compose ps
sudo docker compose logs --tail 100 rustdesk-console rustdesk-console-web updater
sudo docker compose logs --tail 100 hbbs hbbr
```

دستور آخر فقط برای نصب کامل است. ثبت updater به انتشار رسمی سازگار و manifest معتبر وابسته است؛ وضعیت آن را در **Update system** و لاگ updater ببینید. صرفاً Running بودن کانتینر updater، ثبت موفق را تضمین نمی‌کند.

| مشکل | بررسی |
| --- | --- |
| دانلود انجام نمی‌شود | DNS و دسترسی سرور به GitHub، Docker Hub و مخازن Docker را بررسی کنید. |
| پورت اشغال است یا کانتینر `hbbs` موجود است | احتمالاً سرور قبلی دارید؛ نصب کامل را کنار آن بدون برنامهٔ مهاجرت اجرا نکنید. |
| پنل باز نمی‌شود | وضعیت کانتینر وب، پورت 21114 و فایروال دیتاسنتر را بررسی کنید. |
| خطای کلید در کلاینت | متن کلید عمومی و ID server هر دو دستگاه باید مربوط به همین سرور باشد. |
| مدیریت سرور قطع است | آدرس `http://hbbs:21120` و یکسان بودن توکن در پنل و `.env` را بررسی کنید. |
| updater به `CONFIGURATION_DRIFT` رسیده | Compose یا محیط نصب تغییر کرده؛ state را حذف نکنید و [راهنمای بازیابی](system-update.md) را دنبال کنید. |
| نصاب به دلیل وجود پوشه متوقف شده | داده‌ها حفظ شده‌اند. اگر نصب قبلی در دریافت ایمیج یا اجرا متوقف شده، دستورهای ادامهٔ نصب زیر را اجرا کنید. |

ادامهٔ نصب پس از رفع مشکل شبکه یا پورت، بدون تولید دوبارهٔ رمزها:

```sh
cd /opt/rustdesk-console-compose
sudo docker compose config --quiet
sudo docker compose pull
sudo docker compose up -d --wait --wait-timeout 180
```

این دستورها برای تکمیل نصب اولیه‌اند؛ برای ارتقای نصب ثبت‌شده از پنل استفاده کنید. اگر فایل‌های نصب ناقص‌اند، ابتدا آن‌ها را بررسی کنید و پوشهٔ دارای داده را حذف نکنید.

## به‌روزرسانی، بکاپ و توقف

برای ارتقای هماهنگ backend و frontend از **Update system** استفاده کنید. updater خودکار ارتقا را آغاز نمی‌کند و `hbbs/hbbr` را ارتقا نمی‌دهد. جزئیات و محدودیت‌ها در [راهنمای به‌روزرسانی](system-update.md) آمده است.

برای بکاپ سادهٔ نصب پیش‌فرض SQLite، زمانی را انتخاب کنید که هیچ عملیات update/recovery در حال اجرا نیست. توقف سرویس‌ها اتصال‌های فعال را قطع می‌کند. این روش کل پوشه، کلیدها، دیتابیس، تنظیمات و state را ذخیره می‌کند:

```sh
sudo sh -c 'set -eu; umask 077; cd /opt/rustdesk-console-compose; docker compose stop; trap "docker compose start" EXIT; tar -czf "/root/rustdesk-console-$(date +%Y%m%d-%H%M%S).tar.gz" -C /opt rustdesk-console-compose'
```

بکاپ شامل رمزها و کلید خصوصی است؛ آن را در فضای امن و جدا از سرور نگه دارید. برای MySQL خارجی، بکاپ سازگار دیتابیس نیز جداگانه لازم است. بازیابی را روی میزبان با سرویس‌های متوقف، در **همان مسیر مطلق** و با حفظ مالکیت فایل‌ها انجام دهید؛ ابتدا از وضعیت فعلی نسخهٔ پشتیبان بگیرید. مسیر نصب و state updater را خودسرانه جابه‌جا نکنید.

توقف موقت و راه‌اندازی مجدد:

```sh
cd /opt/rustdesk-console-compose
sudo docker compose stop
sudo docker compose start
```

برای حذف کانتینرها بدون حذف پوشهٔ داده می‌توانید `sudo docker compose down` اجرا کنید. حذف مسیر `/opt/rustdesk-console-compose` داده‌ها و هویت سرور را از بین می‌برد؛ برای نصب مجدد یا رفع خطا آن را پاک نکنید.

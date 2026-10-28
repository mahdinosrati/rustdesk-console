# نصب قدم‌به‌قدم RustDesk Console با Docker

[بازگشت به راهنمای فارسی](README-FA.md)

این آموزش برای نصب تازه روی سرور Ubuntu یا Debian با معماری `amd64` یا `arm64` است. پنل، دیتابیس SQLite، updater و در حالت کامل سرورهای `hbbs/hbbr` را راه‌اندازی می‌کنیم. نیازی به نصب Node.js یا ساخت سورس نیست؛ Compose از ایمیج‌های منتشرشدهٔ `databk` استفاده می‌کند.

اگر نصب تک‌دستوری را قبلاً انجام داده‌اید، مراحل ساخت پوشه و تنظیمات را تکرار نکنید؛ از مرحلهٔ ۷ وضعیت نصب را بررسی کنید. دستورها را به ترتیب اجرا کنید و اگر هر مرحله خطا داد، قبل از ادامه همان خطا را رفع کنید.

## ۱. ورود به سرور

از ترمینال کامپیوتر خود متصل شوید؛ `USER` و `SERVER_IP` را جایگزین کنید:

```sh
ssh USER@SERVER_IP
```

دستورهای بعدی روی سرور اجرا می‌شوند. کاربر باید دسترسی `sudo` داشته باشد. دامنهٔ نمونهٔ `rd.example.com` باید به IP همین سرور اشاره کند؛ می‌توانید به جای آن IPv4 سرور را استفاده کنید.

```sh
sudo apt-get update
sudo apt-get install -y ca-certificates curl openssl nano
```

## ۲. نصب Docker Engine و Compose

اگر دستورهای `sudo docker info` و `sudo docker compose version` موفق هستند، نصب مجدد لازم نیست؛ به مرحلهٔ ۳ بروید. اگر Docker یا containerd قدیمی دارید، ابتدا بخش تداخل بسته‌ها در مستندات رسمی [Ubuntu](https://docs.docker.com/engine/install/ubuntu/) یا [Debian](https://docs.docker.com/engine/install/debian/) را بررسی کنید؛ مراحل زیر برای میزبان تازه‌اند.

در همان ترمینال، مخزن رسمی متناسب با توزیع را اضافه کنید:

```sh
. /etc/os-release
docker_distro="$ID"
docker_codename="${UBUNTU_CODENAME:-$VERSION_CODENAME}"
```

این آموزش فقط برای `docker_distro` برابر `ubuntu` یا `debian` است. سپس:

```sh
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL "https://download.docker.com/linux/$docker_distro/gpg" -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources > /dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/$docker_distro
Suites: $docker_codename
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
```

صحت نصب را بررسی کنید:

```sh
sudo docker run --rm hello-world
sudo docker compose version
sudo docker info
sudo docker context inspect --format '{{.Endpoints.docker.Host}}'
```

باید پیام موفقیت `hello-world`، نسخهٔ Compose و مشخصات daemon را ببینید. endpoint باید `unix:///var/run/docker.sock` باشد. نصب مدیریت‌شده به Docker محلی لینوکس بدون rootless نیاز دارد؛ این مراحل برای Docker Desktop ویندوز نیستند.

## ۳. ساخت پوشهٔ نصب

```sh
sudo mkdir -m 755 /opt/rustdesk-console-compose
cd /opt/rustdesk-console-compose
```

اگر `mkdir` گفت مسیر وجود دارد، فایل‌های آن را بررسی کنید؛ روی نصب قبلی مراحل تولید تنظیمات را اجرا نکنید. از `mkdir -p` برای نادیده گرفتن این خطا استفاده نکنید. این مسیر پس از ثبت updater نباید جابه‌جا شود.

فایل‌های Compose را از همان نسخه‌ای که نصاب استفاده می‌کند دریافت کنید:

```sh
console_source=https://raw.githubusercontent.com/mahdinosrati/rustdesk-console/3c568c7c32f829cd85de4823cd63cf92ab12ed78
sudo curl -fsSL "$console_source/docker-compose.yml" -o docker-compose.yml
sudo curl -fsSL "$console_source/docker-compose.override.yml" -o docker-compose.override.yml
ls -l docker-compose.yml docker-compose.override.yml
```

فایل override را نگه دارید؛ updater از آن برای ثبت digest ایمیج‌ها استفاده می‌کند. تنظیمات شخصی را در این فایل ننویسید.

## ۴. ساخت رمزها و تنظیمات اولیه

این بلوک فقط برای بار اول است. اگر `.env` از قبل باشد، آن را بازنویسی نمی‌کند:

```sh
sudo sh -eu <<'SH'
cd /opt/rustdesk-console-compose
set -C
umask 077
jwt=$(openssl rand -hex 32)
password=$(openssl rand -hex 24)
token=$(openssl rand -hex 32)
cat > .env <<EOF
CONSOLE_INSTALL_DIR=/opt/rustdesk-console-compose
JWT_SECRET=$jwt
ADMIN_PASSWORD=$password
DB_TYPE=sqlite
COMPOSE_PROFILES=server
RUSTDESK_RELAY_ADDRESS=rd.example.com:21117
SERVER_MANAGEMENT_TOKEN=$token
EOF
SH
sudo nano .env
```

در ویرایشگر، `rd.example.com` را با دامنه یا IP واقعی سرور عوض کنید؛ شمارهٔ پورت `:21117` بماند. با `Ctrl+O` و Enter ذخیره کنید و با `Ctrl+X` خارج شوید. رمزها به‌صورت تصادفی ساخته شده‌اند؛ نیازی به وارد کردن رمز نمونه نیست.

اگر **فقط پنل** می‌خواهید و سرور RustDesk جدا دارید، پیش از اولین اجرا این سه خط را از `.env` حذف کنید: `COMPOSE_PROFILES`، `RUSTDESK_RELAY_ADDRESS` و `SERVER_MANAGEMENT_TOKEN`. در این حالت سه سرویس پنل اجرا می‌شوند و مراحل مربوط به `hbbs/hbbr` را انجام نمی‌دهید.

```sh
sudo chmod 600 .env
sudo mkdir -m 700 data
sudo chown 1000:1000 data
```

داده‌ها در `data/` روی میزبان می‌مانند. فایل `.env` حاوی رمز مدیر و توکن‌هاست؛ آن را عمومی نکنید. گزینه‌های این فایل را هم‌زمان به‌صورت متغیر محیطی در shell تنظیم نکنید تا اجرای دستی و updater تنظیمات یکسانی داشته باشند.

## ۵. تعیین دسترسی شبکه پیش از اجرا

در نصب کامل، TCP پورت‌های `21115` تا `21119` و UDP پورت `21116` باید از کلاینت‌ها به سرور قابل دسترسی باشند؛ هم فایروال دیتاسنتر و هم NAT را بررسی کنید. پورت `21120` داخلی است و نباید برای مدیریت روی اینترنت باز شود.

برای آزمایش پنل در شبکهٔ مورد اعتماد، دسترسی TCP به `21114` لازم است. برای استفادهٔ عمومی، HTTPS را طبق [بخش پورت‌ها و HTTPS](README-FA.md#پورتها-و-https) تنظیم کنید. اگر reverse proxy روی همین میزبان دارید و می‌خواهید پنل فقط از localhost قابل دسترسی باشد، **همین حالا پیش از اجرا** فایل را ویرایش کنید:

```sh
sudo nano docker-compose.yml
```

مقدار `'21114:80'` را به `'127.0.0.1:21114:80'` تغییر دهید. پس از این تغییر، دسترسی مستقیم از کامپیوتر دیگری به `SERVER_IP:21114` کار نمی‌کند؛ از دامنهٔ HTTPS یا تونل SSH استفاده کنید. انتشار پیش‌فرض روی همهٔ رابط‌هاست و قواعد UFW به‌تنهایی الزاماً پورت Docker را مسدود نمی‌کنند.

## ۶. دریافت ایمیج‌ها و اجرا

```sh
cd /opt/rustdesk-console-compose
sudo docker compose config --quiet
sudo docker compose pull
sudo docker compose up -d --wait --wait-timeout 180
```

دستور اول در حالت موفق خروجی ندارد. دستور دوم ایمیج‌ها را دانلود می‌کند؛ اگر دانلود خطا داد، مشکل شبکه را رفع و همان دستور را تکرار کنید. دستور سوم سرویس‌ها را در پس‌زمینه اجرا می‌کند و منتظر وضعیت آماده می‌ماند. هنگام timeout، به جای تولید دوبارهٔ `.env`، مرحلهٔ بعد را برای دیدن لاگ انجام دهید.

## ۷. بررسی سرویس‌ها

```sh
sudo docker compose ps
sudo docker compose logs --tail 100 rustdesk-console rustdesk-console-web updater
```

در نصب کامل این دو سرویس هم باید فعال باشند:

```sh
sudo docker compose logs --tail 100 hbbs hbbr
```

| سرویس | کاربرد |
| --- | --- |
| `rustdesk-console` | API و دیتابیس پنل |
| `rustdesk-console-web` | رابط وب |
| `updater` | ثبت نصب و به‌روزرسانی مدیریت‌شده |
| `hbbs` | سرویس شناسه و هماهنگی اتصال |
| `hbbr` | رلهٔ اتصال |

`Restarting` یا `Exited` یعنی باید لاگ همان سرویس را بررسی کنید. Running بودن updater به‌تنهایی ثبت موفق نصب را تضمین نمی‌کند؛ ثبت به manifest رسمی سازگار وابسته است. پس از ورود، وضعیت **Update system** را هم بررسی کنید. فایل‌های Compose و مسیر نصب را بعد از ثبت تغییر ندهید؛ تغییر آن‌ها می‌تواند `CONFIGURATION_DRIFT` ایجاد کند.

## ۸. ورود به پنل و معرفی سرور

در حالت انتشار پیش‌فرض و شبکهٔ مورد اعتماد، `http://SERVER_IP:21114` را باز کنید؛ در حالت reverse proxy از دامنهٔ HTTPS خودتان استفاده کنید. نام کاربری اولیه `databk` است. رمز را در خط `ADMIN_PASSWORD` ببینید:

```sh
sudo cat /opt/rustdesk-console-compose/.env
```

در **Settings → Server management**، آدرس `http://hbbs:21120`، توکن همان `SERVER_MANAGEMENT_TOKEN` و شناسهٔ اصلی مثلاً `primary` را وارد کنید. نام نود دلخواه است؛ شناسهٔ اصلی نباید `relay-1` باشد. تنظیمات را ذخیره و وضعیت نود اصلی و رله را بررسی کنید. این تنظیمات داخل پنل خودکار پر نمی‌شوند.

در حالت پنل تنها، آدرس و توکن سرور جداگانهٔ خود را وارد کنید؛ آن سرور باید API مدیریتی سازگار داشته باشد. تغییر رمز حساب موجود را از پنل انجام دهید؛ ویرایش `ADMIN_PASSWORD` رمز حساب ساخته‌شده را عوض نمی‌کند.

## ۹. اتصال اولین کلاینت

در نصب کامل، کلید عمومی را دریافت کنید:

```sh
sudo cat /opt/rustdesk-console-compose/data/server/id_ed25519.pub
```

در تنظیمات شبکهٔ برنامهٔ RustDesk روی **هر دو دستگاه مبدأ و مقصد**:

| فیلد | مقدار |
| --- | --- |
| ID server | `rd.example.com:21116` |
| Relay server | `rd.example.com:21117` |
| API server | دامنهٔ HTTPS پنل؛ برای آزمایش شبکهٔ مورد اعتماد `http://SERVER_IP:21114` |
| Key | متن کامل فایل `id_ed25519.pub` |

دامنهٔ نمونه را جایگزین کنید. در نصب پنل تنها، شناسه، رله و کلید متعلق به سرور موجود شما هستند. پس از آماده شدن کلاینت‌ها، با ID مقصد یک اتصال آزمایشی برقرار کنید؛ ورود حساب و دفترچهٔ آدرس را نیز جداگانه بررسی کنید.

## ۱۰. مدیریت بعد از نصب

دستورهای زیر از پوشهٔ نصب اجرا می‌شوند:

```sh
cd /opt/rustdesk-console-compose
sudo docker compose ps
sudo docker compose logs --tail 100 rustdesk-console
```

برای توقف موقت از `sudo docker compose stop` و برای شروع دوباره از `sudo docker compose start` استفاده کنید؛ توقف سرور، اتصال‌های فعال را قطع می‌کند. برای ارتقای پنل ثبت‌شده از **Update system** استفاده کنید. updater سرویس‌های `hbbs/hbbr` را ارتقا نمی‌دهد.

روش بکاپ، بازیابی و خطاهای رایج در [راهنمای فارسی](README-FA.md) آمده است. پوشهٔ نصب یا `data/` را برای رفع خطا حذف نکنید؛ هویت سرور و دیتابیس در آن‌ها قرار دارند.

<div align="center">

# 🚀 مرکز فرماندهی و اتوماسیون سئو چندسایته
### SEO Command Center — Multi-Tenant SEO Management, SERP Rank Tracking & AI Content Autopilot

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Bootstrap 5 RTL](https://img.shields.io/badge/UI-Bootstrap%205%20RTL-7952B3.svg?style=for-the-badge&logo=bootstrap)](https://getbootstrap.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![GitHub Repository](https://img.shields.io/badge/GitHub-taimazus%2FSEO--Command--Center-181717.svg?style=for-the-badge&logo=github)](https://github.com/taimazus/SEO-Command-Center)

<br/>

<img src="assets/intro-banner.png" alt="SEO Command Center Intro Banner" width="100%" style="border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);" />

<br/><br/>

</div>

<div dir="rtl">

## 📖 معرفی پلتفرم

**SEO Command Center** یک پلتفرم جامع، مدرن و متمرکز برای آژانس‌های دیجیتال مارکتینگ، برنامه‌نویسان و متخصصان سئو است که به شما امکان می‌دهد **ده‌ها وب‌سایت مشتریان و پروژه‌های شخصی** را به صورت همزمان در یک داشبورد اختصاصی مدیریت کنید.

این سیستم با معماری بسیار سریع مبتنی بر **FastAPI** و **SQLite** طراحی شده و ابزارهای حیاتی سئو شامل **رصد روزانه رتبه کلمات در نتایج گوگل (SERP Tracker)**، **ارسال آنی صفحات برای ایندکس سریع (Google & IndexNow)**، **کارخانه تولید محتوای هوشمند با ساختار اسکیما (AI Content Engine)** و **پایشگر سلامت فنی و ریدایرکت‌های ۳۰۱** را در قالبی راست‌چین (RTL) و واکنش‌گرا ارائه می‌دهد.

---

## ✨ امکانات کلیدی پلتفرم

### ۱. مدیریت همزمان چند وب‌سایت (Multi-Tenant Management)
* ثبت بی‌نهایت وب‌سایت و دامنه (فروشگاهی، شرکتی، خدماتی) به همراه شهر و صنف کاری.
* تعریف کلمات کلیدی هدف (Target Keywords) و صفحات فرود (Landing Pages) برای هر سایت به تفکیک.
* بررسی وضعیت کلی تمام سایت‌ها در یک نگاه با شاخص‌های کلیدی عملکرد (KPI).

### ۲. رصد لحظه‌ای و پایش جایگاه در گوگل (SERP Rank Tracker)
* استعلام زنده رتبه دامنه‌ها در کلمات کلیدی فارسی و محلی (مانند «تعمیرات تلویزیون در تبریز»).
* ثبت تاریخچه موقعیت‌ها و نمایش نمودار تفکیک کلمات در صفحه اول (Top 10)، صفحه دوم و صفحات بعدی.
* محاسبه خودکار میزان صعود یا نزول رتبه (Rank Volatility).

### ۳. کارخانه تولید محتوای هوشمند سئو (AI Content Autopilot)
* تولید خودکار مقالات تخصصی، بومی و کاربردی بر اساس شهر و صنف هدف.
* تولید خودکار کدهای ساختاریافته گوگل شامل **FAQ Schema** (`application/ld+json`).
* ذخیره مستقیم در پایگاه داده جهت انتشار در سایت یا خروجی برای وردپرس و سیستم‌های اختصاصی.

### ۴. ایندکس آنی و همگام‌سازی سریع (Instant Indexing Engine)
* ارسال مستقیم لینک صفحات جدید به پروتکل **IndexNow** (موتورهای جستجوی بینگ، یاندکس و سایرین).
* قابلیت خواندن مستقیم صفحات فعال از روی فایل **`sitemap.xml`** و ارسال دسته‌ای به صف ایندکس.
* ثبت تاریخچه و کدهای وضعیت پاسخ موتورهای جستجو در جدول لاگ‌ها.

### ۵. پایشگر سلامت فنی و ریدایرکت‌های ۳۰۱ (Technical SEO Auditor)
* ارزیابی امتیاز سلامت فنی (Technical Score) از ۰ تا ۱۰۰.
* اعتبارسنجی خودکار گواهی امنیتی HTTPS/SSL و سرعت پاسخ‌دهی سرور (Response Time).
* تست فعال بودن ریدایرکت ۳۰۱ نسخه www به غیر www.
* بررسی وجود تگ اصلی H1، تگ کنونیکال (Canonical)، فایل نقشه سایت و robots.txt.

---

## 🏗️ ساختار پروژه

```text
SEO-Command-Center/
├── app/
│   ├── main.py                  # اپلیکیشن اصلی FastAPI و روت‌های وب
│   ├── database.py              # ساختار پایگاه داده SQLite و مدل‌ها
│   ├── services/
│   │   ├── rank_tracker.py      # ماژول رصد و خزش موقعیت در سرپ گوگل
│   │   ├── indexer_service.py   # ماژول ارسال ایندکس فوری و IndexNow
│   │   ├── ai_content.py        # موتور تولید مقاله با ساختار اسکیما
│   │   └── health_auditor.py    # حسابرس سلامت فنی و ریدایرکت‌های ۳۰۱
│   ├── static/                  # فایل‌های استاتیک، فونت وزیرمتن و CSS
│   └── templates/               # قالب‌های HTML راست‌چین با طراحی مدرن
├── assets/
│   ├── intro-banner.png         # تصویر بنر اصلی معرفی
│   └── intro-banner.svg         # نسخه وکتور SVG بنر
├── data/                        # محل نگهداری دیتابیس SQLite
├── tests/                       # آزمون‌های خودکار و تست‌های واحد
├── run.py                       # اسکریپت راه‌اندازی سریع با باز کردن خودکار مرورگر
├── requirements.txt             # کتابخانه‌ها و وابستگی‌های پایتون
└── README.md                    # راهنمای کامل فارسی
```

---

## 🚀 راهنمای نصب و راه‌اندازی سریع

### پیش‌نیازها
* پایتون نسخه 3.10 یا بالاتر
* مرورگر مدرن (کروم، فایرفاکس، اج)

### گام ۱: کلون کردن مخزن
```bash
git clone https://github.com/taimazus/SEO-Command-Center.git
cd SEO-Command-Center
```

### گام ۲: نصب وابستگی‌ها
توصیه می‌شود از یک محیط مجازی (Virtual Environment) استفاده کنید:
```bash
python -m venv venv
# فعال‌سازی در ویندوز:
venv\Scripts\activate
# فعال‌سازی در لینوکس/مک:
source venv/bin/activate

pip install -r requirements.txt
```

### گام ۳: اجرای برنامه
کافیست دستور زیر را اجرا کنید:
```bash
python run.py
```
> با اجرای این دستور، سرور محلی روی آدرس **`http://127.0.0.1:8500`** فعال شده و داشبورد به طور خودکار در مرورگر پیش‌فرض شما باز خواهد شد!

---

## 🧪 اجرای آزمون‌های خودکار (Tests)

برای اطمینان از سلامت عملکرد تمام بخش‌ها و روت‌های پلتفرم:
```bash
python -m pytest tests -v
```

---

## 🎯 توسعه و نقشه راه آینده (Roadmap)
- [x] پنل وب کامل و چندسایته با داشبورد RTL
- [x] رصد زنده رتبه در سرپ گوگل (SERP Tracker)
- [x] موتور تولید محتوا به همراه FAQ Schema
- [x] ارسال ایندکس آنی (IndexNow) و تحلیل sitemap.xml
- [x] بررسی سلامت فنی سایت و خطاهای ریدایرکت ۳۰۱
- [ ] اتصال رسمی با Google Search Console API و Google Indexing API
- [ ] ربات ارسال اعلان روزانه به تلگرام و ایتا
- [ ] خروجی گزارش PDF ماهانه با لوگوی اختصاصی شرکت جهت ارائه به کارفرما

---

## 📄 مجوز انتشار (License)

این پروژه تحت مجوز متن‌باز **MIT** منتشر شده است. استفاده تجاری، توسعه و شخصی‌سازی آن برای کلیه توسعه‌دهندگان و شرکت‌ها آزاد است.

</div>

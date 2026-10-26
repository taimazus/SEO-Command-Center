import os
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.database import get_connection

ARTICLE_TEMPLATES = [
    {
        "pattern": "تعمیر بک لایت",
        "title_template": "راهنمای جامع تعمیر و تعویض بک لایت {brand} در {city} + هزینه و ضمانت",
        "intro": "قطع شدن نور تصویر، سیاه شدن صفحه در حالی که صدا پخش می‌شود یا ایجاد لکه‌های تاریک و روشن روی صفحه نمایش تلویزیون‌های {brand}، یکی از شایع‌ترین نشانه‌های سوختن شاخه‌های بک‌لایت (Backlight) است. در این مقاله تخصصی از مرکز تعمیرات تلویزیون {city}، به بررسی علل خرابی و مراحل تعویض اصولی قطعه می‌پردازیم.",
        "h2_1": "علائم خرابی بک لایت در تلویزیون‌های {brand}",
        "p_1": "شایع‌ترین نشانه‌ها عبارتند از: قطع ناگهانی تصویر پس از چند ثانیه روشن ماندن، چشمک زدن لوگو، آبی یا بنفش شدن نور پس‌زمینه در برخی مدل‌ها، و تاریک شدن نیمه بالا یا پایین صفحه نمایش.",
        "h2_2": "تفاوت تعمیر شاخه‌ای با تعویض دست کامل بک‌لایت",
        "p_2": "در بسیاری از تعمیرگاه‌های غیرمجاز، تنها LEDهای سوخته تعویض می‌شوند که این کار باعث برگشت خرابی در کمتر از ۳ ماه خواهد شد. استاندارد مرکز تخصصی {city}، تعویض کامل کلیه خطوط با شاخه‌های فابریک آلومینیومی همراه با هیت‌سینک خنک‌کننده و اعمال اصلاحیه برد تغذیه (Power Board Modification) جهت کاهش استهلاک ولتاژ است.",
        "h2_3": "مناطق تحت پوشش خدمات در محل در {city}",
        "p_3": "سرویس‌دهی سریع در منزل و محل کار در کلیه محلات و مناطق {city} (از جمله ولیعصر، آبرسان، یاغچیان، زعفرانیه، باغمیشه، مرزداران، ابوریحان، نصف راه و شهرک‌های صنعتی) با اعزام تکنسین و ضمانت کتبی قطعات انجام می‌شود."
    },
    {
        "pattern": "مین برد و پاور",
        "title_template": "علت روشن نشدن و چشمک زدن چراغ استندبای تلویزیون {brand} در {city}",
        "intro": "یکی از نگران‌کننده‌ترین ایرادات برای دارندگان تلویزیون {brand}، روشن نشدن دستگاه و گیر کردن روی حالت استندبای یا خاموش و روشن شدن مداوم (Reboot Loop) است. این مشکل معمولاً ناشی از اختلال در برد تغذیه یا نرم‌افزار مین‌برد (Mainboard) می‌باشد.",
        "h2_1": "بررسی قطعات آسیب‌پذیر در نوسانات برق",
        "p_1": "نوسانات شبکه برق شهری در فصول مختلف باعث خرابی خازن‌های صافی، سوختن ماسفت‌ها یا آی‌سی STR در برد پاور می‌شود. استفاده از دستگاه‌های اندازه‌گیری دقیق و تست پالس‌های خروجی جهت تعیین دقیق بخش معیوب الزامی است.",
        "h2_2": "پروگرام مجدد آی‌سی حافظه مین‌برد",
        "p_2": "در مواردی که تلویزیون روی لوگو متوقف می‌شود، برنامه‌ریزی مجدد ایپرام و ناند فلش (NAND/eMMC Flash) با استفاده از پروگرامرهای تخصصی RT809H بدون نیاز به تعویض کامل مین‌برد، هزینه تعمیرات را تا ۶۰ درصد کاهش می‌دهد.",
        "h2_3": "تعمیر در محل و تحویل فوری در {city}",
        "p_3": "کلیه خدمات عیب‌یابی بردهای الکترونیکی در {city} توسط کارشناسان باتجربه و مجهز به تجهیزات تست روز با قطعات اورجینال و تست کنترل کیفیت انجام می‌پذیرد."
    }
]

def generate_seo_article(site_id: int, topic: str, brand: str = "سامسونگ", city: str = "تبریز") -> Dict[str, Any]:
    conn = get_connection()
    site = conn.execute("SELECT name, domain, city FROM sites WHERE id = ?", (site_id,)).fetchone()
    if not site:
        conn.close()
        raise ValueError(f"Site ID {site_id} not found")

    target_city = city or site["city"] or "تبریز"

    # Match template or generate customized article
    template = ARTICLE_TEMPLATES[0]
    for tmpl in ARTICLE_TEMPLATES:
        if tmpl["pattern"] in topic:
            template = tmpl
            break

    title = template["title_template"].format(brand=brand, city=target_city)
    slug = re.sub(r'[\s\+]+', '-', title).replace('/', '-')

    content_html = f"""
    <article class="seo-article-content">
        <p class="lead">{template['intro'].format(brand=brand, city=target_city)}</p>

        <h2>{template['h2_1'].format(brand=brand, city=target_city)}</h2>
        <p>{template['p_1'].format(brand=brand, city=target_city)}</p>

        <h2>{template['h2_2'].format(brand=brand, city=target_city)}</h2>
        <p>{template['p_2'].format(brand=brand, city=target_city)}</p>

        <h2>{template['h2_3'].format(brand=brand, city=target_city)}</h2>
        <p>{template['p_3'].format(brand=brand, city=target_city)}</p>

        <div class="faq-box mt-4 p-3 bg-light rounded-3 border">
            <h3 class="h5 text-primary">پرسش‌های متداول مشتریان در {target_city}</h3>
            <div class="faq-item mb-2">
                <strong>آیا تعمیر تلویزیون {brand} در منزل انجام می‌شود؟</strong>
                <p>بله، اکثر خدمات عیب‌یابی، تعویض بک‌لایت و تعمیر بردهای پاور در محل مشتری در تمام نقاط {target_city} انجام می‌گیرد.</p>
            </div>
            <div class="faq-item">
                <strong>مدت زمان ضمانت قطعات چقدر است؟</strong>
                <p>کلیه قطعات تعویض شده شامل ضمانت کتبی و گارانتی اصالت ۶ تا ۱۲ ماهه می‌باشند.</p>
            </div>
        </div>

        <!-- FAQ Schema -->
        <script type="application/ld+json">
        {{
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {{
                    "@type": "Question",
                    "name": "آیا تعمیر تلویزیون {brand} در منزل در {target_city} انجام می‌شود؟",
                    "acceptedAnswer": {{
                        "@type": "Answer",
                        "text": "بله، اکثر خدمات عیب‌یابی و تعویض قطعات در محل مشتری در {target_city} انجام می‌گیرد."
                    }}
                }},
                {{
                    "@type": "Question",
                    "name": "مدت زمان ضمانت تعمیر تلویزیون {brand} چقدر است؟",
                    "acceptedAnswer": {{
                        "@type": "Answer",
                        "text": "کلیه قطعات تعویض شده شامل گارانتی کتبی ۶ تا ۱۲ ماهه مرکز تعمیرات هستند."
                    }}
                }}
            ]
        }}
        </script>
    </article>
    """

    meta_desc = f"مرکز تخصصی تعمیرات تلویزیون {brand} در {target_city} با قطعات فابریک، خدمات در منزل و گارانتی کتبی. اعزام فوری تکنسین در کلیه محلات {target_city}."
    keywords_used = f"تعمیر تلویزیون {brand} در {target_city}, تعمیرات تلویزیون {target_city}, تعویض بک لایت {brand}, تعمیر برد تلویزیون {target_city}"

    # Insert into database
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO articles (
            site_id, title, slug, category, summary, content_html,
            keywords_used, meta_description, status, published_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'published', ?)
    """, (
        site_id, title, slug, f"تعمیرات {brand}",
        template['intro'].format(brand=brand, city=target_city)[:200],
        content_html, keywords_used, meta_desc,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    article_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "article_id": article_id,
        "title": title,
        "slug": slug,
        "keywords_used": keywords_used,
        "meta_description": meta_desc,
        "status": "published"
    }

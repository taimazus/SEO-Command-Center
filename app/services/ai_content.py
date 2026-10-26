import os
import json
import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.database import get_connection

logger = logging.getLogger(__name__)

# Specialized Niche Configurations & Intelligent Multi-Site Generator

NICHE_CONFIGS = {
    "gamification": {
        "keywords": ["گردونه", "اسپینورا", "شانس", "گیمیفیکیشن", "بازی", "قرعه", "spinora", "تخفیف"],
        "topics": [
            "راهنمای جامع راه‌اندازی گردونه شانس آنلاین برای افزایش فروش و نرخ تبدیل",
            "اصول بازاریابی سرگرمی (Gamification) در فروشگاه‌های اینترنتی و جذب مشتری",
            "استراتژی‌های اهدای کد تخفیف و جوایز هوشمندانه به کاربران برای افزایش لید",
            "چگونه با گردونه جوایز نرخ ماندگاری کاربر (Dwell Time) و سئو سایت را بالا ببریم؟",
            "روانشناسی تخفیف و وفادارسازی مشتریان با مسابقات و بازی‌های آنلاین"
        ],
        "default_keyword": "گردونه شانس",
        "default_location": "ایران (آنلاین)",
        "content_templates": [
            {
                "title": "راهنمای جامع راه‌اندازی {keyword} برای افزایش چشمگیر فروش و جذب لید",
                "intro": "در دنیای تجارت الکترونیک امروز، یکی از موثرترین راهکارهای افزایش تعامل کاربر و جهش نرخ تبدیل (Conversion Rate)، استفاده از {keyword} و تکنیک‌های گیمیفیکیشن (بازی‌وارسازی) است. پلتفرم {site_name} با ارائه راهکارهای نوین بازاریابی سرگرمی به کسب‌وکارها کمک می‌کند تا بازدیدکنندگان عادی را به خریداران وفادار تبدیل کنند.",
                "h2_1": "چرا استفاده از {keyword} نرخ تبدیل فروشگاه‌ها را متحول می‌کند؟",
                "p_1": "تحقیقات حوزه رفتار مصرف‌کننده نشان می‌دهد که عنصر شانس و پاداش فوری، دوپامین مغز کاربر را فعال کرده و میل به خرید را تا ۷۰ درصد افزایش می‌دهد. با تعبیه {keyword}، کاربر به جای ترک سایت، شماره تماس یا ایمیل خود را برای دریافت یک کوپن تخفیف ثبت می‌کند که این امر قوی‌ترین آهنربای جذب لید (Lead Magnet) محسوب می‌شود.",
                "h2_2": "نکات طلایی در طراحی جوایز و کدهای تخفیف ترغیب‌کننده",
                "p_2": "یک کمپین موفق باید بین جوایز بزرگ (انگیزه اولیه) و کدهای تخفیف با درصد معقول (انگیزه خرید فوری) تعادل برقرار کند. در سیستم هوشمند {site_name}، می‌توانید سقف استفاده از هر جایزه، حداقل مبلغ سفارش برای فعال‌سازی کوپن، و مدت زمان اعتبار (مثلاً ۲۴ ساعت برای ایجاد حس فوریت FOMO) را به دقت تنظیم نمایید.",
                "h2_3": "تاثیر مثبت گیمیفیکیشن بر سئو و ماندگاری کاربر در سایت",
                "p_3": "گوگل به فاکتورهایی نظیر مدت زمان ماندگاری کاربر در صفحه (Dwell Time) و کاهش نرخ پرش (Bounce Rate) اهمیت فراوانی می‌دهد. بازی با {keyword} زمان حضور کاربر در سایت را چند برابر کرده و سیگنال‌های مثبت فوق‌العاده‌ای به الگوریتم‌های رتبه‌بندی موتور جستجو ارسال می‌کند.",
                "faqs": [
                    {
                        "q": "آیا استفاده از {keyword} برای انواع فروشگاه‌های اینترنتی مناسب است؟",
                        "a": "بله، از فروشگاه‌های لباس و لوازم آرایشی تا پلتفرم‌های ارائه‌دهنده خدمات و دوره‌های آموزشی می‌توانند از {keyword} برای ایجاد هیجان خرید استفاده کنند."
                    },
                    {
                        "q": "چگونه می‌توان جلوی تقلب و سوءاستفاده از جوایز را گرفت؟",
                        "a": "سیستم {site_name} با اعتبارسنجی پیامکی شماره موبایل، محدودیت آی‌پی (IP Limit) و ثبت کوکی مانع از چرخاندن چندباره توسط یک کاربر می‌شود."
                    },
                    {
                        "q": "آیا کدهای تخفیف مستقیماً به پنل پیامکی یا ووکامرس متصل می‌شوند؟",
                        "a": "بله، کدهای تخفیف تولید شده بلافاصله برای کاربر پیامک شده و با سبد خرید سایت فروشگاهی شما همگام‌سازی می‌شوند."
                    }
                ]
            }
        ]
    },
    "tv_repair": {
        "keywords": ["تعمیر", "تلویزیون", "بک لایت", "ال سی دی", "ال ای دی", "برد", "سامسونگ", "ال جی", "سونی", "اسنوا"],
        "topics": [
            "راهنمای جامع تعمیر و تعویض بک لایت {keyword} در {city} + هزینه و ضمانت",
            "علت روشن نشدن و چشمک زدن چراغ استندبای تلویزیون {keyword} در {city}",
            "تعمیر تخصصی فلت و پنل آبخورده تلویزیون با دستگاه باندینگ در {city}",
            "خدمات فوری عیب‌یابی و تعمیر تلویزیون در منزل و محل کار در {city}",
            "بررسی تخصصی تفاوت تعمیر مین‌برد و تعویض قطعات در {city}"
        ],
        "default_keyword": "سامسونگ",
        "default_location": "تبریز",
        "content_templates": [
            {
                "title": "راهنمای جامع تعمیر و عیب‌یابی تخصصی تلویزیون {keyword} در {city} + ضمانت کتبی",
                "intro": "قطع ناگهانی تصویر، سیاه شدن صفحه با وجود پخش صدا، چشمک زدن مداوم چراغ پاور یا خطوط عمودی و افقی روی نمایشگر، از شایع‌ترین ایرادات تلویزیون‌های {keyword} است. مرکز تخصصی {site_name} به عنوان مجهزترین پایگاه عیب‌یابی در {city}، خدمات در محل و منزل را با قطعات فابریک ارائه می‌دهد.",
                "h2_1": "شایع‌ترین نشانه‌های خرابی سخت‌افزاری در تلویزیون {keyword}",
                "p_1": "سوختن دیودهای بک‌لایت بر اثر کارکرد مداوم و حرارت بالا، سوختگی خازن‌ها و رگولاتورهای برد پاور به دلیل نوسان برق، و اختلال در آی‌سی پردازنده مین‌برد از عمده‌ترین دلایل از کار افتادن تلویزیون است. تشخیص دقیق بخش معیوب نیازمند تجهیزات عیب‌یابی دیجیتال است.",
                "h2_2": "تعمیر در منزل و محل مشتری در سراسر {city}",
                "p_2": "جابه‌جایی تلویزیون‌های سایز بزرگ ریسک شکستگی و آسیب به صفحه پنل را به همراه دارد. تکنسین‌های مجرب {site_name} مجهز به کلیه ابزارهای تشخیصی و قطعات پرمصرف در کوتاه‌ترین زمان به محل مشتری اعزام شده و تعمیرات اولیه را در حضور شما انجام می‌دهند.",
                "h2_3": "استفاده از قطعات فابریک شرکتی همراه با هیت‌سینک و اصلاحیه ولتاژ",
                "p_3": "در مرکز {site_name} برای افزایش طول عمر تلویزیون، همراه با تعویض شاخه‌های بک‌لایت فابریک آلومینیومی، اصلاحیه ولتاژ روی برد پاور اعمال می‌گردد تا جریان ورودی تنظیم شده و از خرابی مجدد تا سال‌ها جلوگیری شود.",
                "faqs": [
                    {
                        "q": "آیا تعمیر تلویزیون {keyword} در منزل در {city} انجام می‌شود؟",
                        "a": "بله، اکثریت خرابی‌های متداول از جمله تعویض بک‌لایت و تعمیر بردهای تغذیه در محل مشتری در کلیه محلات {city} انجام می‌گیرد."
                    },
                    {
                        "q": "مدت زمان ضمانت قطعات تعویض شده چقدر است؟",
                        "a": "کلیه قطعات و خدمات ارائه شده شامل ضمانت کتبی ۶ تا ۱۲ ماهه مرکز {site_name} هستند."
                    },
                    {
                        "q": "هزینه تعمیر تلویزیون چگونه محاسبه می‌شود؟",
                        "a": "هزینه بر اساس مدل دقیق دستگاه، سایز اینچ، و قطعه معیوب مطابق با نرخ مصوب اتحادیه محاسبه و قبل از آغاز کار به مشتری اعلام می‌گردد."
                    }
                ]
            }
        ]
    },
    "general": {
        "keywords": [],
        "topics": [
            "راهنمای جامع انتخاب و بهره‌برداری از بهترین خدمات {keyword}",
            "بررسی ویژگی‌ها، مزایا و نکات کلیدی در خرید یا سفارش {keyword}",
            "پاسخ به مهم‌ترین دغدغه‌ها و سوالات پرتکرار کاربران درباره {keyword}",
            "معیارهای ارزیابی کیفیت و استانداردهای برتر {keyword} در بازار"
        ],
        "default_keyword": "خدمات تخصصی",
        "default_location": "سراسری",
        "content_templates": [
            {
                "title": "راهنمای تخصصی {keyword} | معرفی خدمات و راهکارهای نوین {site_name}",
                "intro": "در دنیای پرشتاب امروز، دسترسی به خدمات حرفه‌ای، قابل اعتماد و به‌روز در زمینه {keyword} یکی از نیازهای اصلی مشتریان و کسب‌وکارهاست. مجموعه {site_name} با تکیه بر استانداردهای بین‌المللی و تیمی متخصص، بهترین راهکارها را در اختیار شما قرار می‌دهد.",
                "h2_1": "اهمیت و مزایای برجسته استفاده از خدمات تخصصی {keyword}",
                "p_1": "انتخاب یک راهکار حرفه‌ای در حوزه {keyword} نه تنها هزینه‌های جانبی و اتلاف زمان را به حداقل می‌رساند، بلکه بازدهی نهایی و کیفیت نتیجه را تضمین می‌نماید. شناخت دقیق نیازها و بهره‌گیری از تجربه کارشناسان در این مسیر نقش اساسی دارد.",
                "h2_2": "ویژگی‌های متمایز {site_name} در ارائه خدمات {keyword}",
                "p_2": "شفافیت در هزینه‌ها، پشتیبانی مستمر و استفاده از روش‌های مدرن و تست‌شده، از مزیت‌های رقابتی {site_name} است که اطمینان خاطر را برای کاربران به همراه می‌آورد.",
                "h2_3": "راهنمای گام به گام شروع و ثبت سفارش در {city}",
                "p_3": "برای شروع، کافی است نیازمندی خود را از طریق درگاه‌های ارتباطی با مشاوران ما مطرح کنید تا مناسب‌ترین راهکار متناسب با نیاز و بودجه شما تدوین و پیاده‌سازی گردد.",
                "faqs": [
                    {
                        "q": "چگونه می‌توان بهترین نتیجه را از خدمات {keyword} گرفت؟",
                        "a": "تعریف دقیق اهداف و مشاوره اولیه با تیم تخصصی {site_name} مسیر رسیدن به بهترین نتیجه را هموار می‌سازد."
                    },
                    {
                        "q": "آیا خدمات مشاوره و پشتیبانی پس از تحویل ارائه می‌شود؟",
                        "a": "بله، پشتیبانی همه‌جانبه و پیگیری رضایت مشتریان از اصول بنیادین {site_name} است."
                    }
                ]
            }
        ]
    }
}

def detect_site_niche(site_name: str, site_domain: str, category: str, keywords: List[str]) -> str:
    combined = f"{site_name} {site_domain} {category} {' '.join(keywords)}".lower()
    
    # Check gamification / spinora
    for kw in NICHE_CONFIGS["gamification"]["keywords"]:
        if kw.lower() in combined:
            return "gamification"
            
    # Check TV repair
    for kw in NICHE_CONFIGS["tv_repair"]["keywords"]:
        if kw.lower() in combined:
            return "tv_repair"
            
    return "general"

def get_suggested_topics_for_site(site_id: int) -> List[Dict[str, str]]:
    """Returns dynamic, intelligent topic recommendations tailored to the specific site."""
    conn = get_connection()
    site = conn.execute("SELECT name, domain, category, city FROM sites WHERE id = ?", (site_id,)).fetchone()
    if not site:
        conn.close()
        return []
        
    kw_rows = conn.execute("SELECT keyword FROM keywords WHERE site_id = ?", (site_id,)).fetchall()
    site_keywords = [k["keyword"] for k in kw_rows]
    conn.close()
    
    niche_key = detect_site_niche(site["name"], site["domain"], site["category"] or "", site_keywords)
    config = NICHE_CONFIGS.get(niche_key, NICHE_CONFIGS["general"])
    
    primary_kw = site_keywords[0] if site_keywords else config["default_keyword"]
    city = site["city"] or config["default_location"]
    
    topics = []
    for raw_topic in config["topics"]:
        formatted = raw_topic.format(keyword=primary_kw, city=city, site_name=site["name"])
        topics.append({
            "id": formatted,
            "title": formatted,
            "niche": niche_key
        })
    return topics

def generate_seo_article(site_id: int, topic: str, brand: str = "", city: str = "") -> Dict[str, Any]:
    conn = get_connection()
    site = conn.execute("SELECT name, domain, category, city FROM sites WHERE id = ?", (site_id,)).fetchone()
    if not site:
        conn.close()
        raise ValueError(f"Site ID {site_id} not found")

    kw_rows = conn.execute("SELECT keyword FROM keywords WHERE site_id = ?", (site_id,)).fetchall()
    site_keywords = [k["keyword"] for k in kw_rows]
    
    site_name = site["name"]
    site_domain = site["domain"]
    niche_key = detect_site_niche(site_name, site_domain, site["category"] or "", site_keywords)
    config = NICHE_CONFIGS.get(niche_key, NICHE_CONFIGS["general"])
    
    target_keyword = brand.strip() if brand and brand.strip() else (site_keywords[0] if site_keywords else config["default_keyword"])
    target_city = city.strip() if city and city.strip() else (site["city"] or config["default_location"])
    
    # Pick suitable template
    tmpl = config["content_templates"][0]
    
    # Check if custom topic entered
    if topic and topic != "custom":
        custom_headline = topic
    else:
        custom_headline = tmpl["title"].format(keyword=target_keyword, city=target_city, site_name=site_name)

    title = custom_headline
    slug = re.sub(r'[\s\+\/\|]+', '-', title).strip('-')
    
    intro_text = tmpl["intro"].format(keyword=target_keyword, city=target_city, site_name=site_name)
    h2_1 = tmpl["h2_1"].format(keyword=target_keyword, city=target_city, site_name=site_name)
    p_1 = tmpl["p_1"].format(keyword=target_keyword, city=target_city, site_name=site_name)
    h2_2 = tmpl["h2_2"].format(keyword=target_keyword, city=target_city, site_name=site_name)
    p_2 = tmpl["p_2"].format(keyword=target_keyword, city=target_city, site_name=site_name)
    h2_3 = tmpl["h2_3"].format(keyword=target_keyword, city=target_city, site_name=site_name)
    p_3 = tmpl["p_3"].format(keyword=target_keyword, city=target_city, site_name=site_name)
    
    # Render FAQs
    faq_items_html = ""
    faq_schema_list = []
    for faq in tmpl["faqs"]:
        q = faq["q"].format(keyword=target_keyword, city=target_city, site_name=site_name)
        a = faq["a"].format(keyword=target_keyword, city=target_city, site_name=site_name)
        faq_items_html += f"""
        <div class="faq-item mb-3">
            <strong class="text-dark"><i class="fas fa-question-circle text-primary me-1"></i>{q}</strong>
            <p class="text-muted mt-1 mb-0">{a}</p>
        </div>
        """
        faq_schema_list.append({
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": a
            }
        })
        
    faq_schema_json = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": faq_schema_list
    }, ensure_ascii=False, indent=2)

    content_html = f"""
    <article class="seo-article-content">
        <p class="lead">{intro_text}</p>

        <h2>{h2_1}</h2>
        <p>{p_1}</p>

        <h2>{h2_2}</h2>
        <p>{p_2}</p>

        <h2>{h2_3}</h2>
        <p>{p_3}</p>

        <div class="faq-box mt-4 p-4 bg-light rounded-4 border">
            <h3 class="h5 text-primary mb-3"><i class="fas fa-comments me-2"></i>پرسش‌های متداول کاربران درباره {target_keyword}</h3>
            {faq_items_html}
        </div>

        <!-- Google FAQ Schema -->
        <script type="application/ld+json">
        {faq_schema_json}
        </script>
    </article>
    """

    meta_desc = f"{intro_text[:155]}..."
    keywords_used = f"{target_keyword}, {site_name}, {site_domain}, {target_city}"

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO articles (
            site_id, title, slug, category, summary, content_html,
            keywords_used, meta_description, status, published_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'published', ?)
    """, (
        site_id, title, slug, f"{site['category'] or 'سئو و محتوا'}",
        intro_text[:190],
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

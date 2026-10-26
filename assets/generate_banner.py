import os
from PIL import Image, ImageDraw, ImageFont

def generate_intro_banner(output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    width = 1200
    height = 630

    # Modern Dark Gradient / Tech Navy Background
    img = Image.new("RGB", (width, height), color="#0f172a")
    draw = ImageDraw.Draw(img)

    # Gradient simulated lines / cards
    for y in range(height):
        # subtle top-to-bottom navy gradient #0f172a to #1e293b
        r = int(15 + (30 - 15) * (y / height))
        g = int(23 + (41 - 23) * (y / height))
        b = int(42 + (59 - 42) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Glow effects in corners (Teal / Indigo circles)
    # Circle 1 - Top Left
    draw.ellipse([-100, -100, 400, 400], fill="#1e1b4b")
    # Circle 2 - Bottom Right
    draw.ellipse([800, 300, 1300, 800], fill="#042f2e")

    # Central Card container
    draw.rounded_rectangle([60, 60, width - 60, height - 60], radius=24, fill="#1e293b", outline="#334155", width=2)

    # Accent decorative bar on top of card
    draw.rounded_rectangle([62, 62, width - 62, 74], radius=6, fill="#3b82f6")

    # Badges
    draw.rounded_rectangle([100, 100, 310, 140], radius=12, fill="#0284c7")
    draw.text((120, 110), "SEO COMMAND CENTER", fill="#ffffff")

    draw.rounded_rectangle([325, 100, 520, 140], radius=12, fill="#10b981")
    draw.text((345, 110), "MULTI-SITE PLATFORM", fill="#ffffff")

    draw.rounded_rectangle([535, 100, 680, 140], radius=12, fill="#8b5cf6")
    draw.text((555, 110), "AI AUTOPILOT", fill="#ffffff")

    # Main Headline
    draw.text((100, 175), "مرکز فرماندهی و اتوماسیون سئو چندسایته", fill="#f8fafc")
    draw.text((100, 240), "SEO Command Center - Multi-Tenant SEO & SERP Autopilot", fill="#94a3b8")

    # Feature Grid Cards (4 cards)
    # Card 1: Multi-Site Manager
    draw.rounded_rectangle([100, 310, 340, 470], radius=16, fill="#0f172a", outline="#38bdf8", width=2)
    draw.text((120, 330), "مدیریت چندسایته", fill="#38bdf8")
    draw.text((120, 370), "پشتیبانی همزمان از ده‌ها", fill="#cbd5e1")
    draw.text((120, 400), "دامنه، فروشگاه و پرتال", fill="#cbd5e1")
    draw.text((120, 430), "با تفکیک پروژه و کلمات", fill="#94a3b8")

    # Card 2: SERP Rank Tracker
    draw.rounded_rectangle([360, 310, 600, 470], radius=16, fill="#0f172a", outline="#34d399", width=2)
    draw.text((380, 330), "رصد زنده رتبه گوگل", fill="#34d399")
    draw.text((380, 370), "پایش لحظه‌ای موقعیت نتایج", fill="#cbd5e1")
    draw.text((380, 400), "در نتایج سرپ ارگانیک و مپ", fill="#cbd5e1")
    draw.text((380, 430), "همراه با نمودار تغییرات", fill="#94a3b8")

    # Card 3: AI Content Engine
    draw.rounded_rectangle([620, 310, 860, 470], radius=16, fill="#0f172a", outline="#a78bfa", width=2)
    draw.text((640, 330), "تولید محتوای هوشمند", fill="#a78bfa")
    draw.text((640, 370), "تولید مقالات بومی و عمیق", fill="#cbd5e1")
    draw.text((640, 400), "اسکیما مارک‌آپ خودکار", fill="#cbd5e1")
    draw.text((640, 430), "انتشار مستقیم در دیتابیس", fill="#94a3b8")

    # Card 4: Health & Instant Index
    draw.rounded_rectangle([880, 310, 1100, 470], radius=16, fill="#0f172a", outline="#f59e0b", width=2)
    draw.text((900, 330), "ایندکس آنی و سلامت", fill="#f59e0b")
    draw.text((900, 370), "ارسال سریع به گوگل و بینگ", fill="#cbd5e1")
    draw.text((900, 400), "تست خطاهای ۳۰۱ و SSL", fill="#cbd5e1")
    draw.text((900, 430), "امتیاز سلامت فنی ۱۰۰/۱۰۰", fill="#94a3b8")

    # Footer banner bar inside card
    draw.rounded_rectangle([100, 500, 1100, 545], radius=10, fill="#0f172a")
    draw.text((120, 515), "Open-Source Python (FastAPI) Multi-Tenant SEO Platform | Developed for Taimazus & Digital Agencies", fill="#64748b")

    img.save(output_path, "PNG")
    print("Generated intro banner at:", output_path)

if __name__ == "__main__":
    generate_intro_banner("C:/Users/Taimazus/Desktop/SEO-Command-Center/assets/intro-banner.png")
    generate_intro_banner("C:/Users/Taimazus/Desktop/SEO-Command-Center/app/static/images/intro-banner.png")

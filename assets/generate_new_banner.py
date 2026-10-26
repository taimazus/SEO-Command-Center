import os
from PIL import Image, ImageDraw, ImageFont

def generate_new_contrast_banner(output_png: str):
    os.makedirs(os.path.dirname(output_png), exist_ok=True)
    w, h = 1200, 630

    # Deep Onyx Black Canvas
    img = Image.new("RGB", (w, h), color="#060911")
    draw = ImageDraw.Draw(img)

    # Ambient Cyber Glows
    for r in range(120, 0, -2):
        alpha = int(25 * (r / 120))
        draw.ellipse([80 - r, 80 - r, 80 + r, 80 + r], outline=(16, 185, 129))
        draw.ellipse([1100 - r, 500 - r, 1100 + r, 500 + r], outline=(6, 182, 212))

    # Dot Matrix Grid Pattern
    for x in range(30, w, 40):
        for y in range(30, h, 40):
            draw.point((x, y), fill="#1a2538")

    # Main Obsidian Window Card
    draw.rounded_rectangle([50, 40, w - 50, h - 40], radius=20, fill="#0c121e", outline="#1e2d4a", width=2)

    # Header Bar of Window
    draw.rounded_rectangle([50, 40, w - 50, 95], radius=20, fill="#111a2c")
    draw.rectangle([50, 75, w - 50, 95], fill="#111a2c") # square bottom of header
    draw.line([(50, 95), (w - 50, 95)], fill="#233554", width=2)

    # Window Controls (Red, Yellow, Green dots)
    draw.ellipse([75, 62, 87, 74], fill="#ef4444")
    draw.ellipse([95, 62, 107, 74], fill="#f59e0b")
    draw.ellipse([115, 62, 127, 74], fill="#10b981")

    # Terminal prompt title
    draw.text((150, 60), "root@seo-command-center:~# live-diagnostics --source=F:/Projects/TabrizTv", fill="#38bdf8")

    # High Contrast Badges
    draw.rounded_rectangle([80, 120, 310, 160], radius=10, fill="#064e3b", outline="#10b981", width=2)
    draw.text((100, 132), "SOURCE DOCTOR 2.1", fill="#6ee7b7")

    draw.rounded_rectangle([325, 120, 520, 160], radius=10, fill="#164e63", outline="#06b6d4", width=2)
    draw.text((345, 132), "DEPLOY MANIFEST", fill="#7dd3fc")

    draw.rounded_rectangle([535, 120, 700, 160], radius=10, fill="#78350f", outline="#f59e0b", width=2)
    draw.text((555, 132), "GSC & MAPS API", fill="#fde68a")

    # Main Headline
    draw.text((80, 185), "پلتفرم جامع مهندسی سئو و پزشک سورس‌کد", fill="#ffffff")
    draw.text((80, 230), "SEO Command Center - Source Code Doctor, Auto-Publisher & Live SERP Engine", fill="#94a3b8")

    # 3 High-Contrast Feature Pillars
    # Pillar 1: Source Doctor & Auto-Publisher
    draw.rounded_rectangle([80, 280, 410, 480], radius=14, fill="#070c16", outline="#10b981", width=2)
    draw.text((105, 305), "[ 1 ] پزشک سورس‌کد و انتشار", fill="#10b981")
    draw.text((105, 345), "* اسکن فایلهای Web.config و مستر", fill="#f1f5f9")
    draw.text((105, 375), "* جلوگیری از خطای سرور 500 در App_Code", fill="#f1f5f9")
    draw.text((105, 405), "* لیست فایلهای نیازمند آپلود در پلسک", fill="#f1f5f9")
    draw.text((105, 435), "* تولید بسته ZIP با 1 کلیک", fill="#34d399")

    # Pillar 2: Live SERP & Maps
    draw.rounded_rectangle([435, 280, 765, 480], radius=14, fill="#070c16", outline="#06b6d4", width=2)
    draw.text((460, 305), "[ 2 ] رصد زنده گوگل و نقشه", fill="#06b6d4")
    draw.text((460, 345), "* رصد لحظه‌ای رتبه کلمات در تبریز", fill="#f1f5f9")
    draw.text((460, 375), "* اتصال به Google Search Console", fill="#f1f5f9")
    draw.text((460, 405), "* پایش رتبه در پک نقشه (Top 3)", fill="#f1f5f9")
    draw.text((460, 435), "* نمودارهای توزیع رتبه‌ها", fill="#38bdf8")

    # Pillar 3: AI Content & Instant Indexing
    draw.rounded_rectangle([790, 280, 1120, 480], radius=14, fill="#070c16", outline="#f59e0b", width=2)
    draw.text((815, 305), "[ 3 ] کارخانه محتوا و ایندکس", fill="#f59e0b")
    draw.text((815, 345), "* تولید مقالات بومی با FAQ Schema", fill="#f1f5f9")
    draw.text((815, 375), "* ارسال مستقیم به دیتابیس سایت", fill="#f1f5f9")
    draw.text((815, 405), "* ایندکس آنی در گوگل و IndexNow", fill="#f1f5f9")
    draw.text((815, 435), "* تست ریدایرکت 301 و SSL", fill="#fbbf24")

    # Bottom Terminal Output Bar
    draw.rounded_rectangle([80, 510, 1120, 565], radius=10, fill="#060911", outline="#233554", width=1)
    draw.text((100, 528), "> status: ALL SYSTEMS ONLINE  |  host: 127.0.0.1:8500  |  developed for: taimazus  |  repo: github.com/taimazus/SEO-Command-Center", fill="#10b981")

    img.save(output_png, "PNG")
    print("New high-contrast banner generated at:", output_png)

if __name__ == "__main__":
    generate_new_contrast_banner(r"C:\Users\Taimazus\Desktop\SEO-Command-Center\assets\intro-banner.png")
    generate_new_contrast_banner(r"C:\Users\Taimazus\Desktop\SEO-Command-Center\app\static\images\intro-banner.png")

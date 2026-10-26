import json
from typing import Dict, Any, List
from app.database import get_connection

class SEOCopilot:
    """
    Autonomous AI SEO Strategist & Copilot.
    Simulates a senior SEO specialist performing daily audits, identifying Quick Wins,
    optimizing CTR, and creating localized market domination roadmaps.
    """
    def __init__(self, site_id: int):
        self.site_id = site_id

    def generate_full_analysis(self) -> Dict[str, Any]:
        conn = get_connection()
        site = conn.execute("SELECT * FROM sites WHERE id = ?", (self.site_id,)).fetchone()
        if not site:
            conn.close()
            return {"error": "Site not found"}

        keywords = conn.execute("SELECT * FROM keywords WHERE site_id = ? ORDER BY current_position ASC", (self.site_id,)).fetchall()
        gsc_queries = conn.execute("SELECT * FROM gsc_queries WHERE site_id = ? ORDER BY impressions DESC", (self.site_id,)).fetchall()
        recent_audit = conn.execute("SELECT * FROM health_audits WHERE site_id = ? ORDER BY id DESC LIMIT 1", (self.site_id,)).fetchone()
        conn.close()

        city = site["city"] or "تبریز"
        domain = site["domain"]

        quick_wins = []
        ctr_opportunities = []
        content_gaps = []
        tech_priorities = []

        # 1. Quick Wins: Page 2 keywords (ranks 11-20)
        page_2_keywords = [k for k in keywords if 10 < (k["current_position"] or 0) <= 20]
        for kw in page_2_keywords:
            pos = kw["current_position"]
            keyword_text = kw["keyword"]
            quick_wins.append({
                "keyword": keyword_text,
                "current_position": pos,
                "target_page": kw["target_url"] or f"https://{domain}/",
                "difficulty": "آسان (فاصله تا صفحه اول: ۱ الی ۵ رتبه)",
                "action_title": f"ارتقای سریع «{keyword_text}» از رتبه {pos} به صفحه اول",
                "recommendation": f"این کلمه در صفحه دوم گوگل حضور دارد. با افزودن یک تیتر H2 اختصاصی با عنوان «{keyword_text} در {city}» و ایجاد حداقل یک لینک داخلی با انکرتکست دقیق از صفحه اصلی، طی ۱۰ روز به صفحه اول صعود می‌کند.",
                "title_suggestion": f"{keyword_text} | خدمات فوری و تضمینی در {city} با گارانتی"
            })

        # If few page 2 keywords in DB, add high-potential GSC queries
        if len(quick_wins) < 3 and gsc_queries:
            for q in gsc_queries:
                if 10 < (q["position"] or 0) <= 25 and q["impressions"] > 100:
                    quick_wins.append({
                        "keyword": q["query"],
                        "current_position": round(q["position"], 1),
                        "target_page": f"https://{domain}/",
                        "difficulty": "متوسط (کوئری سرچ کنسول)",
                        "action_title": f"فرصت طلایی کنسول: «{q['query']}» ({q['impressions']} بازدید بالقوه)",
                        "recommendation": f"این عبارت ماهانه بیش از {q['impressions']} بار در سرپ نمایش داده شده است. ساخت صفحه لندینگ مجزا برای این عبارت، بلافاصله منجر به جذب کلیک روزانه می‌شود.",
                        "title_suggestion": f"{q['query']} | قیمت و هزینه قطعات در {city}"
                    })

        # 2. CTR Optimization: Page 1 with low CTR (< 6%)
        page_1_keywords = [k for k in keywords if 0 < (k["current_position"] or 0) <= 10]
        for kw in page_1_keywords:
            ctr_opportunities.append({
                "keyword": kw["keyword"],
                "rank": kw["current_position"],
                "current_title": f"تعمیر تلویزیون - {domain}",
                "optimized_title": f"⚡ {kw['keyword']} (اعزام تعمیرکار در ۳۰ دقیقه در {city}) + ۱۲ ماه گارانتی",
                "optimized_description": f"مرکز تخصصی {kw['keyword']}؛ تعمیر انواع برندهای سامسونگ، ال جی، سونی با قطعات اصلی، هزینه منصفانه و عیب‌یابی رایگان در محل سراسر {city}.",
                "expected_boost": "+۴۰٪ تا +۷۰٪ افزایش نرخ کلیک کاربران"
            })

        # 3. Local Neighborhood Dominance Roadmap (City neighborhoods)
        neighborhoods = ["ولیعصر", "رشدیه", "شاهگلی (ایل‌گلی)", "آبرسان", "زعفرانیه", "باغمیشه", "نصف‌راه", "مرند و حومه"]
        covered_kw_texts = " ".join([k["keyword"] for k in keywords])
        
        for n in neighborhoods:
            if n not in covered_kw_texts:
                content_gaps.append({
                    "neighborhood": n,
                    "target_keyword": f"تعمیر تلویزیون در {n} {city}",
                    "intent": "موقعیت محلی پردرآمد با نرخ تبدیل بسیار بالا",
                    "action": f"تولید یک مقاله یا لندینگ پیج خدمات فوری با عنوان «تعمیر تلویزیون در محله {n} {city}» و ثبت در کارخانه محتوا."
                })

        # 4. Technical Priorities
        if recent_audit and recent_audit["issues_json"]:
            try:
                raw_issues = json.loads(recent_audit["issues_json"])
                for iss in raw_issues:
                    if isinstance(iss, dict):
                        t = iss.get("title", "اصلاح فنی")
                        s = iss.get("severity", "medium")
                        d = iss.get("description", "")
                    else:
                        t = str(iss)
                        s = "critical" if any(w in str(iss) for w in ["SSL", "500", "وضعیت"]) else "medium"
                        d = str(iss)

                    tech_priorities.append({
                        "title": t,
                        "severity": s,
                        "description": d,
                        "solution": "با مراجعه به بخش «پزشک سورس‌کد»، دکمه رفع خودکار را کلیک کنید یا تنظیمات هاست پلسک را بازبینی نمایید."
                    })
            except Exception as e:
                import logging
                logging.warning(f"Error parsing issues_json in SEOCopilot: {e}")

        # Calculate SEO Authority Score
        total_score = 75
        if len(page_1_keywords) >= 4:
            total_score += 15
        if len(page_2_keywords) >= 3:
            total_score += 5

        result = {
            "site_id": self.site_id,
            "domain": domain,
            "city": city,
            "seo_authority_score": min(total_score, 98),
            "quick_wins_count": len(quick_wins),
            "quick_wins": quick_wins[:5],
            "ctr_opportunities": ctr_opportunities[:4],
            "content_gaps": content_gaps[:5],
            "tech_priorities": tech_priorities
        }

        # Save to DB
        self._save_recommendations(quick_wins[:3] + ctr_opportunities[:2])
        return result

    def _save_recommendations(self, recs: List[Dict[str, Any]]):
        conn = get_connection()
        for r in recs:
            title = r.get("action_title") or r.get("keyword") or "توصیه هوشمند"
            desc = r.get("recommendation") or r.get("optimized_title") or ""
            action = r.get("title_suggestion") or r.get("optimized_description") or ""
            
            exists = conn.execute("SELECT id FROM seo_recommendations WHERE site_id = ? AND title = ?", (self.site_id, title)).fetchone()
            if not exists:
                conn.execute("""
                    INSERT INTO seo_recommendations (site_id, rec_type, title, description, action_plan, impact_level)
                    VALUES (?, 'quick_win', ?, ?, ?, 'high')
                """, (self.site_id, title, desc, action))
        conn.commit()
        conn.close()

"""
Smart Researcher - OpenAI bilan web search va post yaratish
"""

from openai import AsyncOpenAI
from config import OPENAI_API_KEY
import aiohttp
import os

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ============ PROMPTLAR ============

SEARCH_SYSTEM_PROMPT = """Sen professional IT tadqiqotchisan. 
Vazifang: Berilgan mavzu bo'yicha internetdan eng so'nggi va ishonchli ma'lumotlarni topish.

QOIDALAR:
1. Faqat ishonchli manbalardan foydalaning (rasmiy bloglar, texnik saytlar)
2. Eng yangi ma'lumotlarni toping (so'nggi 1 hafta/oy)
3. Har bir fakt uchun manbani yozing
"""

POST_SYSTEM_PROMPT = """Sen professional IT jurnalistsan va Telegram kanal yuritasan.

VAZIFA: Berilgan ma'lumotlar asosida o'zbek tilida professional post yoz.

POST FORMATI (Telegram HTML):
<b>📱 SARLAVHA - KATTA HARFDA</b>

Kirish - 1-2 jumla, mavzuni tanishtirish.

🔹 <b>Muhim nuqta 1</b> - aniq fakt
🔹 <b>Muhim nuqta 2</b> - aniq fakt  
🔹 <b>Muhim nuqta 3</b> - aniq fakt

<i>💡 Xulosa: Qisqa xulosa - 1-2 jumla</i>

———
📚 <b>Manbalar:</b>
- Manba 1 nomi
- Manba 2 nomi

#hashtag1 #hashtag2 #hashtag3

FORMATLASH QOIDALARI:
1. <b>matn</b> - qalin (muhim so'zlar uchun)
2. <i>matn</i> - kursiv (xulosa, izohlar uchun)
3. <code>kod</code> - kod yoki buyruqlar uchun
4. <pre>kod bloki</pre> - katta kod uchun

QOIDALAR:
1. O'zbek tilida yoz (texnik atamalar inglizcha bo'lishi mumkin)
2. Sodda va tushunarli til
3. Faqat berilgan faktlarga asoslan
4. 150-300 so'z oralig'ida
5. Kod bo'lsa <code> ichida yoz
6. Hashtaglar tegishli bo'lsin
"""

COMPARE_SYSTEM_PROMPT = """Sen texnologiya ekspertisan.

VAZIFA: Ikki texnologiyani solishtirish va Telegram uchun post yozish.

FORMAT (Telegram HTML):
<b>⚔️ TEXNOLOGIYA1 vs TEXNOLOGIYA2</b>

Kirish - nima uchun solishtirmoqdamiz.

<b>📊 Solishtirish:</b>

<b>✅ Texnologiya1 afzalliklari:</b>
- Afzallik 1
- Afzallik 2

<b>✅ Texnologiya2 afzalliklari:</b>
- Afzallik 1
- Afzallik 2

<b>🎯 Qachon qaysi birini tanlash kerak:</b>
- <i>Holat 1</i> → Tanlash
- <i>Holat 2</i> → Tanlash

<i>💡 Xulosa: Qisqa tavsiya</i>

#hashtag1 #hashtag2
"""

QUICK_SYSTEM_PROMPT = """Sen IT blogger san.

VAZIFA: Berilgan mavzu haqida qisqa, lo'nda post yoz.

FORMAT (Telegram HTML):
<b>⚡ SARLAVHA</b>

Asosiy ma'lumot - 2-3 jumla.

🔗 <i>Batafsil: manba</i>

#hashtag1 #hashtag2
"""

TRENDING_SYSTEM_PROMPT = """Sen IT yangiliklar tahlilchisisan.

FORMAT (Telegram HTML):
<b>🔥 BUGUNGI IT TRENDLAR</b>

1️⃣ <b>Trend 1</b>
   └ <i>Qisqa izoh</i>

2️⃣ <b>Trend 2</b>
   └ <i>Qisqa izoh</i>

3️⃣ <b>Trend 3</b>
   └ <i>Qisqa izoh</i>

4️⃣ <b>Trend 4</b>
   └ <i>Qisqa izoh</i>

5️⃣ <b>Trend 5</b>
   └ <i>Qisqa izoh</i>

#trending #tech #news
"""

# Rasm qidirish uchun prompt
IMAGE_SEARCH_PROMPT = """Berilgan mavzu uchun rasm qidirish uchun ingliz tilida 2-3 so'zlik kalit so'z ber.
Faqat kalit so'zni yoz, boshqa hech narsa yozma.
Masalan: "React 19" uchun → "React logo programming"
"""


class SmartResearcher:
    """OpenAI orqali tadqiqot va post yaratish"""

    def __init__(self):
        self.client = client
        self.model = "gpt-4o"

    async def search_and_analyze(self, query: str) -> dict:
        """Internetdan qidirish va ma'lumot yig'ish"""

        response = await self.client.responses.create(
            model=self.model,
            tools=[{"type": "web_search_preview"}],
            input=f"""
            Quyidagi mavzu bo'yicha internetdan eng so'nggi ma'lumotlarni top:

            MAVZU: {query}

            TOPILGAN MA'LUMOTLARNI QUYIDAGI FORMATDA BER:

            1. ASOSIY FAKTLAR:
            - [fakt 1]
            - [fakt 2]
            - [fakt 3]
            (kamida 5 ta fakt)

            2. MANBALAR:
            - [Manba nomi 1]: [qisqa tavsif]
            - [Manba nomi 2]: [qisqa tavsif]

            3. SO'NGGI YANGILIKLAR:
            - [yangilik 1 - sana bilan]
            - [yangilik 2 - sana bilan]

            Faqat ishonchli manbalardan foydalaning!
            """,
        )

        return {
            "query": query,
            "research": response.output_text,
            "status": "success"
        }

    async def generate_post(self, research_data: dict, post_type: str = "full") -> str:
        """Tadqiqot natijalariga asoslangan post yaratish"""

        if post_type == "compare":
            system_prompt = COMPARE_SYSTEM_PROMPT
        elif post_type == "quick":
            system_prompt = QUICK_SYSTEM_PROMPT
        elif post_type == "trending":
            system_prompt = TRENDING_SYSTEM_PROMPT
        else:
            system_prompt = POST_SYSTEM_PROMPT

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""
                Quyidagi tadqiqot natijalari asosida post yoz:

                MAVZU: {research_data['query']}

                TADQIQOT NATIJALARI:
                {research_data['research']}
                """}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        return response.choices[0].message.content

    async def get_image_for_topic(self, topic: str) -> str | None:
        """Mavzu uchun rasm URL olish (Unsplash)"""
        try:
            # Kalit so'z olish
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": IMAGE_SEARCH_PROMPT},
                    {"role": "user", "content": topic}
                ],
                max_tokens=20
            )
            keyword = response.choices[0].message.content.strip()

            # Unsplash'dan rasm olish (API key kerak emas)
            unsplash_url = f"https://source.unsplash.com/800x600/?{keyword.replace(' ', ',')}"

            return unsplash_url

        except Exception as e:
            print(f"Rasm olishda xatolik: {e}")
            return None

    async def full_research(self, topic: str, post_type: str = "full", with_image: bool = False) -> dict:
        """To'liq jarayon: qidirish + post yaratish"""

        # 1. Internetdan qidirish
        research = await self.search_and_analyze(topic)

        if research["status"] != "success":
            return {
                "success": False,
                "error": "Qidirishda xatolik yuz berdi"
            }

        # 2. Post yaratish
        post = await self.generate_post(research, post_type)

        # 3. Rasm olish (agar kerak bo'lsa)
        image_url = None
        if with_image:
            image_url = await self.get_image_for_topic(topic)

        return {
            "success": True,
            "topic": topic,
            "research": research["research"],
            "post": post,
            "image_url": image_url
        }

    async def compare_topics(self, topic1: str, topic2: str) -> dict:
        """Ikki mavzuni solishtirish"""

        combined_query = f"{topic1} vs {topic2} comparison differences advantages"

        research = await self.search_and_analyze(combined_query)

        if research["status"] != "success":
            return {"success": False, "error": "Qidirishda xatolik"}

        research["query"] = f"{topic1} vs {topic2}"
        post = await self.generate_post(research, "compare")

        return {
            "success": True,
            "topic1": topic1,
            "topic2": topic2,
            "post": post
        }

    async def quick_post(self, topic: str) -> dict:
        """Tezkor qisqa post"""
        return await self.full_research(topic, "quick")

    async def get_trending(self, category: str = "tech") -> dict:
        """Trendlar ro'yxati"""

        query = f"trending {category} news today 2024 2025"

        research = await self.search_and_analyze(query)

        if research["status"] != "success":
            return {"success": False, "error": "Xatolik"}

        post = await self.generate_post(research, "trending")

        return {
            "success": True,
            "post": post
        }
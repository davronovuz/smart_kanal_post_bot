"""
Smart Researcher - OpenAI bilan web search va post yaratish
"""

from openai import AsyncOpenAI
from config import OPENAI_API_KEY
import aiohttp
import random

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ============ PROMPTLAR ============

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

QOIDALAR:
1. O'zbek tilida yoz
2. Sodda va tushunarli til
3. Faqat berilgan faktlarga asoslan
4. 150-300 so'z oralig'ida
5. Kod bo'lsa <code>kod</code> ichida yoz
"""

COMPARE_SYSTEM_PROMPT = """Sen texnologiya ekspertisan.

FORMAT (Telegram HTML):
<b>⚔️ TEXNOLOGIYA1 vs TEXNOLOGIYA2</b>

Kirish - nima uchun solishtirmoqdamiz.

<b>✅ Texnologiya1 afzalliklari:</b>
- Afzallik 1
- Afzallik 2

<b>✅ Texnologiya2 afzalliklari:</b>
- Afzallik 1
- Afzallik 2

<b>🎯 Qachon qaysi birini tanlash:</b>
- <i>Holat 1</i> → Tanlash

<i>💡 Xulosa: Qisqa tavsiya</i>

#hashtag1 #hashtag2
"""

QUICK_SYSTEM_PROMPT = """Sen IT blogger san.

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


class SmartResearcher:
    """OpenAI orqali tadqiqot va post yaratish"""

    def __init__(self):
        self.client = client
        self.model = "gpt-4o"

    async def search_and_analyze(self, query: str) -> dict:
        """Internetdan qidirish"""
        try:
            response = await self.client.responses.create(
                model=self.model,
                tools=[{"type": "web_search_preview"}],
                input=f"""
                Quyidagi mavzu bo'yicha internetdan eng so'nggi ma'lumotlarni top:

                MAVZU: {query}

                FORMATDA BER:
                1. ASOSIY FAKTLAR (kamida 5 ta)
                2. MANBALAR
                3. SO'NGGI YANGILIKLAR (sana bilan)
                """,
            )

            return {
                "query": query,
                "research": response.output_text,
                "status": "success"
            }
        except Exception as e:
            return {
                "query": query,
                "research": "",
                "status": "error",
                "error": str(e)
            }

    async def generate_post(self, research_data: dict, post_type: str = "full") -> str:
        """Post yaratish"""

        prompts = {
            "compare": COMPARE_SYSTEM_PROMPT,
            "quick": QUICK_SYSTEM_PROMPT,
            "trending": TRENDING_SYSTEM_PROMPT,
            "full": POST_SYSTEM_PROMPT
        }

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompts.get(post_type, POST_SYSTEM_PROMPT)},
                {"role": "user",
                 "content": f"MAVZU: {research_data['query']}\n\nMA'LUMOTLAR:\n{research_data['research']}"}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        return response.choices[0].message.content

    async def get_image_for_topic(self, topic: str) -> str | None:
        """Mavzu uchun rasm URL olish"""
        try:
            # Kalit so'z olish
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system",
                     "content": "Rasm qidirish uchun 1-2 so'zlik inglizcha kalit so'z ber. Faqat so'zni yoz, boshqa hech narsa yozma."},
                    {"role": "user", "content": topic}
                ],
                max_tokens=10
            )
            keyword = response.choices[0].message.content.strip().replace(" ", "-")

            # Picsum - ishonchli bepul rasm
            random_id = random.randint(1, 1000)
            image_url = f"https://picsum.photos/seed/{keyword}{random_id}/800/600"

            # URL ishlashini tekshirish
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, allow_redirects=True) as resp:
                    if resp.status == 200:
                        return str(resp.url)

            return None

        except Exception as e:
            print(f"Rasm olishda xatolik: {e}")
            return None

    async def full_research(self, topic: str, post_type: str = "full", with_image: bool = False) -> dict:
        """To'liq jarayon: qidirish + post yaratish"""

        # 1. Internetdan qidirish
        research = await self.search_and_analyze(topic)

        if research["status"] != "success":
            return {"success": False, "error": research.get("error", "Qidirishda xatolik")}

        # 2. Post yaratish
        post = await self.generate_post(research, post_type)

        # 3. Rasm olish
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

        research = await self.search_and_analyze(f"{topic1} vs {topic2} comparison advantages disadvantages")

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
        return await self.full_research(topic, "quick", with_image=False)

    async def get_trending(self) -> dict:
        """Trendlar ro'yxati"""

        research = await self.search_and_analyze("trending tech AI programming news today 2024 2025")

        if research["status"] != "success":
            return {"success": False, "error": "Qidirishda xatolik"}

        post = await self.generate_post(research, "trending")

        return {
            "success": True,
            "post": post
        }
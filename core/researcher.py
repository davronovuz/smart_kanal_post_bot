"""
Smart Researcher - OpenAI bilan web search va post yaratish
Faqat bitta API - OpenAI!
"""

from openai import AsyncOpenAI
from config import OPENAI_API_KEY

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

POST FORMATI:
📱 [SARLAVHA - KATTA HARFDA, 5-8 so'z]

[Kirish - 1-2 jumla, mavzuni tanishtirish]

🔹 [Muhim nuqta 1 - aniq fakt]
🔹 [Muhim nuqta 2 - aniq fakt]  
🔹 [Muhim nuqta 3 - aniq fakt]
[Agar kerak bo'lsa, yana 1-2 nuqta]

💡 Xulosa: [Qisqa xulosa - 1-2 jumla]

———
📚 Manbalar:
• [Manba 1 nomi]
• [Manba 2 nomi]

#[teglar - 3-5 ta, vergulsiz]

QOIDALAR:
1. O'zbek tilida yoz (texnik atamalar inglizcha bo'lishi mumkin)
2. Sodda va tushunarli til
3. Faqat berilgan faktlarga asoslan, o'zing to'qima
4. 150-250 so'z oralig'ida
5. Emoji kam ishlat, ortiqcha emas
6. Hashtaglar tegishli bo'lsin (#python #react #ai kabi)
"""

COMPARE_SYSTEM_PROMPT = """Sen texnologiya ekspertisan.

VAZIFA: Ikki texnologiyani solishtirish va Telegram uchun post yozish.

FORMAT:
⚔️ [TEXNOLOGIYA1] vs [TEXNOLOGIYA2]

[Kirish - nima uchun solishtirmoqdamiz]

📊 Solishtirish:

✅ [Texnologiya1] afzalliklari:
• [Afzallik 1]
• [Afzallik 2]

✅ [Texnologiya2] afzalliklari:
• [Afzallik 1]
• [Afzallik 2]

🎯 Qachon qaysi birini tanlash kerak:
• [Holat 1] → [Tanlash]
• [Holat 2] → [Tanlash]

💡 Xulosa: [Qisqa tavsiya]

#[teglar]
"""

QUICK_SYSTEM_PROMPT = """Sen IT blogger san.

VAZIFA: Berilgan mavzu haqida qisqa, lo'nda post yoz.

FORMAT:
⚡ [SARLAVHA]

[Asosiy ma'lumot - 2-3 jumla]

🔗 Batafsil: [manba]

#[2-3 hashtag]

QOIDALAR:
- Maksimum 100 so'z
- Faqat eng muhim fakt
- Tez o'qilsin
"""


class SmartResearcher:
    """OpenAI orqali tadqiqot va post yaratish"""

    def __init__(self):
        self.client = client
        self.model = "gpt-4o"  # Eng yaxshi model

    async def search_and_analyze(self, query: str) -> dict:
        """
        Internetdan qidirish va ma'lumot yig'ish
        OpenAI web_search toolidan foydalanadi
        """

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
        """
        Tadqiqot natijalariga asoslangan post yaratish
        """

        # Post turiga qarab prompt tanlash
        if post_type == "compare":
            system_prompt = COMPARE_SYSTEM_PROMPT
        elif post_type == "quick":
            system_prompt = QUICK_SYSTEM_PROMPT
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

    async def full_research(self, topic: str, post_type: str = "full") -> dict:
        """
        To'liq jarayon: qidirish + post yaratish
        """

        # 1. Internetdan qidirish
        research = await self.search_and_analyze(topic)

        if research["status"] != "success":
            return {
                "success": False,
                "error": "Qidirishda xatolik yuz berdi"
            }

        # 2. Post yaratish
        post = await self.generate_post(research, post_type)

        return {
            "success": True,
            "topic": topic,
            "research": research["research"],
            "post": post
        }

    async def compare_topics(self, topic1: str, topic2: str) -> dict:
        """
        Ikki mavzuni solishtirish
        """

        combined_query = f"{topic1} vs {topic2} comparison differences advantages"

        research = await self.search_and_analyze(combined_query)

        if research["status"] != "success":
            return {
                "success": False,
                "error": "Qidirishda xatolik"
            }

        research["query"] = f"{topic1} vs {topic2}"
        post = await self.generate_post(research, "compare")

        return {
            "success": True,
            "topic1": topic1,
            "topic2": topic2,
            "post": post
        }

    async def quick_post(self, topic: str) -> dict:
        """
        Tezkor qisqa post
        """
        return await self.full_research(topic, "quick")

    async def get_trending(self, category: str = "tech") -> dict:
        """
        Trendlar ro'yxati
        """

        query = f"trending {category} news today 2024"

        research = await self.search_and_analyze(query)

        if research["status"] != "success":
            return {"success": False, "error": "Xatolik"}

        # Maxsus trending prompt
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": """Sen IT yangiliklar tahlilchisisan.

FORMAT:
🔥 BUGUNGI TRENDLAR

1️⃣ [Trend 1]
   └ [Qisqa izoh]

2️⃣ [Trend 2]
   └ [Qisqa izoh]

3️⃣ [Trend 3]
   └ [Qisqa izoh]

4️⃣ [Trend 4]
   └ [Qisqa izoh]

5️⃣ [Trend 5]
   └ [Qisqa izoh]

#trending #tech #news
"""},
                {"role": "user", "content": research["research"]}
            ],
            temperature=0.7
        )

        return {
            "success": True,
            "post": response.choices[0].message.content
        }
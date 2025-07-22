# ============================
# Imports & Setup
# ============================
import asyncio
import logging
import os
import random
import re
from collections import defaultdict
from datetime import timedelta, datetime, timezone
from typing import Optional, Dict, List, Set, Union

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import wikipedia
from duckduckgo_search import DDGS

try:
    import webserver  # type: ignore
except ImportError:
    webserver = None

# ============================
# Environment & Logging
# ============================
load_dotenv()
DISCORD_TOKEN = os.getenv("discordkey")
ALLOWED_GUILD_ID = 752891683888431124

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s › %(message)s",
    handlers=[
        logging.FileHandler("discord.log", encoding="utf-8", mode="w"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("bot")

# ============================
# Bot Setup
# ============================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ============================
# Banned Words System
# ============================
class BannedWords:
    def __init__(self):
        self.word_lists: Dict[str, Set[str]] = defaultdict(set)
        self.all_words: Set[str] = set()
        self.pattern: Optional[re.Pattern] = None
        self._load_words()
        
    def _load_words(self):
        """Load all abusive words from all languages"""
        # English
        self.word_lists['english'].update([
            "fuck", "bitch", "bastard", "asshole", "cunt", "slut", "dick", "cock", "prick",
            "motherfucker", "pussy", "jerk", "shit", "moron", "crap", "damn", "retard",
            "whore", "fag", "faggot", "douchebag", "twat", "wanker", "nigga", "nigger",
            "son of a bitch", "kys", "kill yourself", "uninstall", "trash", "scrub",
            "dogwater", "suck", "ez", "loser", "fatherless", "adopted", "touch grass"
        ])
        
        # Hindi
        self.word_lists['hindi'].update([
            "chutiya", "madarchod", "bhosdiwala", "gaand", "loda", "behenchod", "randi",
            "kutta", "chut", "launda", "maa ki chut", "teri maa", "mc", "bc", "kutte", "randwa",
            "lund", "choot", "bhen ke laude", "teri maa ka bhosda", "gaandu", "chutiyapa",
            "bhosad", "bhosadi", "chutmarike", "gandmara", "lavde", "maa ka bhosda",
            "randi ka bacha", "teri maa randi", "teri behen randi", "chootiya", "jhaat", "jhaant",
            "bhonsdiwale", "maa chuda", "behen ke laude", "lund choos", "gaand mara", "choot chatora",
            "gel chodi gand andhi rand", "tere baap ki chut", "maa ke laude", "behen ke lund",
            "teri maa ki chut", "teri behen ki chut", "maa ka lund", "behen ka lund"
        ])
        
        # Marathi
        self.word_lists['marathi'].update([
            "gand", "chod", "zhaavla", "lavda", "bhosdi", "randi", "bhadwa", "kutta",
            "baapacha", "aichya gavat", "bawlat", "phodri", "gadhav", "akramhshi", "andya",
            "aighala", "zhatu", "zhavat", "bhund", "bocha", "bulli", "chut", "gandu",
            "haramkhor", "jhant", "kutra", "lavdya", "maaicha", "madarchod", "rand",
            "saala", "tharki", "bhosda", "chinar", "chutad", "fokatya", "ghandu", "zhavat",
            "aai zav", "aai zavli", "aai zavlya", "aai zavla", "aai zavlya cha", "aai zavlya chi",
            "aai zavlya che", "aai zavlya la", "aai zavlya ne", "aai zavlya ni", "aai zavlya cha"
        ])
        
        # Bengali
        self.word_lists['bengali'].update([
            "chod", "choda", "chudir baccha", "chudbo", "chudi", "loda", "lode", "lodachoda",
            "maa ke chudi", "bon chuda", "bokachoda", "shuar", "kukur", "chot", "chotmarani",
            "chudbaaz", "maachuda", "bonchuda", "tor maa ke chudi", "tor bon ke chudi", "lund",
            "gaandu", "randi", "haraami", "chinal", "boka", "pagol", "fatu", "dhorbo",
            "tor maa r choda", "tor bou r choda", "tor bon r choda", "tor maa r chod",
            "tor bou r chod", "tor bon r chod", "tor maa r chudi", "tor bou r chudi",
            "tor bon r chudi", "tor maa r chud", "tor bou r chud", "tor bon r chud"
        ])
        
        # Punjabi
        self.word_lists['punjabi'].update([
            "chutiya", "madarchod", "behenchod", "randi", "tera baap", "maa da bhosda",
            "chod", "lund", "ghandu", "kutta", "suar da puttar", "behn di", "sala",
            "teri maa di", "teri behen di", "teri maa da", "teri behen da", "teri maa di chut",
            "teri behen di chut", "teri maa da lund", "teri behen da lund", "teri maa da bhosda",
            "teri behen da bhosda", "teri maa di gand", "teri behen di gand"
        ])
        
        # South Indian Languages (Tamil/Telugu/Kannada/Malayalam)
        self.word_lists['south_indian'].update([
            "thevudiya", "pochi", "punda", "naaye", "kundi", "dengudu", "lavda", "kodaka",
            "sule", "soole", "bosi", "pund", "thendi", "thalla", "kazhutha", "nayinte",
            "dongamunda", "thikka", "sani", "kirik", "holeya", "gandu", "chamkili", "kuthra",
            "pakal", "kothi", "pucchi", "gotya", "chhinaal", "zhavli", "madarchod",
            "ninna amma", "ninna thayi", "ninna maga", "ninna thangi", "ninna appa",
            "amma na", "bejaar", "chut naku", "lund tinod", "sulu chuchu", "gand mara"
        ])
        
        # Gaming Slang
        self.word_lists['gaming'].update([
             "kill yourself","end yourself","fuck", "bitch", "asshole", "dick", "slut", "nigga",
             "madarchod", "bhosdike", "chutiya", "lund", "beti chod", "gaand", "randi",
             "bhenchod", "bhench*d", "mc", "bc", "chootiya", "kutte", "gandu",
             "lode", "lauda", "maa ka bhosda", "teri maa", "teri behen", "chodu", "randwa",
             "bol teri gand kaise maru", "gandmara", "chdmarike", "choot chatora",
             "gel chodi gand andhi rand", "lavde", "madar chod", "gand maar lunga",
             "tere baap ki chut hai", "tere maa market me nanga nach kr rahi hai",
             "kutta kamine bsdk chutiya", "teri maa randwi hai", "lund ke tope",
             "chut ke kitde", "chinal ki aulad", "chutmari ka choda", "teri chut", "bhg bsdk",
             "bhen ka lavda", "chut chatora", "jhaat bara bar", "me toh chut ka shikari hu", "bhosda", "chutad","jhat","अकराम्हशी","अकराम्हशीचा","अकराम्हशीच्या","आंद्या","आंद्याचा","आंद्याच्या","आंद्यात","आईघाला","आईघाल्","आईघाल्या","आईघाल्याचा","आईजवाडा","आईजवाडाचा","आईझव","आईझवली","आईझवलीचा","आईझवाडा","आईझवाडाचा","कँडल","कँडलचा","कँडलच्या","कृतघ्न","गांड","गांडचा","गांडच्या","गांडीचा","गांडीत","गांडू","गांडूचा","गांडूच्या","गांडूत","गाढव","गाढवागांडुळ","गोट्या","गोट्याचा","गोट्याच्या","गोट्यात","चावट","चीनाल","चीनालचा","चीनालच्या","चुत","चुतचा","चुतच्या","चुतत","चुतमारीचा","चुतमारीच्या","चुतमारीच्यात","छिनाल","छिनालचा","छिनालच्या","झवली","झवलीचा","झवलीत","झवाड्या","झवाड्याचा","झवाड्याच्या","झाटू","झाटूचा","झाटूच्या","झाटूत","नालायकच्यायला","पागलगुदा","पुच्ची","पुच्चीचा","पुच्चीच्या","पुच्चीत","फोकणीच्या","फोकणीच्याचा","फोकणीच्यात","फोद्री","फोद्रीचा","फोद्रीच्या","फोद्रीच्यात","फोद्रीत","बावळट","बावळटच्या","बावळटत","बुडाला","बुल्ली","बुल्लीचा","बुल्लीत","बेअक्कल","बेशरम","बोचा","बोचाच्या","बोचात","बोच्याबुल्लीच्या","भडवा","भडविच्याभिकारचोट","भडव्या","भडव्यात","भुंड्","भुंड्त","भुंड्यात","भुंड्यातत","भोक","भोकचा","भोकत","भोकाच्या","भोसडा","भोसडाचा","भोसडात","भोसडीच्या","भोसडीच्यात","मंद","माईचा","माईचात","माईच्या","मादरचोद","मारीच्या","मारीच्यात","मुठ्ठया","मुठ्ठयाचा","मुठ्ठयात","मूर्ख","रंडी","रंडीचा","रंडीच्या","रंडीच्यात","रंडीत","रांड",
"रांडचा","रांडच्या","रांडीच्या","रांडीच्यात","लवड्या","लवड्याचा","लवड्याच्या","लवड्यात"
"साला","हरामखोर","हलकट" "हरामखोरचा","हरामखोरच्या","हरामखोरात","akramhshi", "akramhshicha", "akramhshichya","andya", "andyacha", "andyachya", "andyat",
"aighala", "aighalya", "aighalyacha",
"aijawada", "aijawadacha",
"aizhav", "aizhavli", "aizhavlicha", "aizhawada", "aizhawadacha",
"candle", "candlecha", "candlechya",
"krutaghn",
"gand", "gandcha", "gandchya", "gandicha", "gandit",
"gandu", "ganducha", "ganduchya", "gandut",
"gadhav", "gadhavagandul",
"gotya", "gotyacha", "gotyachya", "gotyat",
"chawat", "chinal", "chinalcha", "chinalchya",
"chut", "chutcha", "chutchya", "chuttat",
"chutmari", "chutmarcha", "chutmarchyat",
"chhinaal", "chhinaalcha", "chhinaalchya","zhavli", "zhavlicha", "zhavlit",
"zhawadya", "zhawadyacha", "zhawadyachya",
"zhatu", "zhatucha", "zhatuchya", "zhatut",
"nalayakchyayla","pagalguda",
    # Family-Based
    "ninna amma chudrappa", "ninna thayi bosi", "ninna thayi chuchu", "ninna amma maga", "ninna thangi naakthini",
    "ninna magalu daari dalli", "thayi chut tinod maga", "ninna appa chut kaayi", "amma na naakthini", "bejaar thayi chut",

    # Mental/Character/Caste
    "gandu", "lusu", "loose huduga", "mental case", "buddhi illa", "tharle", "kirik", "mentalt",
    "chamkili", "chamaar maga", "holeya", "holeyaru", "basse kasta",

    # Animal
    "nayi", "handi", "saalige", "hasu", "kudure", "koli maga", "mooru nayi", "hakki maga", "hejjegalu", "enu gothilla nayi",

    # Gaming Slang
    "noob nayi", "camper sulen", "scope nodoke baralla", "ninna team full gandu", "clutch beda maga",
    "teri lobby gayi tel lagaake", "mic haaki mare", "stream sniping soole", "hacker nayi", "peek madoke baralla",
    "sulen jasti swalpa skill ko",

    # Combo Insults
    "ninna amma chut alli chalu aagidale", "chut thora maga", "lund ella alli ide",
    "ninna thayi soole dalli kelsa madtha idale", "pundeya gandu", "chut borege saku", "sulekke nayi kooda baralla",# Genital/Sexual
    "bhalu", "mukhrot dhula", "patar", "chutmarani", "chutkhaowa", "lund kha", "gaand phati gol",
    "chut dhula", "suri kha", "chut diya", "chut khai ase",

    # Family-Based
    "tor maari", "tor bou", "tor ma randi", "tor bhonti randi", "tor ma chut", "tor bou lund",
    "tor bhonti chut", "tor ma lund", "tor maa gaand diya", "tor bou randi", "tor maa chut khai ase",

    # Mental/Character
    "bokachoda", "bura bokachoda", "pagol", "uthoni", "bekar", "bhagwan r nai", "dhemeli",
    "ulta jukti diya", "bokami kori thaka", "matha dhula", "akkal nai", "moron",

    # Animal
    "suwor", "suworer baccha", "xial", "kutta", "kukura", "goru", "gadha", "bandor",
    "dhuli", "dhol", "kukurni", "suali kutta",

    # Gaming/Online
    "noob", "hack use kori khel", "lundor aim", "camper kutta", "tor aim chutot", "tor gaand te crosshair",
    "tor mouse gaandot", "tor ping chut", "camper randi", "aim assist randi",

    # Hybrid/Roasting
    "tor maari chut", "tor bou chut khai ase", "lund diya randi", "chut dhula bhonti",
    "tor aim maa te", "gaand khuli gol", "mobile te maa chut dise", "stream snipe kori chut kha",# Genital
    "chod", "choda", "chudir baccha", "chudbo", "chudi", "chudchhi", "chudachhi",
    "choda dibi", "chudi dibi", "chudiye debo", "chot", "chotmarani", "chotkhani",
    "chot khaowa", "chot chush", "loda", "lode", "lodachoda", "loda chusbi", "loda dhukabo",
    "biran", "biraler chot", "chudbaaz", "chuda player",

    # Family/Parental
    "tor maa ke chudi", "tor bon ke chudi", "maa chuda", "bon chuda", "maa ke loda",
    "maa r chot", "maa ke chodchi", "maa choder player", "tor bon choda",
    "maa ke chudbo", "maa ke chudiye debo", "maa r loda chushe felbi",
    "tor bou r chot", "bou ke chudchi", "bou ke lodai", "tor bou chudi",

    # Mental
    "bokachoda", "boka", "pagol", "pagla", "fatu", "boka choda", "byatha",
    "bhootni", "dhorbo", "brain nai", "buddhiheen",

    # Animal
    "shuar", "shuarer baccha", "kukur", "kukur choda", "bandor", "beral",
    "goru", "gadha", "ghoda", "suorer chhana", "bandorer chot",

    # Online Gaming
    "noob choda", "stream sniping randir baccha", "aim nai loder moto",
    "camperer maa choda", "gaand mara player", "neter chot", "crosshair maa r chot",
    "spray maa te", "hackerer chot", "loda aim assist", "jhari galo lobby",

    # Hybrid / Dank Combos
    "tor maa ke loda dhukiye debo", "tor bon er chot bhenge debo", "loda dhuke chudbo",
    "bou ke maa banabo", "stream kore maa chod", "chot e loda", "tor family ek shathe chudbo",
    "tor chot porjonto toxic", "loder moto speech", "maa bon ekta pod er upor"

        ])
        
        # Add all words to master list
        for words in self.word_lists.values():
            self.all_words.update(words)
            
        self._compile_pattern()
    
    def _compile_pattern(self):
        """Create optimized regex pattern"""
        # Match whole words only, with common variations
        self.pattern = re.compile(
            r'(?<!\w)(' + '|'.join(
                re.escape(word) + r'(s|ing|ed|er)?'  # Handle plurals/verbs
                for word in self.all_words
            ) + r')(?!\w)',
            re.IGNORECASE
        )
    
    def contains_banned_word(self, text: str) -> bool:
        """Check if text contains any banned words"""
        return bool(self.pattern.search(text.lower()))
    
    def get_banned_words(self, text: str) -> List[str]:
        """Get all banned words found in text"""
        return self.pattern.findall(text.lower())
    
    def add_custom_words(self, words: Union[List[str], Set[str]], language: str = 'english'):
        """Add custom banned words"""
        if isinstance(words, list):
            words = set(words)
        self.word_lists[language].update(words)
        self.all_words.update(words)
        self._compile_pattern()

# Initialize banned words detector
banned_words = BannedWords()

# ============================
# Data & Constants
# ============================
SPAM_TIME_FRAME = 5  # seconds
SPAM_MESSAGE_LIMIT = 5
TIMEOUT_DURATION = 60  # seconds

user_message_times = defaultdict(list)
user_recent_messages = defaultdict(list)
modmail_map: Dict[int, int] = {}

general_knowledge_qa = {
    "what is the capital of france": "Paris 🇫🇷",
    "who wrote harry potter": "J.K. Rowling ✍️",
    "what is the largest planet": "Jupiter is the largest planet in our solar system! 🪐",
    "who is the president of usa": "As of now, it's Joe Biden.",
    "what is pi": "Pi (π) is approximately 3.14159.",
    "what is the speed of light": "The speed of light is about 299,792 kilometers per second.",
    "who invented the telephone": "Alexander Graham Bell invented the telephone.",
    "how many continents are there": "There are 7 continents on Earth.",
    "what's the tallest mountain": "Mount Everest is the tallest mountain above sea level.",
    "when is independence day (india)": "India celebrates Independence Day on 15th August."
}

# Friendly Triggers (add more everyday chat)
friendly_triggers = {
    ("hello", "hi", "hey", "yo", "oye", "sup", "wassup", "namaste", "salaam", "good morning", "good afternoon", "good evening"): [
        "Hey {mention}, kaise ho? 😊", "Namaste {mention}!", "Hello hello {mention}!", "Oye, kya haal hai {mention}? 👋", "Yo {mention}, what's up?"
    ],
    ("or", "or kya", "or batao", "or bhai", "aur bata", "aur kya", "kya scene hai"): [
        "Sab badiya {mention}, tum batao!", "Aur kya ho raha hai {mention}?", "Bhai, life set hai. Tumhara kya haal hai?", "Chalo, batao koi nayi baat {mention}."
    ],
    ("how are you", "kaisa hai", "kya haal hai", "kaisi ho", "how's it going", "kaisi chal rahi hai life"): [
        "Mast hoon! Tum sunao {mention}?", "Main theek hoon, tum kaise ho {mention}?", "Bas, zinda hoon! 😎"
    ],
    ("what's up", "whats up", "kya chal raha hai", "kya ho raha hai"): [
        "Sab theek! Tumhara kya scene hai {mention}?", "Aaj kuch naya nahi {mention}, tum batao!", "Life ekdum chill hai!"
    ],
    ("tell me a joke", "joke", "koi joke sunao", "make me laugh"): [
        "Why don't scientists trust atoms? Because they make up everything! 😂",
        "Teacher: Why are you late? Student: Because of the sign. Teacher: What sign? Student: School Ahead, Go Slow! 🤣",
        "What do you call fake spaghetti? An impasta! 🍝"
    ],
    ("who made you", "creator", "banaya kisne", "who is your developer"): [
        "Mujhe banaya Neon ne! 😎", "Neon is my boss! 💻", "I'm powered by Neon! 🔥"
    ],
    ("bye", "good night", "gn", "see you", "goodbye", "tc", "take care"): [
        "Bye {mention}, milte hain phir! 👋", "Good night {mention}, sweet dreams! 🌙", "Take care {mention}!"
    ],
    ("thanks", "thank you", "ty", "shukriya", "dhanyawad"): [
        "Koi baat nahi {mention}, anytime! 🙏", "Yahi to kaam hai mera 😄", "You're welcome {mention}!"
    ],
    ("love you", "i love you bot", "ily bot", "luv u bot"): [
        "Love you too {mention} ❤️", "Aww 🥺, tum bhi best ho {mention}!", "Dil jeet liya tumne {mention} 😍"
    ]
}

# Add more relatable fallback replies
fallback_replies = [
    "Hmmm... interesting! Tumhe pata hai, honey never spoils. 😲",
    "Accha yeh batao, tum sabse zyada kis cheez mein expert ho?",
    "Waise, tumhe memes pasand hai? Main bhi meme lover hoon!",
    "Pata hai, octopus ke teen dil hote hain! 🐙",
    "Main samajh nahi paaya, but tumhare saath baat kar ke maza aata hai!",
    "Yeh question tough tha! Tum batao, kuch aur poochna hai?"
]
# ============================
# Utility Functions
# ============================
def get_general_knowledge(content: str) -> Optional[str]:
    return GENERAL_KNOWLEDGE.get(content.lower().strip().rstrip("?"))

def pick_friendly_reply(content: str, author_mention: str) -> Optional[str]:
    lowered = content.lower()
    for triggers, responses in FRIENDLY_TRIGGERS.items():
        if any(t in lowered for t in triggers):
            return random.choice(responses).format(mention=author_mention)
    return None

async def duckduckgo_search(query: str) -> str:
    """Perform DuckDuckGo search and return formatted results"""
    try:
        loop = asyncio.get_running_loop()
        def _sync_search():
            with DDGS() as ddgs:
                results = []
                for r in ddgs.text(query, max_results=3):
                    results.append(f"• [{r['title']}]({r['href']})\n{r['body']}")
                return "\n\n".join(results) if results else "No results found."
        return await loop.run_in_executor(None, _sync_search)
    except Exception as e:
        log.error(f"DuckDuckGo search error: {e}")
        return "Search failed. Please try again later."

# ============================
# Search Handlers
# ============================
async def handle_wiki_search(message: discord.Message, query: str):
    """Handle Wikipedia search requests"""
    try:
        async with message.channel.typing():
            clean_query = query.strip()
            if not clean_query:
                await message.reply("Please specify a search term after 'wiki'")
                return
                
            try:
                summary = wikipedia.summary(clean_query, sentences=3, auto_suggest=True)
                embed = discord.Embed(
                    title=f"Wikipedia: {clean_query}",
                    description=summary,
                    color=discord.Color.blue(),
                    url=f"https://en.wikipedia.org/wiki/{clean_query.replace(' ', '_')}"
                )
                await message.reply(embed=embed)
            except wikipedia.DisambiguationError as e:
                options = "\n".join(f"• {opt}" for opt in e.options[:5])
                await message.reply(f"Multiple matches found:\n{options}\n\nPlease be more specific!")
            except wikipedia.PageError:
                await message.reply(f"No Wikipedia page found for '{clean_query}'. Try different keywords?")
                
    except Exception as e:
        log.error(f"Wikipedia error: {e}")
        await message.reply("Wikipedia search failed. Try again later.")

async def handle_web_search(message: discord.Message, query: str):
    """Handle DuckDuckGo web searches"""
    try:
        async with message.channel.typing():
            clean_query = query.strip()
            if not clean_query:
                await message.reply("Please specify a search term after 'search'")
                return
                
            results = await duckduckgo_search(clean_query)
            embed = discord.Embed(
                title=f"Search Results: {clean_query}",
                description=results,
                color=discord.Color.green()
            )
            await message.reply(embed=embed)
    except Exception as e:
        log.error(f"Web search error: {e}")
        await message.reply("Web search failed. Please try again later.")

# ============================
# Events
# ============================
@bot.event
async def on_ready():
    log.info("Logged in as %s (%s)", bot.user, bot.user.id)
    if webserver:
        webserver.keep_alive()
    clear_histories.start()

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or (message.guild and message.guild.id != ALLOWED_GUILD_ID):
        return

    now = datetime.now(timezone.utc)
    uid = message.author.id

    # Anti-spam handling
    user_message_times[uid].append(now)
    user_message_times[uid] = [t for t in user_message_times[uid] if (now - t).total_seconds() <= SPAM_TIME_FRAME]

    user_recent_messages[uid].append(message)
    user_recent_messages[uid] = [m for m in user_recent_messages[uid] if (now - m.created_at).total_seconds() <= SPAM_TIME_FRAME]

    if len(user_message_times[uid]) >= SPAM_MESSAGE_LIMIT and not message.author.guild_permissions.administrator:
        try:
            for m in user_recent_messages[uid]:
                await m.delete()
            await message.channel.send(f"{message.author.mention} stop spamming! Timed-out for {TIMEOUT_DURATION}s.")
            until = discord.utils.utcnow() + timedelta(seconds=TIMEOUT_DURATION)
            await message.author.timeout(until, reason="Spam")
        except discord.Forbidden:
            await message.channel.send("⚠️ I lack permission to timeout users.")
        finally:
            user_message_times[uid].clear()
            user_recent_messages[uid].clear()
        return

    # Banned words filter
    if banned_words.contains_banned_word(message.content):
        bad_words = banned_words.get_banned_words(message.content)
        try:
            await message.delete()
            warning = (
                f"⚠️ {message.author.mention}, your message contained banned words: "
                f"||{', '.join(set(bad_words))}||\n"
                "**This violates our community guidelines.**"
            )
            await message.channel.send(warning, delete_after=10)
            log.warning(f"Banned words detected from {message.author}: {bad_words}")
        except discord.Forbidden:
            await message.channel.send("⚠️ I lack permissions to delete messages.")
        return

    # Mod-mail handling
    if isinstance(message.channel, discord.DMChannel):
        guild = bot.get_guild(ALLOWED_GUILD_ID)
        mod_channel = discord.utils.get(guild.text_channels, name="mod-mail") if guild else None
        if not mod_channel:
            await message.channel.send("❌ Mod-mail channel not found.")
            return

        embed = discord.Embed(title="📬 New Mod-mail", description=message.content, color=discord.Color.blue())
        embed.set_author(name=f"{message.author} ({message.author.id})", icon_url=message.author.display_avatar.url)
        sent = await mod_channel.send(embed=embed)
        modmail_map[sent.id] = message.author.id
        await message.channel.send("✅ Your message has been sent to the moderators!")
        return

    # Handle wiki commands (prefix: wiki)
    if message.content.lower().startswith("wiki "):
        query = message.content[5:].strip()
        await handle_wiki_search(message, query)
        return

    # Handle web search commands (prefix: search or !search)
    if message.content.lower().startswith(("search ", "!search ")):
        prefix = "search " if message.content.lower().startswith("search ") else "!search "
        query = message.content[len(prefix):].strip()
        await handle_web_search(message, query)
        return

    # Process other commands
    await bot.process_commands(message)

    # Only respond to mentions/DMs for other responses
    if not (bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel)):
        return

    lowered = message.content.lower()

    # General knowledge
    if (answer := get_general_knowledge(lowered)):
        await message.channel.send(answer)
        return

    # Friendly replies
    if (reply := pick_friendly_reply(lowered, message.author.mention)):
        await message.channel.send(reply)
        return

    # Fallback
    await message.channel.send(random.choice(FALLBACK_REPLIES))

# ============================
# Commands
# ============================
@bot.command(name="reply")
@commands.has_permissions(manage_messages=True)
async def reply_to_modmail(ctx: commands.Context, message_id: int, *, response: str):
    user_id = modmail_map.get(message_id)
    if not user_id:
        await ctx.send("❌ Message ID not found in active mod-mail.")
        return
    try:
        user = await bot.fetch_user(user_id)
        await user.send(f"📩 **Moderator reply:**\n{response}")
        await ctx.send(f"✅ Replied to {user.display_name}")
    except discord.Forbidden:
        await ctx.send("❌ Cannot DM this user.")

@bot.command(name="triggers")
async def list_triggers(ctx: commands.Context):
    lines = ["**I respond to these phrases (when tagged or DMed):**"]
    for group in FRIENDLY_TRIGGERS:
        lines.append(" • " + ", ".join(f"`{t}`" for t in group))
    await ctx.send("\n".join(lines))

@bot.command(name="addbanned")
@commands.has_permissions(manage_messages=True)
async def add_banned_word(ctx: commands.Context, language: str, *, words: str):
    """Add custom banned words"""
    word_list = [w.strip() for w in words.split(",")]
    banned_words.add_custom_words(word_list, language.lower())
    await ctx.send(f"✅ Added {len(word_list)} words to {language} banned list")

# ============================
# Tasks
# ============================
@tasks.loop(minutes=5)
async def clear_histories():
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=SPAM_TIME_FRAME)
    for uid in list(user_message_times):
        user_message_times[uid] = [t for t in user_message_times[uid] if t > cutoff]
        user_recent_messages[uid] = [m for m in user_recent_messages[uid] if m.created_at > cutoff]
        if not user_message_times[uid]:
            user_message_times.pop(uid, None)
            user_recent_messages.pop(uid, None)


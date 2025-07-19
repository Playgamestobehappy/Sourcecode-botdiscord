import discord
from discord.ext import commands
from discord import app_commands
from keepAlive import keep_alive
import os
import yt_dlp
import asyncio
import datetime
import pytz
import random
import time

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

start_time = time.time()

user_data = {}

def get_thai_time():
    tz = pytz.timezone("Asia/Bangkok")
    now = datetime.datetime.now(tz)
    return now.strftime("%H:%M:%S | %d-%m-%Y")

def get_uptime():
    seconds = int(time.time() - start_time)
    return str(datetime.timedelta(seconds=seconds))

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot พร้อมใช้งาน: {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="ใช้ /play หรือ /fish เล่นเกม"))

# ----------- Voice & Music Commands -----------

@tree.command(name="join", description="เชื่อมต่อบอทเข้าห้องเสียงของคุณ")
async def join_cmd(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.response.send_message("กรุณาเข้าห้องเสียงก่อนสั่งบอท", ephemeral=True)
        return
    vc = interaction.guild.voice_client
    if vc and vc.is_connected():
        await interaction.response.send_message("บอทอยู่ในห้องเสียงแล้ว", ephemeral=True)
        return
    channel = interaction.user.voice.channel
    await channel.connect()
    await interaction.response.send_message(f"เชื่อมต่อห้องเสียง: {channel.name}")

@tree.command(name="leave", description="บอทออกจากห้องเสียง")
async def leave_cmd(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        await vc.disconnect()
        await interaction.response.send_message("บอทออกจากห้องเสียงเรียบร้อยแล้ว")
    else:
        await interaction.response.send_message("บอทไม่ได้อยู่ในห้องเสียง")

@tree.command(name="play", description="เล่นเพลงจาก YouTube")
@app_commands.describe(query="ลิงก์หรือชื่อเพลงที่ต้องการเล่น")
async def play_cmd(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    vc = interaction.guild.voice_client
    if not vc:
        if interaction.user.voice:
            vc = await interaction.user.voice.channel.connect()
        else:
            await interaction.followup.send("กรุณาเข้าห้องเสียงก่อนสั่งเพลง")
            return
    ytdl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "default_search": "ytsearch"
    }
    try:
        with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if "entries" in info:
                info = info["entries"][0]
            url = info["url"]
            title = info.get("title", "เพลงไม่มีชื่อ")
    except Exception as e:
        await interaction.followup.send(f"ไม่พบเพลงที่ต้องการ: {e}")
        return

    def after_play(error):
        if error:
            print(f"เกิดข้อผิดพลาดขณะเล่นเพลง: {error}")

    if vc.is_playing():
        vc.stop()

    vc.play(discord.FFmpegPCMAudio(url), after=after_play)
    await interaction.followup.send(f"กำลังเล่นเพลง: **{title}**")

@tree.command(name="pause", description="หยุดเพลงชั่วคราว")
async def pause_cmd(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await interaction.response.send_message("หยุดเพลงชั่วคราวแล้ว")
    else:
        await interaction.response.send_message("ไม่มีเพลงเล่นอยู่ในขณะนี้")

@tree.command(name="resume", description="เล่นเพลงต่อ")
async def resume_cmd(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_paused():
        vc.resume()
        await interaction.response.send_message("เล่นเพลงต่อแล้ว")
    else:
        await interaction.response.send_message("ไม่มีเพลงหยุดไว้")

@tree.command(name="skip", description="ข้ามเพลง")
async def skip_cmd(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message("ข้ามเพลงเรียบร้อยแล้ว")
    else:
        await interaction.response.send_message("ไม่มีเพลงเล่นอยู่ในขณะนี้")

@tree.command(name="stop", description="หยุดเพลงและออกจากห้องเสียง")
async def stop_cmd(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        await vc.disconnect()
        await interaction.response.send_message("หยุดเพลงและออกจากห้องเสียงแล้ว")
    else:
        await interaction.response.send_message("บอทไม่ได้เชื่อมต่อกับห้องเสียง")

# ----------- Mini Games -----------

@tree.command(name="fish", description="ตกปลาเพื่อสุ่มไอเท็มและได้เงิน")
async def fish_cmd(interaction: discord.Interaction):
    user = str(interaction.user.id)
    fishes = ["ปลาทอง", "ปลาหมอ", "ปลากัด", "ปลาบู่", "ปลาช่อน", "ปลาสวาย", "ปลานิล"]
    fish = random.choice(fishes)
    money_earned = random.randint(10, 100)

    if user not in user_data:
        user_data[user] = {"fish_caught": [], "money": 0}
    user_data[user]["fish_caught"].append(fish)
    user_data[user]["money"] += money_earned

    await interaction.response.send_message(f"🎣 คุณตกได้ **{fish}** และได้รับเงิน `{money_earned}` บาท!")

@tree.command(name="myfish", description="ดูปลาที่คุณตกได้")
async def myfish_cmd(interaction: discord.Interaction):
    user = str(interaction.user.id)
    fish_list = user_data.get(user, {}).get("fish_caught", [])
    if not fish_list:
        await interaction.response.send_message("คุณยังไม่ตกปลาเลย!")
        return
    fish_str = ", ".join(fish_list)
    money = user_data.get(user, {}).get("money", 0)
    await interaction.response.send_message(f"🐟 ปลาที่คุณตกได้: {fish_str}\n💰 เงินในบัญชี: {money} บาท")

@tree.command(name="daily", description="รับเงินรายวัน 100 บาท")
async def daily_cmd(interaction: discord.Interaction):
    user = str(interaction.user.id)
    now = int(time.time())
    if user in user_data and "last_daily" in user_data[user]:
        last = user_data[user]["last_daily"]
        if now - last < 86400:
            await interaction.response.send_message("⏳ คุณรับเงินรายวันไปแล้ว รออีกหน่อยนะ")
            return
    user_data.setdefault(user, {"fish_caught": [], "money": 0})
    user_data[user]["money"] += 100
    user_data[user]["last_daily"] = now
    await interaction.response.send_message("💵 รับเงินรายวัน 100 บาทเรียบร้อย!")

# ----------- Utility Commands -----------

@tree.command(name="time", description="ดูเวลาไทยตอนนี้")
async def time_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(f"🕰 เวลาไทยตอนนี้: `{get_thai_time()}`")

@tree.command(name="status", description="ดูสถานะบอท")
async def status_cmd(interaction: discord.Interaction):
    uptime = get_uptime()
    ping = round(bot.latency * 1000)
    guild_count = len(bot.guilds)
    
    embed = discord.Embed(title="สถานะบอท", color=0x00ff00)
    embed.add_field(name="สถานะ", value="ออนไลน์", inline=True)
    embed.add_field(name="ระยะเวลาทำงาน", value=uptime, inline=True)
    embed.add_field(name="Ping", value=f"{ping} ms", inline=True)
    embed.add_field(name="จำนวนเซิร์ฟเวอร์", value=str(guild_count), inline=True)
    embed.set_footer(text="namuiri_x 🔥")

    await interaction.response.send_message(embed=embed)

@tree.command(name="credits", description="เครดิตผู้สร้างบอท")
async def credits_cmd(interaction: discord.Interaction):
    await interaction.response.send_message("🔥 ผู้สร้างบอท: **namuiri_x 🔥**")

keep_alive()

token = os.environ['TOKEN']
bot.run(token)

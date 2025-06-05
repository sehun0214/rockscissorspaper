import discord
import asyncio
import os

intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # 메세지 내용 읽기 권한 필수

bot = discord.Bot(intents=intents)

game_in_progress = False
choices = {}  # {user_id: '가위'/'바위'/'보'}
game_channel = None

@bot.slash_command(name="가위바위보", description="가위바위보 게임을 시작합니다.")
async def rps(ctx: discord.ApplicationContext):
    global game_in_progress, choices, game_channel
    if game_in_progress:
        await ctx.respond("이미 게임이 진행 중입니다!", ephemeral=True)
        return

    game_in_progress = True
    choices = {}
    game_channel = ctx.channel

    await ctx.respond("가위바위보 게임 시작! 20초 안에 저에게 DM으로 '가위', '바위', '보'를 보내주세요!")

    await asyncio.sleep(20)

    if not choices:
        await game_channel.send("아무도 참여하지 않았습니다. 게임 종료.")
        game_in_progress = False
        return

    await show_results()
    game_in_progress = False

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    global game_in_progress

    if isinstance(message.channel, discord.DMChannel) and game_in_progress:
        choice = message.content.strip()

        synonyms = {
            '가위': ['가위', '찌'],
            '바위': ['바위', '묵'],
            '보': ['보', '빠']
        }

        normalized_choice = None
        for key, values in synonyms.items():
            if choice in values:
                normalized_choice = key
                break

        if normalized_choice:
            choices[message.author.id] = normalized_choice
            await message.channel.send(f"{normalized_choice} 선택 완료!")
        else:
            await message.channel.send("가위/바위/보 또는 묵/찌/빠 중 하나를 보내주세요.")
        return

    await bot.process_commands(message)

def determine_winner(p1_choice, p2_choice):
    wins = {'가위': '보', '바위': '가위', '보': '바위'}
    if p1_choice == p2_choice:
        return 0
    elif wins[p1_choice] == p2_choice:
        return 1
    else:
        return 2

async def show_results():
    if len(choices) < 2:
        await game_channel.send("참가자가 2명 미만이라 게임을 할 수 없습니다.")
        return
    
    user_ids = list(choices.keys())
    results = []
    
    for i in range(len(user_ids)):
        user_i = user_ids[i]
        win_count = 0
        for j in range(len(user_ids)):
            if i == j:
                continue
            user_j = user_ids[j]
            result = determine_winner(choices[user_i], choices[user_j])
            if result == 1:
                win_count += 1
        results.append((user_i, win_count))
    
    results.sort(key=lambda x: x[1], reverse=True)
    max_win = results[0][1]
    winners = [user for user, wins in results if wins == max_win]

    msg = "**가위바위보 결과 발표!**\n"
    for user_id, choice in choices.items():
        user = bot.get_user(user_id)
        msg += f"{user.display_name}: {choice}\n"
    
    if len(winners) == 1:
        winner_user = bot.get_user(winners[0])
        msg += f"\n🏆 승자는 {winner_user.display_name}님입니다! 축하합니다! 🏆"
    else:
        msg += f"\n무승부입니다! 승자가 없습니다."

    await game_channel.send(msg)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

token = os.getenv("DISCORD_TOKEN")
bot.run(token)

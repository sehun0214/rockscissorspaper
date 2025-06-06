import discord
from discord.ext import commands
import asyncio
import os
import random

intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # 메시지 내용 읽기 권한

bot = commands.Bot(command_prefix='!', intents=intents)

# 상태 변수들
game_in_progress = False
choices = {}  # {user_id: '가위'/'바위'/'보'}
game_channel = None
pending_ai_game = {}  # {user_id: True}

# 가위바위보 명령어 (단체용)
@bot.command()
async def 가위바위보(ctx):
    global game_in_progress, choices, game_channel
    if game_in_progress:
        await ctx.send("이미 게임이 진행 중입니다!")
        return

    game_in_progress = True
    choices = {}
    game_channel = ctx.channel

    await ctx.send("가위바위보 게임 시작! 20초 안에 저에게 DM으로 '가위', '바위', '보' 또는 '묵', '찌', '빠' 중 하나를 보내주세요!")

    await asyncio.sleep(20)

    if not choices:
        await ctx.send("아무도 참여하지 않았습니다. 게임 종료.")
        game_in_progress = False
        return

    await show_results()
    game_in_progress = False

# AI 가위바위보 명령어
@bot.command()
async def ai가위바위보(ctx):
    pending_ai_game[ctx.author.id] = True
    await ctx.send(f"{ctx.author.mention} 가위 / 바위 / 보 (또는 묵찌빠) 중 하나를 채팅으로 입력하세요!")

# 메시지 처리 (명령어 + DM + AI 게임 통합 처리)
@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.bot:
        return

    user_id = message.author.id
    content = message.content.strip()

    # 공통 가위바위보 입력 처리용 동의어
    synonyms = {
        '가위': ['가위', '찌'],
        '바위': ['바위', '묵'],
        '보': ['보', '빠']
    }

    # 단체 게임 중 DM으로 선택받기
    if isinstance(message.channel, discord.DMChannel) and game_in_progress:
        normalized_choice = None
        for key, values in synonyms.items():
            if content in values:
                normalized_choice = key
                break

        if normalized_choice:
            choices[user_id] = normalized_choice
            await message.channel.send(f"{normalized_choice} 선택 완료!")
        else:
            await message.channel.send("가위/바위/보 또는 묵/찌/빠 중 하나를 보내주세요.")
        return

    # AI 가위바위보 처리
    if user_id in pending_ai_game and pending_ai_game[user_id]:
        user_choice = None
        for k, v in synonyms.items():
            if content in v:
                user_choice = k
                break

        if not user_choice:
            await message.channel.send("가위 / 바위 / 보 (또는 묵찌빠) 중 하나만 골라주세요!")
            return

        ai_choice = random.choice(['가위', '바위', '보'])

        def winner(p1, p2):
            win = {'가위': '보', '바위': '가위', '보': '바위'}
            if p1 == p2:
                return 0
            elif win[p1] == p2:
                return 1
            else:
                return 2

        result = winner(user_choice, ai_choice)

        if result == 0:
            outcome = "비겼어요! 😐"
        elif result == 1:
            outcome = "이겼어요! 🎉"
        else:
            outcome = "졌어요... 😢"

        await message.channel.send(
            f"당신: {user_choice}\nAI: {ai_choice}\n\n**{outcome}**"
        )

        pending_ai_game.pop(user_id)

# 단체 게임 결과 출력 함수
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
        msg += "\n무승부입니다! 승자가 없습니다."

    await game_channel.send(msg)

# 승패 판단 함수
def determine_winner(p1_choice, p2_choice):
    wins = {'가위': '보', '바위': '가위', '보': '바위'}
    if p1_choice == p2_choice:
        return 0
    elif wins[p1_choice] == p2_choice:
        return 1
    else:
        return 2

# 봇 실행
token = os.getenv("DISCORD_TOKEN")
bot.run(token)

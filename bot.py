import discord
from discord.ext import commands, tasks
import asyncio
import os
import random

intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # 메세지 내용 읽기 권한 필수

bot = commands.Bot(command_prefix='!', intents=intents)

game_in_progress = False
choices = {}  # {user_id: '가위'/'바위'/'보'}
game_channel = None

@bot.command()
async def 가위바위보(ctx):
    global game_in_progress, choices, game_channel
    if game_in_progress:
        await ctx.send("이미 게임이 진행 중입니다!")
        return
    
    game_in_progress = True
    choices = {}
    game_channel = ctx.channel

    await ctx.send("가위바위보 게임 시작! 20초 안에 저에게 DM으로 '가위', '바위', '보'를 보내주세요!")

    # 20초 후 결과 발표
    await asyncio.sleep(20)
    
    if not choices:
        await ctx.send("아무도 참여하지 않았습니다. 게임 종료.")
        game_in_progress = False
        return

    # 결과 처리
    await show_results()

    game_in_progress = False

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    global game_in_progress

    if isinstance(message.channel, discord.DMChannel) and game_in_progress:
        choice = message.content.strip()

        # 묵찌빠 동의어 처리
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
            await message.channel.send(f"{normalized_choice} 선택 완료!")  # ✅ 여기는 OK
        else:
            await message.channel.send("가위/바위/보 또는 묵/찌/빠 중 하나를 보내주세요.")
        return

    await bot.process_commands(message)  # ← 이건 잊지 말고 항상 마지막에 넣어주세요

def determine_winner(p1_choice, p2_choice):
    # p1_choice가 이기면 1, 지면 2, 비기면 0 리턴
    wins = {'가위': '보', '바위': '가위', '보': '바위'}
    if p1_choice == p2_choice:
        return 0
    elif wins[p1_choice] == p2_choice:
        return 1
    else:
        return 2

async def show_results():
    # 참가자가 2명 이상일 때만 승패 계산
    if len(choices) < 2:
        await game_channel.send("참가자가 2명 미만이라 게임을 할 수 없습니다. AI 모드로 1인에서 플레이하세요!")
        return
    
    user_ids = list(choices.keys())
    results = []
    
    # 한 명씩 다른 사람과 비교해서 승패 판단 (간단하게 무승부 제외)
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
    
    # 가장 많이 이긴 사람 찾기
    results.sort(key=lambda x: x[1], reverse=True)
    max_win = results[0][1]
    winners = [user for user, wins in results if wins == max_win]

    # 결과 메시지 만들기
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

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

def determine_winner(p1_choice, p2_choice):
    wins = {'가위': '보', '바위': '가위', '보': '바위'}
    if p1_choice == p2_choice:
        return 0
    elif wins[p1_choice] == p2_choice:
        return 1
    else:
        return 2

@bot.command(name="ai가위바위보보")
async def ai_rps(ctx):
    await ctx.send(f"{ctx.author.mention} 가위 / 바위 / 보 중 하나를 채팅으로 입력하세요!(또는 묵찌빠빠)")

    def check(m):
        return (
            m.author == ctx.author and
            m.channel == ctx.channel and
            m.content.strip() in ['가위', '바위', '보', '묵', '찌', '빠']
        )

    try:
        user_msg = await bot.wait_for("message", timeout=15.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send("시간 초과! 다음에 다시 도전해주세요.")
        return

    synonyms = {
        '가위': ['가위', '찌'],
        '바위': ['바위', '묵'],
        '보': ['보', '빠']
    }

    user_raw_choice = user_msg.content.strip()
    user_choice = None
    user_display = None

    for key, values in synonyms.items():
        if user_raw_choice in values:
            user_choice = key
            if user_raw_choice != key:
                user_display = f"{key}({user_raw_choice})"
            else:
                user_display = key
            break

    ai_choice = random.choice(['가위', '바위', '보'])

    result_msg = f"당신: {user_display} vs 봇: {ai_choice}\n"

    result = determine_winner(user_choice, ai_choice)
    if result == 0:
        result_msg += "무승부입니다!"
    elif result == 1:
        result_msg += "당신이 이겼습니다! 🎉"
    else:
        result_msg += "당신은 Ai한테 졌어요... 😎"

    await ctx.send(result_msg)

@bot.command()
async def ai가위바위보(ctx):
    pending_ai_game[ctx.author.id] = True
    await ctx.send(f"{ctx.author.mention} 가위 / 바위 / 보 중 하나를 채팅으로 입력하세요!")



# 봇 토큰 넣어서 실행
token = os.getenv("DISCORD_TOKEN")
bot.run(token)

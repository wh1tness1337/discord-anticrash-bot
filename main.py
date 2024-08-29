import discord
from discord.ext import commands
from difflib import SequenceMatcher

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.bans = True
intents.guild_messages = True
intents.presences = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
previous_channels = {}
spam_count = {}
whitelist = [] 


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

log_channel_id = 1234567890
log_channel = None

def get_log_channel():
    global log_channel
    if log_channel is None:
        log_channel = bot.get_channel(log_channel_id)
    return log_channel

@bot.event
async def on_member_ban(guild, user):
    channel = get_log_channel()
    if channel:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            responsible_user = entry.user

            if responsible_user.id not in whitelist:
                embed = discord.Embed(
                    title=f"🛑 Участник **{user}** был забанен",
                    description=f"Забанил: **{responsible_user}**",
                    color=discord.Color.red()
                )
                embed.add_field(name="Участника нет в вайт листе и он был забанен!", value="", inline=False)
                await guild.ban(user, reason="Попытка сноса сервера")
                await channel.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=f"🛡️ Участник **{user}** был кикнут",
                    description=f"Кикнул: **{responsible_user}**",
                    color=discord.Color.green()
                )
                await channel.send(embed=embed)


@bot.event
async def on_member_remove(member):
    channel = get_log_channel()
    if channel:
        async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id:

                kicker = entry.user
                if kicker != bot.user:
                    try:
                        if kicker.id not in whitelist:
                            embed = discord.Embed(
                                title=f"🛑 Участник **{member}** был кикнут",
                                description=f"Кикнул: **{kicker}**",
                                color=discord.Color.red()
                            )
                            embed.add_field(name="Участника нет в вайт листе и он был забанен!", value="", inline=False)
                            await kicker.ban(reason="Кикнул участника, что запрещено.")
                            await channel.send(embed=embed)
                        else:
                            embed = discord.Embed(
                                title=f"🛡️ Участник **{member}** был кикнут",
                                description=f"Кикнул: **{kicker}**",
                                color=discord.Color.green()
                            )
                            await channel.send(embed=embed)
                    except discord.Forbidden:
                        print(f"Не хватает прав для бана {kicker}. Проверьте права бота.")
                    except discord.HTTPException:
                        print(f"Не удалось забанить {kicker}.")


@bot.event
async def on_guild_role_update(before, after):
    async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
        if entry.target.id == after.id:
            changer = entry.user


            permissions_changed = []
            for perm in discord.Permissions.VALID_FLAGS:
                before_perm = getattr(before.permissions, perm)
                after_perm = getattr(after.permissions, perm)
                if before_perm != after_perm:
                    change = f"{'✅' if after_perm else '❌'} {perm}"
                    permissions_changed.append(change)

            if permissions_changed:
                if changer.id not in whitelist:
                    embed = discord.Embed(
                        title=f"🛑 Роль **{after.name}** была изменена",
                        description=f"Изменил: **{changer}**",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="Измененные права:", value="\n".join(permissions_changed), inline=False)
                    embed.add_field(name="Участника нет в вайт листе и он был забанен!", value="", inline=False)
                    channel = get_log_channel()
                    await channel.send(embed=embed)
                    await changer.ban(reason="Попытка сноса сервера!")
                else:
                    embed = discord.Embed(
                        title=f"🛡️ Роль **{after.name}** была изменена",
                        description=f"Изменил: **{changer}**",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Измененные права:", value="\n".join(permissions_changed), inline=False)

                    channel = get_log_channel()
                    await channel.send(embed=embed)
            break

@bot.event
async def on_guild_role_create(role):
    channel = get_log_channel()
    if channel:
        async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
            user = entry.user
            if user.guild_permissions.manage_roles:
                try:

                    if user.id not in whitelist:

                        embed = discord.Embed(
                            title=f"🛑 Была создана роль **{role}**",
                            description=f"Создал: **{user}**",
                            color=discord.Color.red()
                        )
                        embed.add_field(name="Участника нет в вайт листе и он был забанен!", value="", inline=False)
                        await channel.send(embed=embed)
                        await role.guild.ban(user, reason="Забанен за создание роли!")
                    else:
                        embed = discord.Embed(
                            title=f"🛡️ Была создана роль **{role}**",
                            description=f"Создал: **{user}**",
                            color=discord.Color.green()
                        )
                        await channel.send(embed=embed)

                except discord.Forbidden:
                    print("У бота недостаточно прав для бана.")
                except discord.HTTPException as e:
                    print(f"Не удалось забанить пользователя: {e}")
@bot.event
async def on_guild_role_delete(role):
    channel = get_log_channel()
    if channel:
        async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            user = entry.user
            if user.guild_permissions.manage_roles:
                try:

                    if user.id not in whitelist:
                        await role.guild.ban(user, reason="Забанен за удаление роли!")
                        embed = discord.Embed(
                            title=f"🛑 Была удалена роль **{role}**",
                            description=f"Удалил: **{user}**",
                            color=discord.Color.red()
                        )
                        embed.add_field(name="Участника нет в вайт листе и он был забанен!", value="", inline=False)
                        await channel.send(embed=embed)
                        await role.guild.ban(user, reason="Забанен за удаление роли!")
                    else:
                        embed = discord.Embed(
                            title=f"🛡️ Была удалена роль **{role}**",
                            description=f"Удалил: **{user}**",
                            color=discord.Color.green()
                        )
                        await channel.send(embed=embed)
                except discord.Forbidden:
                    print("У бота недостаточно прав для бана.")
                except discord.HTTPException as e:
                    print(f"Не удалось забанить пользователя: {e}")

@bot.event
async def on_member_update(before, after):
    channel = get_log_channel()
    added_roles = set(after.roles) - set(before.roles)
    for role in added_roles:
        if role.name and role.permissions.administrator:

            if channel:
                async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                    if entry.target.id == after.id:
                        admin_issuer = entry.user
                        if admin_issuer.id not in whitelist:
                            embed = discord.Embed(
                                title=f"🛑 Была выдана роль с правами администратора **{role}** участнику **{after}**",
                                description=f"Выдал: **{admin_issuer}**",
                                color=discord.Color.red()
                            )
                            embed.add_field(name="Участника нет в вайт листе и он был забанен!", value="",inline=False)
                            await channel.send(embed=embed)
                            await after.remove_roles(role)
                            await after.guild.ban(admin_issuer, reason="Попытка сноса сервера")
                        else:
                            embed = discord.Embed(
                                title=f"🛡️ Была выдана роль с правами администратора **{role}** участнику **{after}**",
                                description=f"Выдал: **{admin_issuer}**",
                                color=discord.Color.green()
                            )
                            await channel.send(embed=embed)

@bot.event
async def on_guild_channel_create(channel):
    channel1 = get_log_channel()
    if channel.guild:

        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
            if entry.user.id not in whitelist:
                embed = discord.Embed(
                    title=f"🛑 Был создан канал **{channel.name}**",
                    description=f"Создатель: **{entry.user}** ",
                    color=discord.Color.red()
                )
                embed.add_field(name="Участника нет в вайт-листе и он был забанен, а канал удален!", value="", inline=False)
                await channel1.send(embed=embed)
                await channel.delete(reason="Создание канала без разрешения")
                await entry.user.ban(reason="Попытка сноса сервера!")
            else:
                embed = discord.Embed(
                    title=f"🛡️ Был создан канал **{channel.name}**",
                    description=f"Создатель: **{entry.user}** ",
                    color=discord.Color.green()
                )
                await channel1.send(embed=embed)
@bot.event
async def on_guild_channel_delete(channel):
    channel1 = get_log_channel()
    if channel.guild:
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):

            previous_channels[channel.id] = {
                'name': channel.name,
                'position': channel.position,
                'overwrites': channel.overwrites,
                'category_id': channel.category_id
            }

            if entry.user.id not in whitelist:
                embed = discord.Embed(
                    title=f"🛑 Был удален канал **{channel.name}**",
                    description=f"Удалил: **{entry.user}**",
                    color=discord.Color.red()
                )
                embed.add_field(name="Участника нет в вайт-листе и он был забанен!", value="", inline=False)
                await channel1.send(embed=embed)
                await restore_channel(channel.guild, previous_channels[channel.id])
                await entry.user.ban(reason="Удаление каналов")

            else:
                embed = discord.Embed(
                    title=f"🛡️ Был удален канал **{channel.name}**",
                    description=f"Удалил: **{entry.user}**",
                    color=discord.Color.green()
                )
                await channel1.send(embed=embed)


async def restore_channel(guild, channel_data):
    try:
        category = guild.get_channel(channel_data['category_id']) if channel_data['category_id'] else None

        restored_channel = await guild.create_text_channel(
            name=channel_data['name'],
            position=channel_data['position'],
            overwrites=channel_data['overwrites'],
            category=category
        )
        print(
            f'Канал {restored_channel.name} был восстановлен в категорию {category.name if category else "без категории"}.')
    except discord.HTTPException as e:
        print(f'Не удалось восстановить канал: {e}')



@bot.event
async def on_message(message):
    author_id = message.author
    author_id1 = message.author.id
    muted_role_name = "Zamu4en"

    channel = get_log_channel()
    muted_role = discord.utils.get(message.guild.roles, name=muted_role_name)


    if author_id1 in whitelist:
        return

    content = message.content.lower()
    banned_words = ["http", "https", ".com", ",com", ",gg", ".gg", ".ru", "ru", ".net", ",net", "gg/", "gg /", ".fun", ",fun"]


    for word in banned_words:
        if word in content:
            if message.author.guild_permissions.administrator:
                embed = discord.Embed(
                    title=f"🛡️ **{author_id}** был замучен за отправку ссылок",
                    description=f"Сообщение: `{message.content}`",
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)
                await message.author.ban(reason='Попытка рейда')
            else:

                if not muted_role:
                    muted_role = await message.guild.create_role(name=muted_role_name)
                    for ch in message.guild.channels:
                        await ch.set_permissions(muted_role, send_messages=False)

                await message.author.add_roles(muted_role)
                embed = discord.Embed(
                    title=f"🛡️ **{author_id}** был замучен за отправку ссылок",
                    description=f"Сообщение: `{message.content}`",
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)
            await message.delete()
            break

    if author_id1 not in whitelist:
        if author_id in spam_count:
            similarity = similar(message.content, spam_count[author_id]['last_message'])

            if similarity >= 0.75:
                spam_count[author_id]['count'] += 1
                if spam_count[author_id]['count'] > 2:
                    if message.author.guild_permissions.administrator:
                        embed = discord.Embed(
                            title=f"🛡️ **{author_id}** был замучен за спам",
                            description=f"Сообщение: `{message.content}`",
                            color=discord.Color.red()
                        )
                        await channel.send(embed=embed)
                        await message.author.ban(reason='Попытка рейда')
                    else:
                        if not muted_role:
                            muted_role = await message.guild.create_role(name=muted_role_name)
                            for ch in message.guild.channels:
                                await ch.set_permissions(muted_role, send_messages=False)

                        await message.author.add_roles(muted_role)
                        embed = discord.Embed(
                            title=f"🛡️ **{author_id}** был замучен за спам",
                            description=f"Сообщение: `{message.content}`",
                            color=discord.Color.red()
                        )
                        await channel.send(embed=embed)

                    async for hist_message in message.channel.history(limit=10):
                        if similar(hist_message.content, message.content) >= 0.75:
                            await hist_message.delete()

                    spam_count[author_id]['count'] = 0
            else:
                spam_count[author_id] = {'count': 1, 'last_message': message.content}
        else:
            spam_count[author_id] = {'count': 1, 'last_message': message.content}

        spam_count[author_id]['last_message'] = message.content

    await bot.process_commands(message)


bot.run('')

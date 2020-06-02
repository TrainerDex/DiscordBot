from discord.ext import commands
from core.models import DiscordUser, DiscordGuild

class Welcomer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print('Welcomer initiated')
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guilddb = DiscordGuildSettings.objects.get_or_create(id=member.guild.id)[0]
        
        if not guilddb.welcomer:
            return
        
        channel = self.bot.get_channel(guilddb.welcomer_channel.id) or member.guild.system_channel
        
        if not channel:
            return
        
        try:
            trainer = DiscordUser.objects.get(uid=str(member.id)).user.trainer
            if guilddb.welcomer_message_existing:
                await channel.send(guilddb.welcomer_message_existing.format(trainer=trainer, guild=member.guild, member=member))
            else:
                await channel.send("Welcome {trainer.nickname} to {guild.name}. I've found you in our database.".format(trainer=trainer, guild=member.guild, member=member))
        except DiscordUser.DoesNotExist:
            if guilddb.welcomer_message_new:
                await channel.send(guilddb.welcomer_message_new.format(trainer=trainer, guild=member.guild, member=member))
            else:
                await channel.send("Welcome {member} to {guild.name}. Are you new?".format(guild=member.guild, member=member))
    
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def simulate_join(self, ctx):
        """Simulates on_member_join"""
        await self.on_member_join(ctx.author)
    
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def set_welcome_message_new(self, ctx, *, msg: str):
        """Sets the welcome message"""
        if msg=='none':
            msg=None
        guilddb = DiscordGuildSettings.objects.get_or_create(id=ctx.message.channel.guild.id)[0]
        guilddb.welcomer_message_new = msg
        guilddb.save()
        await ctx.send(f"Welcome message for new users set to '{guilddb.welcomer_message_new}' for this server.")
    
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def set_welcome_message_existing(self, ctx, *, msg: str):
        """Sets the welcome message"""
        if msg=='none':
            msg=None
        guilddb = DiscordGuildSettings.objects.get_or_create(id=ctx.message.channel.guild.id)[0]
        guilddb.welcomer_message_existing = msg
        guilddb.save()
        await ctx.send(f"Welcome message for existing users set to '{guilddb.welcomer_message_existing}' for this server.")

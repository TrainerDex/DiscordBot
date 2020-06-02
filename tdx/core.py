import logging
import os
import discord

from redbot.core import checks, commands, Config
from trainerdex.client import Client, Trainer

log = logging.getLogger("red.tdx.core")
POGOOCR_TOKEN_PATH = os.path.join(os.path.dirname(__file__), 'data/key.json')

class TrainerDexCore(commands.Cog):
    """TrainerDex Core Functionality"""
    
    def __init__(self, bot) -> None:
        self.bot = bot
        self.config = Config.get_conf(self, identifier=8124637339) # TrainerDex on a T9 keyboard
        self.client: Client = None
        
        assert os.path.isfile(POGOOCR_TOKEN_PATH) # Looks for a Google Cloud Token
        
        self.global_defaults = {
            'embed_footer': 'Provided with ❤️ by TrainerDex',
            'notice': None,
        }
        self.guild_defaults = {
            'emoji_success': "✅",
            'emoji_failure': "❌",
            'emoji_warning': "⚠️",
            'emoji_notice': "⚠️",
            'emoji_loading': "<a:loading:471298325904359434>",
        }
        
        self.config.register_global(**self.global_defaults)
        self.config.register_guild(**self.guild_defaults)
    
    async def initialize(self) -> None:
        await self._creat_client()
    
    async def _creat_client(self) -> None:
        """Create TrainerDex API Client"""
        token = await self._get_token()
        self.client = Client(token=token)
    
    async def _get_token(self) -> str:
        """Get TrainerDex token"""
        api_tokens = await self.bot.get_shared_api_tokens("trainerdex")
        token = api_tokens.get("token", "")
        if not token:
            log.warning("No valid token found")
        return token
    
    class BaseCard(discord.Embed):
        
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            # Set default colour
            try:
                self.colour = kwargs['colour']
            except KeyError:
                self.colour = kwargs.get('color', 13252437)
            
            self._author = {
                'name': 'TrainerDex',
                'url': 'https://www.trainerdex.co.uk/',
                'icon_url': 'https://www.trainerdex.co.uk/static/img/android-desktop.png',
            }
        
        async def build_card(self, parent, ctx):
            self._parent = parent
            self._ctx = ctx
            
            self._footer = {
                'text': await self._parent.config.embed_footer()
            }
            
            notice = await self._parent.config.notice()
            if notice:
                if self._ctx.guild:
                    emoji = await self._parent.config.guild(self._ctx.guild).emoji_notice()
                else:
                    emoji = self._parent.guild_defaults.get("emoji_notice")
                self._notice = f"{emoji} {notice}"
                
                if self.description:
                    self.description = "{}\n\n{}".format(self._notice, self.description)
                else:
                    self.description = self._notice
            return self
    
    async def _get_BaseCard(self, ctx, **kwargs):
        return await self.BaseCard(**kwargs).build_card(self, ctx)
    
    class ProfileCard(BaseCard):
        
        def __init__(self, trainer: Trainer, **kwargs):
            super().__init__(**kwargs)
            self._trainer = trainer
            self.colour = self._trainer.team.colour.get('hex', self.colour)
            self.title = '{nickname} | TL{level}'.format(nickname=self._trainer.nickname, level=self._trainer.level.level)
            self.url = 'https://www.trainerdex.co.uk/profile?id={}'.format(self._trainer.id)
            self.timestamp = max(self._trainer.last_modified, max(self._trainer.updates, key=lambda x: x.update_time).update_time)
        
        async def build_card(self, parent, ctx):
            await super().build_card(parent, ctx)
            self.add_field(name='Team', value=self._trainer.team.name)
            self.add_field(name='Level', value=self._trainer.level.level)
            self.add_field(name='Total XP', value="{:,}".format(self._trainer.get_current_stat('total_xp')))
            return self
        
        async def add_leaderboards(self):
            if self._ctx.guild:
                guild_leaderboard = self._parent.client.get_discord_leaderboard(self._ctx.guild.id)
                if self._trainer in guild_leaderboard:
                    self.insert_field_at(
                        index = 0,
                        name = '{guild} Leaderboard'.format(guild=self._ctx.guild.name),
                        value = str(list(guild_leaderboard.filter_trainers([self._trainer.id]))[0].position),
                    )
            
            leaderboard = self._parent.client.get_worldwide_leaderboard()
            if self._trainer in leaderboard:
                self.insert_field_at(
                    index = 0,
                    name = 'Global Leaderboard',
                    value = str(list(leaderboard.filter_trainers([self._trainer.id]))[0].position),
                )
    
    async def _get_ProfileCard(self, ctx, trainer: Trainer, **kwargs):
        return await self.ProfileCard(trainer, **kwargs).build_card(self, ctx)
    
    async def _get_emoji(self, ctx, emoji: str):
        """Returns the default or set emoji based on context"""
        
        if f'emoji_{emoji}' not in self.guild_defaults:
            raise NotFoundError
        
        if ctx.guild:
            return await getattr(self.config.guild(ctx.guild), f'emoji_{emoji}')()
        return self.guild_defaults.get(f'emoji_{emoji}')
    
    @commands.command()
    async def whois(self, ctx, trainer: str):
        emoji_loading = await self._get_emoji(ctx, 'loading')
        emoji_failure = await self._get_emoji(ctx, 'failure')
        emoji_warning = await self._get_emoji(ctx, 'warning')
        
        message = await ctx.send('{} Searching for profile...'.format(emoji_loading))
        trainer = self.client.search_trainer(trainer)
        
        if trainer:
            await message.edit(content='{} Found profile. Loading...'.format(emoji_loading))
        else:
            await message.edit(content='{} Profile not found.'.format(emoji_failure))
            
        embed = await self._get_ProfileCard(ctx, trainer)
        await message.edit(content='{} Checking leaderboards...'.format(emoji_loading), embed=embed)
        try:
            await embed.add_leaderboards()
        except Exception as e:
            await message.edit(content='{} Error in leaderboard.'.format(emoji_warning), embed=embed)
            raise e
        await message.edit(content=None, embed=embed)

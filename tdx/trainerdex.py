#!/usr/bin/env python
import asyncio
import cv2
import datetime
import discord
import glob
import humanize
import json
import math
import maya
import numpy as np
import operator
import os
import pendulum
import pycent
import pytz
import random
import requests
import statistics
import trainerdex
import PogoOCR
from .utils import checks
from .utils.dataIO import dataIO
from collections import namedtuple
from discord.ext import commands


# settings_file = 'data/trainerdex/settings.json'
# json_data = dataIO.load_json(settings_file)
# token = json_data['token']

EMOJI_POSITIVE = "\U0001F44D"
EMOJI_NEGATIVE = "\U0001F44E"

Difference = namedtuple('Difference', [
	'old_date',
	'old_xp',
	'new_date',
	'new_xp',
	'change_time',
	'change_xp',
])

class StartDateUpdate:
	
	def __init__(self, trainer):
		self.raw = None
		self.id = 0-trainer.id
		self.update_time = trainer.start_date
		self.xp = 0
	
	@classmethod
	def level(cls):
		return 1
	
	@classmethod
	def trainer(cls):
		return trainer

class TrainerDex:
	
	def __init__(self, bot):
		self.bot = bot
		self.join_client = trainerdex.Client(token=token, identifier='ss_registration') if token else trainerdex.Client()
		self.client = trainerdex.Client(token=token, identifier='ts_social_discord') if token else trainerdex.Client()
		self.ocr_client = trainerdex.Client(token=token, identifier='ss_ocr') if token else trainerdex.Client()
	
	async def get_trainer(self, username=None, discord=None, account=None, prefered=True):
		"""Returns a Trainer object for a given discord, trainer username or account id
		
		Search is done in the order of username > discord > account, if you specify more than one, it will ONLY search the first one.
		"""
		
		if username:
			return self.client.get_trainer_from_username(username)
		elif discord and prefered==True:
			try:
				for x in self.client.get_discord_user(uid=[discord])[0].owner().trainer():
					if x.prefered:
						return x
			except IndexError:
				return None
		elif discord and prefered==False:
			try:
				return self.client.get_discord_user(uid=[discord])[0].trainer()
			except IndexError:
				return None
		elif account and prefered==True:
			for x in self.client.get_user(account)[0].owner().trainer():
				if x.prefered:
					return x
		elif account and prefered==False:
			return self.client.get_user(account).trainer()
		
	async def getTeamByName(self, team: str):
		return {'teamless':trainerdex.get_team(0),'mystic':trainerdex.get_team(1),'valor':trainerdex.get_team(2),'instinct':trainerdex.get_team(3)}[team.lower()]
	
	async def getDiff(self, trainer, days: int):
		updates = trainer.updates()
		if trainer.start_date:
			updates.append(StartDateUpdate(trainer))
		updates.sort(key=lambda x: x.update_time)
		latest = trainer.update
		first = updates[-1]
		reference = [x for x in updates if x.update_time <= (datetime.datetime.now(pytz.utc)-datetime.timedelta(days=days)+datetime.timedelta(hours=6))]
		reference.sort(key=lambda x: x.update_time, reverse=True)
		if reference==[]:
			if latest==first:
				diff = Difference(
					old_date = None,
					old_xp = None,
					new_date = latest.update_time,
					new_xp = latest.xp,
					change_time = None,
					change_xp = None
				)
				return diff
			elif first.update_time > (latest.update_time-datetime.timedelta(days=days)+datetime.timedelta(hours=3)):
				reference=first
		else:
			reference = reference[0]
		diff = Difference(
				old_date = reference.update_time,
				old_xp = reference.xp,
				new_date = latest.update_time,
				new_xp = latest.xp,
				change_time = latest.update_time-reference.update_time,
				change_xp = latest.xp-reference.xp
			)
		
		return diff
	
	async def updateCard(self, ctx_msg, trainer, days=None):
		dailyDiff = await self.getDiff(trainer, days or 1)
		level=trainer.level
		embed=discord.Embed(timestamp=dailyDiff.new_date, colour=int(trainer.team().colour.replace("#", ""), 16))
		embed.set_author(name="TrainerDex", url="https://www.trainerdex.co.uk/", icon_url='https://www.trainerdex.co.uk/static/img/favicon.png')
		embed.title = '{} | TL {}'.format(trainer.username, level.level)
		embed.url = "https://www.trainerdex.co.uk/profile?id={}".format(trainer.id)
		settings = dataIO.load_json(settings_file)
		if settings['message']:
			embed.description = settings['message']
		else:
			embed.description = "Graphs can be found on [your profile](https://www.trainerdex.co.uk/profile?id={id}).".format(id=trainer.id)
		embed.set_footer(text="Provided for free️ by TrainerDex")
		embed.set_thumbnail(url='https://www.trainerdex.co.uk/static/img/{}.png'.format(trainer.team().name))
		for x in self.client.leaderboard():
			if x['id'] == trainer.id:
				embed.add_field(
					name='Global Leaderboard',
					value=x['position']
				)
		if ctx_msg.server:
			try:
				embed.add_field(
					name='Server Leaderboard',
					value=self.client.get_discord_leaderboard(ctx_msg.server.id).filter_trainers([trainer.id])[0].position
				)
			except IndexError:
				pass
			except requests.exceptions.HTTPError:
				pass
		embed.add_field(name='Level', value=level.level)
		if level.level != 40:
			embed.add_field(name='XP', value='{:,} / {:,}'.format(trainer.update.xp-level.total_xp,level.xp_required))
		embed.add_field(name='Total XP', value="{:,}".format(dailyDiff.new_xp))
		if dailyDiff.change_xp and dailyDiff.change_time:
			gain = '{:,} since {}. '.format(dailyDiff.change_xp, humanize.naturaldate(dailyDiff.old_date))
			if dailyDiff.change_time.days>1:
				gain += "That's {:,} xp/day.".format(round(dailyDiff.change_xp/dailyDiff.change_time.days))
			embed.add_field(name='Gain', value=gain)
			if trainer.goal_daily and dailyDiff.change_time.days>0:
				dailyGoal = trainer.goal_daily
				embed.add_field(name='Daily completion', value='{}% towards {:,}'.format(pycent.percentage(dailyDiff.change_xp/max(1,dailyDiff.change_time.days), dailyGoal), dailyGoal))
		if trainer.goal_total and trainer.goal_total!=0:
			totalGoal = trainer.goal_total
		else:
			totalGoal = None
		if totalGoal:
			totalDiff = await self.getDiff(trainer, days or 7)
			embed.add_field(name='Goal remaining', value='{:,} out of {}'.format(totalGoal-totalDiff.new_xp, humanize.intword(totalGoal)))
			if totalDiff.change_time.seconds>=1:
				eta = lambda x, y, z: round(x/(y/z))
				eta = eta(totalGoal-totalDiff.new_xp, totalDiff.change_xp, totalDiff.change_time.total_seconds())
				eta = totalDiff.new_date+datetime.timedelta(seconds=eta)
				embed.add_field(name='Goal ETA', value=humanize.naturaltime(eta.replace(tzinfo=None)))
			if totalDiff.change_time.total_seconds()<583200 or days:
				embed.description = "⚠️ ETA may be inaccurate. Using {} of data.".format(humanize.naturaldelta(totalDiff.change_time))
		
		return embed
	
	async def profileCard(self, ctx_msg, name: str, force=False):
		try:
			trainer = await self.get_trainer(username=name)
		except LookupError:
			raise
		if not trainer:
			raise LookupError("Trainer not found")
		account = trainer.owner()
		discordUser = account.discord()[0]
		level=trainer.level
		
		embed=discord.Embed(timestamp=trainer.update.update_time, colour=int(trainer.team().colour.replace("#", ""), 16))
		embed.set_author(name="TrainerDex", url="https://www.trainerdex.co.uk/", icon_url='https://www.trainerdex.co.uk/static/img/favicon.png')
		embed.title = '{} | TL {}'.format(trainer.username, level.level)
		embed.url = "https://www.trainerdex.co.uk/profile?id={}".format(trainer.id)
		embed.set_footer(text="Provided with ❤️ by TrainerDex")
		embed.set_thumbnail(url='https://www.trainerdex.co.uk/static/img/{}.png'.format(trainer.team().name))
		for x in self.client.leaderboard():
			if x['id'] == trainer.id:
				embed.add_field(
					name='Global Leaderboard',
					value=x['position']
				)
		if ctx_msg.server:
			try:
				embed.add_field(
					name='Server Leaderboard',
					value=self.client.get_discord_leaderboard(ctx_msg.server.id).filter_trainers([trainer.id])[0].position
				)
			except LookupError:
				pass
		embed.add_field(name='Team', value=trainer.team().name)
		if trainer.update.xp <= 39999999:
			embed.add_field(name='Level', value=level.level)
		else:
			embed.add_field(name='Level', value="40x{}".format(int(trainer.update.xp/20000000)))
		if level.level != 40:
			embed.add_field(name='XP', value='{:,} / {:,}'.format(trainer.update.xp-level.total_xp,level.xp_required))
		embed.add_field(name='Total XP', value="{:,}".format(trainer.update.xp))
		if discordUser:
			embed.add_field(name='Discord', value='<@{}>'.format(discordUser.id))
		if trainer.cheater is True:
			desc = "⚠️ {} has been known to cheat."
			embed.description = desc.format(trainer.username)
		return embed
	
	async def _addProfile(self, message, mention, username: str, xp: int, team, has_cheated=False, currently_cheats=False, name: str=None, prefered=True, datetime=None):
		#Check existance
		print('Attempting to add {} to database, checking if they already exist'.format(username))
		trainer = await self.get_trainer(username=username)
		if trainer:
			print('⚠️ Found {}, updating XP and aborting...'.format(username))
			await self.bot.edit_message(message, "⚠️ A record already exists in the database for this trainer.")
			if xp > trainer.update.xp:
				if datetime:
					update = self.join_client.create_update(trainer.id, xp, time_updated=maya.MayaDT.from_datetime(datetime))
				else:
					update = self.join_client.create_update(trainer.id, xp)
				trainer = await self.get_trainer(username=username)
			return trainer
		#Create or get auth.User and discord user
		print('⚠️ Checking if existing Discord User {} exists in our database...'.format(mention.id))
		discordUserlist=self.client.get_discord_user(uid=[mention.id])
		if discordUserlist:
			print('⚠️ Found... Using that.')
			discordUser = discordUserlist[0]
			user = discordUser.owner()
		else:
			user = self.client.create_user(username=username, first_name=name)
			discordUser = self.client.import_discord_user(uid=mention.id, user=user.id)
		#create trainer
		print('⚠️ Creating trainer...')
		trainer = self.client.create_trainer(username=username, team=team.id, has_cheated=has_cheated, currently_cheats=currently_cheats, prefered=prefered, account=user.id, verified=True)
		print('✅ Trainer created. Creating update object...')
		#create update object
		if datetime:
			update = self.join_client.create_update(trainer.id, xp, time_updated=maya.MayaDT.from_datetime(datetime))
		else:
			update = self.join_client.create_update(trainer.id, xp)
		print('✅ Update object created')
		return trainer
	
	#Public Commands
	
	@commands.command(pass_context=True, name="trainer")
	async def trainer(self, ctx, trainer: str):
		"""Look up a Pokemon Go Trainer
		
		Example: trainer JayTurnr
		"""
		
		message = await self.bot.say('<a:loading:471298325904359434> Searching...')
		await self.bot.send_typing(ctx.message.channel)
		if len(ctx.message.mentions) >= 1:
			trainer = await self.get_trainer(discord=ctx.message.mentions[0].id)
			tainer = trainer.username
		try:
			embed = await self.profileCard(ctx.message, trainer)
			await self.bot.edit_message(message, new_content=' ', embed=embed)
		except LookupError as e:
			await self.bot.edit_message(message, '`Error: '+str(e)+'`')
	
	@commands.command(pass_context=True)
	async def projection(self, ctx, days: int):
		"""
		Get an estimate of what your XP will be in x days since your last update
		"""
		
		trainer = await self.get_trainer(discord=ctx.message.author.id)
		if not trainer:
			await self.bot.say("It looks like you're not set up to use this command. Please contact an admin or <@319792326958514176>.")
			return
		
		playtime = 4
		playtime_fraction = datetime.timedelta(hours=playtime).total_seconds()/datetime.timedelta(days=1).total_seconds()
		
		progression = await self.getDiff(trainer, 7)
		progression_raw_rate = progression.change_xp/(progression.change_time.total_seconds()*playtime_fraction)
		progression_day_rate = progression_raw_rate*datetime.timedelta(hours=playtime).total_seconds()
		estimated_gain = int(progression_day_rate*days)
		
		await self.bot.say("Based on the forumla of {rate}… xp/day over {time}, on {futuredate}, I reckon you will be at {predicted:,}XP ({gain:,} gain)".format(
			rate = int(progression_day_rate),
			time = humanize.naturaldelta(progression.change_time),
			futuredate = humanize.naturaldate(progression.new_date+datetime.timedelta(days=days)),
			predicted = estimated_gain+trainer.update.xp,
			gain = estimated_gain
		))
		
	
	@commands.command(pass_context=True)
	async def progress(self, ctx, trainer=None):
		"""Find out information about your own progress"""
		
		if trainer:
			trainer = await self.get_trainer(username=trainer)
		else:
			trainer = await self.get_trainer(discord=ctx.message.author.id)
			if not trainer:
				await self.bot.say("It looks like you're not set up to use this command. Please contact an admin or <@319792326958514176>.")
				return
		
		message = await self.bot.say('<a:loading:471298325904359434> Thinking...')
		await self.bot.send_typing(ctx.message.channel)
		
		if trainer:
			embed = await self.updateCard(ctx.message, trainer)
			await self.bot.edit_message(message, new_content='✅', embed=embed)
		else:
			await self.bot.edit_message(message, '❌ `Error: Trainer not found`')
	
	@commands.group(pass_context=True)
	async def update(self, ctx):
		"""Update information about your TrainerDex profile"""
			
		if ctx.invoked_subcommand is None:
			await self.bot.send_cmd_help(ctx)
	
	@commands.command(pass_context=True)
	async def average(self, ctx, days: int):
		message = await self.bot.say('<a:loading:471298325904359434> Calculating...')
		trainer = await self.get_trainer(discord=ctx.message.author.id)
		if not trainer:
			await self.bot.say("It looks like you're not set up to use this command. Please contact an admin or <@319792326958514176>.")
			return
		else:
			embed = await self.updateCard(ctx.message, trainer, days=days)
			await self.bot.edit_message(message, new_content=' ', embed=embed)
	
	async def __update_xp(self, author, xp, message, ocr=False):
		trainer = await self.get_trainer(discord=author.id)
		if trainer:
			if trainer.update.xp > int(xp):
				await self.bot.edit_message(message, "❌ You've previously set your XP to higher than what you're trying to set it to. It's currently set to {xp:,}. If this is incorrect, please contact us on Twitter. @TrainerDexApp".format(xp=trainer.update.xp))
				return
			elif trainer.update.xp == int(xp):
				await self.bot.edit_message(message, "⚠️ You've already set your XP to this figure. In future, to see the output again, please run the `progress` command as it costs us to run OCR. <a:loading:471298325904359434> Loading output")
				embed = await self.updateCard(message, trainer)
				await self.bot.edit_message(message, "⚠️ You've already set your XP to this figure. In future, to see the output again, please run the `progress` command as it costs us to run OCR.", embed=embed)
				return
			
			# Update XP
			update = self.ocr_client.create_update(trainer.id, xp) if ocr == True else self.client.create_update(trainer.id, xp)
			
			await self.bot.edit_message(message, new_content='✅ Success\n<a:loading:471298325904359434> Loading response...')
			await asyncio.sleep(1)
			
			trainer = self.client.get_trainer(trainer.id) #Refreshes the trainer
			embed = await self.updateCard(message, trainer)
			await self.bot.edit_message(message, new_content='✅ Success', embed=embed)
		else:
			await self.bot.edit_message(message, '❌ `Error: Trainer not found`\n\nPlease contact us on Twitter. @TrainerDexApp')

	@update.command(name="badges", pass_context=True)
	async def advanced_update(self, ctx):
		await self.bot.say("To update your badges, go to https://www.trainerdex.co.uk/tools/update_stats/ - when prompted to log in, choose the 'Discord' log in option at the bottom.")
	
	@update.command(name="start", pass_context=True)
	async def start_date(self, ctx, *, date: str):
		"""Set the day you started Pokemon Go"""
		
		message = await self.bot.say('<a:loading:471298325904359434> Thinking...')
		await self.bot.send_typing(ctx.message.channel)
		trainer = await self.get_trainer(discord=ctx.message.author.id)
		if not trainer:
			await self.bot.say("It looks like you're not set up to use this command. Please contact an admin or <@319792326958514176>.")
			return
		try:
			suspected_time = pendulum.parse(date)
		except pendulum.parsing.exceptions.ParserError:
			await self.bot.edit_message(message, "❓ I can't figure out what you mean by '{}', can you please use YYYY/MM/DD".format(date))
			return
		await self.bot.edit_message(message, "Just to confirm, you mean {}, right? {emoji_pos}/{emoji_neg}".format(humanize.naturaldate(suspected_time), emoji_pos=EMOJI_POSITIVE, emoji_neg=EMOJI_NEGATIVE))
		await self.bot.add_reaction(message, EMOJI_POSITIVE)
		await self.bot.add_reaction(message, EMOJI_NEGATIVE)
		reaction = await self.bot.wait_for_reaction(user=ctx.message.author, emoji=[EMOJI_POSITIVE, EMOJI_NEGATIVE], message=message)
		await self.bot.remove_reaction(message, EMOJI_POSITIVE, self.bot.user)
		await self.bot.remove_reaction(message, EMOJI_NEGATIVE, self.bot.user)
		if reaction.reaction.emoji == EMOJI_POSITIVE:
			if suspected_time.date() < datetime.date(2016, 7, 5):
				message = await self.bot.say("❌ The date you entered was before launch date of 6th July 2016. Sorry, but you can't do that.")
				return
			self.client.update_trainer(trainer, start_date=suspected_time)
			await self.bot.say("✅ {}, your start date has been set to {}".format(ctx.message.author.mention, humanize.naturaldate(suspected_time)))
		elif reaction.reaction.emoji == EMOJI_NEGATIVE:
			await self.bot.say("❓ Not getting the right date? Use ISO 8601. (YYYY/MM/DD)")
	
	@update.command(name="goal", pass_context=True, disabled=True)
	async def goal(self, ctx, which: str, goal):
		"""Update your goals
		
		Example: update goal daily 2000
		"""
		
		message = await self.bot.say('<a:loading:471298325904359434> Processing...\n⚠️ This command will hopefully be changed soon.')
		await self.bot.send_typing(ctx.message.channel)
		trainer = await self.get_trainer(discord=ctx.message.author.id)
		if not trainer:
			await self.bot.edit_message(message, "❌ It looks like you're not set up to use this command. Please contact an admin or <@319792326958514176>.")
			return
		if which.title()=='Daily':
			trainer = self.client.update_trainer(trainer, daily_goal=goal)
			embed = await self.updateCard(ctx.message, trainer)
			await self.bot.edit_message(message, "✅ {}, your daily goal has been set to {:,}\n⚠️ This command will hopefully be changed soon.".format(ctx.message.author.mention, int(goal)), embed=embed)
		elif which.title()=='Total':
			if goal == 'auto':
				current_level = trainer.level.level
				if current_level != 40:
					next_level = trainerdex.level_parser(level=current_level+1)
					goal_needed = next_level.total_xp
					trainer = self.client.update_trainer(trainer, total_goal=goal_needed)
					embed = await self.updateCard(ctx.message, trainer)
					await self.bot.edit_message(message, "✅ I've automatically set your goal to {goal_needed}, which is what you need to reach TL {nlevel}.\n⚠️ This command will hopefully be changed soon.".format(goal_needed=goal_needed, nlevel=next_level.level), embed=embed)
				else:
					goal_needed = trainer.update.xp + (20000000 - trainer.update.xp % 20000000)
					trainer = self.client.update_trainer(trainer, total_goal=goal_needed)
					embed = await self.updateCard(ctx.message, trainer)
					await self.bot.edit_message(message, "✅ I've automatically set your goal to {goal_needed}, which is what you need to reach TL 40x{multiplier}.\n⚠️ This command will hopefully be changed soon.".format(goal_needed=goal_needed, multiplier=int(goal_needed/20000000)), embed=embed)
			elif int(goal)>trainer.update.xp or int(goal)==0:
				trainer = self.client.update_trainer(trainer, total_goal=int(goal))
				embed = await self.updateCard(ctx.message, trainer)
				await self.bot.edit_message(message, "✅ {}, your total goal has been set to {:,}.\n⚠️ This command will hopefully be changed soon.".format(ctx.message.author.mention, int(goal)), embed=embed)
			else:
				await self.bot.edit_message(message, "❌ {}, try something higher than your current XP of {:,}.\n⚠️ This command will hopefully be changed soon.".format(ctx.message.author.mention, trainer.update.xp))
		else:
			await self.bot.edit_message(message, "❓ {}, please choose 'Daily' or 'Total' for after goal.\n⚠️ This command will hopefully be changed soon.".format(ctx.message.author.mention))
	
	@commands.command(pass_context=True, no_pm=True)
	async def leaderboard(self, ctx, modifier=None, mod2=None):
		"""
		View the leaderboard for your server
		
		Modifiers:
		mystic, valor, instinct - automatic if ran in a chat with those teams in the name
		no40 - level 39s and lower
		lowerthan - expects a sections paramter, which is the max level you want to see
		"""
		
		message = await self.bot.say("<a:loading:471298325904359434> Thinking...")
		await self.bot.send_typing(ctx.message.channel)
		leaderboard = self.client.get_discord_leaderboard(ctx.message.server.id)
		embed=discord.Embed(title=leaderboard.title, timestamp=leaderboard.time)
		embed.set_footer(text="Provided with ❤️ by TrainerDex")
		if 'mystic' in ctx.message.channel.name.lower() or 'mystic' == modifier:
			lb_filter = leaderboard.mystic
		elif 'valor' in ctx.message.channel.name.lower() or 'valor' == modifier:
			lb_filter = leaderboard.valor
		elif 'instinct' in ctx.message.channel.name.lower() or 'instinct' == modifier:
			lb_filter = leaderboard.instinct
		elif modifier == 'no40':
			lb_filter = leaderboard.get_lower_levels(min=1, max=39)
		elif modifier == 'lowerthan':
			if int(mod2) > 40:
				await self.bot.edit_message(message, new_content="`lowerthan` is a reference to the level. Not the position.")
				return
			lb_filter = leaderboard.get_lower_levels(min=1, max=int(mod2)-1)
		else:
			lb_filter = leaderboard.top_25
		for x in lb_filter[:25]:
				embed.add_field(
					name = '# {x.position} {x.trainer.username} • {x.team.name}'.format(x=x),
					value = "{x.xp:,} • TL{x.level.level} • {date}".format(x=x,date=maya.MayaDT.from_datetime(x.time).slang_date()),
					inline=False
				)
		await self.bot.edit_message(message, new_content=" ", embed=embed)
	
	@commands.command(pass_context=True, no_pm=True)
	async def teamstats(self, ctx, team):
		"""
		Get stats about a team
		"""
		
		message = await self.bot.say("<a:loading:471298325904359434> Thinking...")
		await self.bot.send_typing(ctx.message.channel)
		try:
			team = await self.getTeamByName(team)
		except KeyError:
			await self.bot.edit_message(message, "❌ Please select a team from `valor`, `mystic`, `instinct` or `teamless`. Double check for typos!")
			return
		_server_leaderboard = self.client.get_discord_leaderboard(ctx.message.server.id)
		server_leaderboard = _server_leaderboard.filter_teams((team.id,))
		server_leaderboard.sort(key=lambda x: x.position)
		embed=discord.Embed(title=team.name, timestamp=_server_leaderboard.time, colour=int(team.colour.replace("#", ""), 16))
		embed.set_footer(text="Provided for free by TrainerDex")
		embed.set_thumbnail(url='https://www.trainerdex.co.uk/static/img/{}.png'.format(team.name))
		embed.add_field(name="Name", value=team.name)
		embed.add_field(name="Trainers", value=len(server_leaderboard))
		embed.add_field(name="Total XP", value='{:,}'.format(sum([x.xp for x in server_leaderboard])))
		embed.add_field(name="Mean XP (All)", value='{:,}'.format(int(statistics.mean([x.xp for x in server_leaderboard]))))
		embed.add_field(name="Mean XP (Top 50)", value='{:,}'.format(int(statistics.mean([x.xp for x in server_leaderboard[:50]]))))
		try:
			embed.add_field(name="Mode Level (All)", value=str(statistics.mode([x.level.level for x in server_leaderboard])))
		except statistics.StatisticsError:
			embed.add_field(name="Mode Level (All)", value="null")
		try:
			embed.add_field(name="Mode Level (Top 50)", value=str(statistics.mode([x.level.level for x in server_leaderboard[:50]])))
		except statistics.StatisticsError:
			embed.add_field(name="Mode Level (Top 50)", value="null")
		embed.add_field(name="Man of the Match", value='{x.trainer.username} • {x.xp:,} • TL{x.level.level}'.format(x=server_leaderboard[0]))
		embed.add_field(name="Trainer Showcase", value='{x.trainer.username} • {x.xp:,} • TL{x.level.level}'.format(x=random.choice(server_leaderboard[1:])))
		await self.bot.edit_message(message, new_content=" ", embed=embed)
	
	@commands.command(pass_context=True, no_pm=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def say(self, ctx, *, msg: str):
		"""Simon says...."""
		await self.bot.delete_message(ctx.message)
		await self.bot.say(msg)
	
	async def check_xp_screenshot(self, message):
		"""Checks for attachment and scans it."""
		if message.attachments and ((message.channel.name in ('bot-commands', 'trainerdex',)) or (int(message.channel.id) in (595386799057010709, 531091708814032908, 524622561909407744, 468838256352690186, 418897651619332096, 420185267362725908, 426869945628884992, 431537895711571968, 406537912562483210, 348104003248193537, 439429887191810050, 478564413528473611, 489462023713718272, 516203083718590464, 469522524678389781, 626782347626414090))):
			trainer = await self.get_trainer(discord=message.author.id)
			if not trainer:
				return
			if len(message.attachments) > 1:
				return
			message_1 = await self.bot.send_message(message.channel, "<a:loading:471298325904359434> That's a nice image you have there, let's see...\n⚠️ Please refrain from posting non-profile images in this channel. If your image doesn't scan, please try a new image. Image processing isn't free.")
			await self.bot.send_typing(message.channel)
			ocr = PogoOCR.ProfileSelf('/opt/TrainerDex-RedCog/key.json', image_uri=message.attachments[0]["proxy_url"])
			ocr.get_text()
			if ocr.total_xp: # Need to update TraindeDex.py module in order to update more stats
				await self.bot.edit_message(message_1, new_content="{0}, we're sure your XP is {1:,}. Just processing that now...\n\nIf that doesn't look right, please contact us on Twitter. @TrainerDexApp".format(message.author.mention, ocr.total_xp))
				message_2 = await self.bot.send_message(message.channel, " <a:loading:471298325904359434>")
				await self.bot.send_typing(message.channel)
				await self.__update_xp(message.author, ocr.total_xp, message_2, ocr=True)
			else:
				await self.bot.edit_message(message_1, new_content="❓ Sorry, I couldn't find the XP in this image. Reverting to manual input. Please enter your Total XP now within 120 seconds.\n\nTo improve our service, please send us a report on Twitter including the image that failed. @TrainerDexApp")
				response = await self.bot.wait_for_message(timeout=120, author=message.author)
				if response:
					message_2 = await self.bot.send_message(message.channel, "<a:loading:471298325904359434> Thank you! I'll look at that now.")
					if response.content.strip().replace(',', '').replace('.', '').replace(' ', '').replace('XP', '').isdigit():
						await self.bot.send_typing(message.channel)
						await self.__update_xp(message.author, int(response.content.strip().replace(',', '').replace('.', '').replace(' ', '').replace('XP', '')), message_2)
					else:
						await self.bot.edit_message(message_2, new_content="❌ I couldn't parse the XP from your message. Aborting!")
				else:
					await self.bot.edit_message(message_1, new_content="~~Sorry, I couldn't find the XP in this image. Reverting to manual input. Please enter your Total XP now within 120 seconds.~~\n❌ Timeout! Please try again later.\n\nTo improve our service, please send us a report on Twitter including the image that failed. @TrainerDexApp")

	#Mod-commands
	
	@commands.command(name="addprofile", no_pm=True, pass_context=True, alias="newprofile")
	@checks.mod_or_permissions(assign_roles=True)
	async def addprofile(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''):
		"""Add a user to the Trainer Dex database
		
		Optional arguments:
		spoofer - sets the user as a spoofer
		
		Example: addprofile @JayTurnr#1234 JayTurnr Valor 34 1234567
		"""
		
		message = await self.bot.say('<a:loading:471298325904359434> Processing...')
		await self.bot.send_typing(ctx.message.channel)
		if len(ctx.message.mentions) != 1:
			await self.bot.edit_message(message, "❌ Please check you've tagged a member and only one member!")
			return
		mbr = ctx.message.mentions[0]
		if level != 40:
			xp = trainerdex.level_parser(level=level).total_xp + xp
		try:
			team = await self.getTeamByName(team)
		except KeyError:
			await self.bot.edit_message(message, "❌ Please select a team from `valor`, `mystic`, `instinct` or `teamless`. Double check for typos!")
			return
		if opt.title() == 'Spoofer':
			await self._addProfile(message, mbr, name, xp, team, has_cheated=True, currently_cheats=True)
		else:
			await self._addProfile(message, mbr, name, xp, team)
		try:
			embed = await self.profileCard(ctx.message, name)
			await self.bot.edit_message(message, new_content='✅ Success', embed=embed)
		except LookupError as e:
			await self.bot.edit_message(message, '❌ `Error: '+str(e)+'`')
	
	@commands.command(pass_context=True, no_pm=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def approve(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''):
		"""
		Add a user to the Trainer Dex database and set the correct role on Discord
		
		Roles, renaming and registering a user
		
		Example: approve @JayTurnr#1234 JayTurnr Valor 34 1234567 minor
		"""
		
		message = await self.bot.say('<a:loading:471298325904359434> (1/2) Setting Discord nickname and roles...')
		await self.bot.send_typing(ctx.message.channel)
		
		if not (3 <= len(name) <= 15):
			await self.bot.edit_message(message, "❌ Error: Username must be between 3-13 letters long. Please copy it down exactly as it is in game. Failure to do so can result in data corruption.")
			return
		
		xp = trainerdex.level_parser(level=level).total_xp + xp
		try:
			team = await self.getTeamByName(team)
		except KeyError:
			await self.bot.edit_message(message, "❌ Please select a team from `valor`, `mystic`, `instinct` or `teamless`. Double check for typos!")
			return
		if len(ctx.message.mentions) != 1:
			await self.bot.edit_message(message, "❌ Please check you've tagged a member and only one member!")
			return
		mbr = ctx.message.mentions[0]
		try:
			await self.bot.change_nickname(mbr, name)
		except discord.errors.Forbidden:
			name_changed = False
			await self.bot.edit_message(message, "❓ I don't have permission to change nicknames. Continue anyway? (120s)")
			await self.bot.add_reaction(message, EMOJI_POSITIVE)
			await self.bot.add_reaction(message, EMOJI_NEGATIVE)
			reaction = await self.bot.wait_for_reaction(timeout=120, user=ctx.message.author, emoji=[EMOJI_POSITIVE, EMOJI_NEGATIVE], message=message)
			await self.bot.remove_reaction(message, EMOJI_POSITIVE, self.bot.user)
			await self.bot.remove_reaction(message, EMOJI_NEGATIVE, self.bot.user)
			if reaction.reaction.emoji == EMOJI_POSITIVE:
				message = await self.bot.send_message(message.channel, "<a:loading:471298325904359434> (1/2) Setting roles...")
				await self.bot.remove_reaction(message, EMOJI_POSITIVE, ctx.message.author)
				await self.bot.send_typing(message.channel)
			elif reaction.reaction.emoji == EMOJI_NEGATIVE or reaction.reaction.emoji == None:
				await self.bot.edit_message(message, "❌ I don't have permission to change nicknames. Aborted!")
				await self.bot.remove_reaction(message, EMOJI_POSITIVE, ctx.message.author)
				return
		else:
			name_changed = True
		
		SERVER_ROLES_ADD = {
			'319811219093716993': '341546728467464193', # PoGo! Thanet # Trainer
			'364313717720219651': '366514738118787073', # TrainerDex # Trainer
			'248518377843326976': '408029141158330369', # Pokémon GO Bexley # ✅ Verified
			'406076657695195136': '436982006048489485', # Richmond Raiders # Verified
			'408721816044175360': '426871358429986831', # I-127 # ??
			'478562841130172432': '478564901431017482', # Valor Vampires # Vampire
			'531034671849406495': '531090131226984469', # PVP TW # Verified
			'595377804611420161': '595378228680589322', #Ladres, #Membre
			'511195299545481218': '600369303178706945', #HB&W # Trainer
			'459727475119882272': '626748070494863360', # Hastings # EXP Leaderboard Users
		}
		SERVER_ROLES_REMOVE = {
			'347122839704567818': '427920162981806080', # Novi Pokemon Go # Welcome!
			'408721816044175360': '451096783729459212', # I-127 #Unverified
		}
		
		DEFAULT_ROLE = discord.utils.find(lambda x: x.name == 'TrainerDex User', ctx.message.server.roles)
		
		roles_to_add = []
		roles_to_remove = []
		
		roles_to_add.append(discord.utils.find(lambda x: team.name.upper() in x.name.upper(), ctx.message.server.roles))
		
		try:
			roles_to_add.append(discord.utils.find(lambda x: x.id == SERVER_ROLES_ADD[ctx.message.server.id], ctx.message.server.roles))
		except KeyError:
			roles_to_add.append(DEFAULT_ROLE)
		
		try:
			roles_to_remove.append(discord.utils.find(lambda x: x.id == SERVER_ROLES_REMOVE[ctx.message.server.id], ctx.message.server.roles))
		except KeyError:
			pass
		
		try:
			await self.bot.add_roles(mbr, *list(filter(None.__ne__, roles_to_add)))
			await asyncio.sleep(2.5)
			await self.bot.remove_roles(mbr, *list(filter(None.__ne__, roles_to_remove)))
		except discord.errors.Forbidden:
			roles_added = False
			await self.bot.edit_message(message, "❓ I don't have permission to set roles. Continue anyway?")
			await self.bot.add_reaction(message, EMOJI_POSITIVE)
			await self.bot.add_reaction(message, EMOJI_NEGATIVE)
			reaction = await self.bot.wait_for_reaction(timeout=120, user=ctx.message.author, emoji=[EMOJI_POSITIVE, EMOJI_NEGATIVE], message=message)
			await self.bot.remove_reaction(message, EMOJI_POSITIVE, self.bot.user)
			await self.bot.remove_reaction(message, EMOJI_NEGATIVE, self.bot.user)
			if reaction.reaction.emoji == EMOJI_POSITIVE:
				message = await self.bot.send_message(message.channel, "<a:loading:471298325904359434> (1/2) Just finishing up...")
				await self.bot.remove_reaction(message, EMOJI_POSITIVE, ctx.message.author)
				await self.bot.send_typing(message.channel)
			elif reaction.reaction.emoji == EMOJI_NEGATIVE or reaction.reaction.emoji == None:
				await self.bot.edit_message(message, "❌ I don't have permission to set roles. Aborted!")
				await self.bot.remove_reaction(message, EMOJI_POSITIVE, ctx.message.author)
				return
		else:
			roles_added = True
		
		step_1_message = "✅ {} has been approved!"
		if name_changed == False and roles_added == False:
			step_1_message += "\n❌ Nickname and Roles remain unchanged."
		elif name_changed == False and roles_added == True:
			step_1_message += " Roles set.\n❌ Nickname unchanged."
		elif name_changed == True and roles_added == False:
			step_1_message += " Nickname set.\n❌ Roles unchanged."
		elif name_changed == True and roles_added == True:
			step_1_message += " Nickname & Roles set."
		await self.bot.edit_message(message, step_1_message.format(name))
		message = await self.bot.say('<a:loading:471298325904359434> (2/2) Introducing user to database')
		await self.bot.send_typing(ctx.message.channel)
		if opt.title() == 'Spoofer':
			trainer = await self._addProfile(message, mbr, name, xp, team, has_cheated=True, currently_cheats=True)
		else:
			trainer = await self._addProfile(message, mbr, name, xp, team)
		try:
			embed = await self.profileCard(ctx.message, name)
			await self.bot.edit_message(message, new_content='✅ Successfully added {} as {}'.format(mbr.mention, trainer.username), embed=embed)
		except LookupError as e:
			await self.bot.edit_message(message, '❌ `Error: '+str(e)+'`')
	
	@commands.group(pass_context=True)
	@checks.is_owner()
	async def tdset(self, ctx):
		"""Settings for TrainerDex cog"""
		
		if ctx.invoked_subcommand is None:
			await self.bot.send_cmd_help(ctx)
	
	@tdset.command(pass_context=True)
	@checks.is_owner()
	async def message(self, ctx, *, msg: str):
		message = await self.bot.say('<a:loading:471298325904359434> Processing...')
		await self.bot.send_typing(ctx.message.channel)
		settings = dataIO.load_json(settings_file)
		if msg == "none":
			settings['message'] = None
		else:
			settings['message'] = msg
		dataIO.save_json(settings_file, settings)
		if settings['message']:
			await self.bot.edit_message(message, '✅ Message set to:\n{}'.format(settings['message']))
		else:
			await self.bot.edit_message(message, '✅ Message reset')
	
	@tdset.command(pass_context=True)
	@checks.is_owner()
	async def api(self, ctx, token: str):
		"""Sets the TrainerDex API token - owner only"""
		
		message = await self.bot.say('<a:loading:471298325904359434> Processing...')
		await self.bot.send_typing(ctx.message.channel)
		settings = dataIO.load_json(settings_file)
		if token:
			settings['token'] = token
			dataIO.save_json(settings_file, settings)
			await self.bot.edit_message(message, '✅ API token set - please restart cog')

def check_folders():
	if not os.path.exists("data/trainerdex"):
		print("Creating data/trainerdex folder...")
		os.makedirs("data/trainerdex")

def check_file():
	f = 'data/trainerdex/settings.json'
	data = {}
	data['token'] = ''
	if not dataIO.is_valid_json(f):
		print("Creating default token.json...")
		dataIO.save_json(f, data)

def setup(bot):
	check_folders()
	check_file()
	cog = TrainerDex(bot)
	bot.add_cog(cog)
	bot.add_listener(cog.check_xp_screenshot, 'on_message')

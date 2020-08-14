# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Calendar Versioning](https://calver.org/) `YYYY.0W`.

## [Unreleased]

## [2020.32.0] - 2020-08-07 [YANKED]
### Added
- New Client library
- GDPR settings
- Bot now DMs user on join!

### Changed
- Fixed a bug on generating progress if no data old enough found
- Added 3 more stats to profile_ocr
- Most requests are now async! I'm now awaiting a cup of tea

### [2020.32.1] - 2020-08-07 [YANKED]
#### Changed
- Fixed a bug on outputting data on new users

### [2020.32.2] - 2020-08-07 [YANKED]
#### Changed
- Fixed a bug on sending DMs from a server with no additional_message set

### [2020.32.3] - 2020-08-07
#### Security Fix
- Updated to `Red-DiscordBot==3.3.11`

## [2020.31.0] - 2020-07-31 [YANKED]
### Added
- Start of `quickstart` commands
- Added `tdx.converters.NicknameConverter`
- Basic leaderboard command

### Changed
- Moved translations to a submodule for Crowdin support
- Merged `[p]progress` and `[p]profile lookup` commands
- Converted `get_trainer` to a `discord.commands.Converter` known as `tdx.converters.TrainerConverter`
- Hardened `tdx.converters.TeamConverter` and changed the interface of the return
- Fixed DivideByZero bug (#11)
- BaseCard it's descendants are now async - call `await ProfileCard(**kwargs)` instead of `await ProfileCard(**kwargs).build_card(**kwargs)`
- Fixed `[p]profile create` loop lock issue (#12)
- Handled errors when we're unable to edit a `discord.Member`

### [2020.31.1] - 2020-07-31 [YANKED]
#### Changed
- Fixed a bug on formatting role names on `[p]approve`

### [2020.31.2] - 2020-07-31 [YANKED]
#### Changed
- ~~Fixed a bug where roles weren't changed as `add_roles` wasn't awaited~~

### [2020.31.3] - 2020-07-31
#### Changed
- Fixed a bug where roles weren't changed as `add_roles` wasn't awaited

## [2020.30.0] - 2020-07-25
### Added
- Profile lookup command
 - `[p]profile lookup [mention]`
- Profile creation command
 - `[p]profile create [mention] (nickname) (team) (total_xp)`
- Add [PogoOCR](https://github.com/TrainerDex/PogoOCR) engine for scanning for Total XP
- Progress command
 - `[p]progress (mention)`
- Settings commands

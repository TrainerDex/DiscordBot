# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Calendar Versioning](https://calver.org/) `YYYY.0W`.

## [Unreleased]

## [2020.33.0] - 2020-08-14
### Added
- Added a Level object to Client (756302f732899284dda700414fccaecfca8f5004)
- Server leaderboards (756302f732899284dda700414fccaecfca8f5004, 52ac9d1d7108523eb2caeb33fb3814a040840b6a)
- Leaderboard positions in trainer output (52ac9d1d7108523eb2caeb33fb3814a040840b6a)
- Emoji on trainer output (52ac9d1d7108523eb2caeb33fb3814a040840b6a)
- Admin commands to change footer or notice on demand (2f5ede6b18423cc106e296e1972a96047f4dc41e, 2f5ede6b18423cc106e296e1972a96047f4dc41e)

### Changed
- Made proper use of relative imports. This has fixed a weird import issue that sometimes happen when reloading the cog (756302f732899284dda700414fccaecfca8f5004)
- Changed the user-agent (756302f732899284dda700414fccaecfca8f5004)
- Client objects are now hashable and support the == operator (756302f732899284dda700414fccaecfca8f5004, 52ac9d1d7108523eb2caeb33fb3814a040840b6a)
- Filtering a leaderboard now filters in place. (756302f732899284dda700414fccaecfca8f5004)
- Some commands are now Case Insensitive (e5d4d9a480525cb4ff89b73ab9d44e94547434ac, 3c8084a70b864cf82c59cae26e7b047f8fac7d44)
- Various bug fixes (63df44a033625035dae5d1c47bc167438504f492, a9f23b2bc60464cd023ef9a4ab362c65095b80a3, 63173356afee7e61dceb47cbb2596d4770046339, 50ad59bd342b9f9e60c0163f18e6634209eb5a74)

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

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
- New Client library (f9c4453eba52ea011175e90b0ab4072a9d467359, 74f78695dfb23b44a96307453571ac9fb409e3da, 14d6b9ca5baa64878f4511192b3698294e3fca06, d3c4a1bfbac360a04d4a04a581d74a2c41bd1663)
- GDPR settings (dc49e6553a43287c53ec69aa1a9a46a2fee6a9a1, 428eb709a5d93f1513194bf5aedc7b71106d9fb1, d785a995c72b22f11b2c13647af60b51ee83a32e)
- Bot now DMs user on join! (d785a995c72b22f11b2c13647af60b51ee83a32e)

### Changed
- Fixed a bug on generating progress if no data old enough found (ab257d1b7e5e2fe03579ca8a35e49167743d2e6a)
- Added 3 more stats to profile_ocr (aca8ca6f7c286deed8bfe0921314ea5026294015)
- Various bug fixes (e2d9a9231e2eb866a59811ad5987300f24d2b29f, 2ac79c9fcc251149a21898fe669aed931f0d69f4)

### [2020.32.1] - 2020-08-07 [YANKED]
#### Changed
- Fixed a bug on outputting data on new users (11171f18cddec93d273b3a18ade8db9c17eb9d0a)

### [2020.32.2] - 2020-08-07 [YANKED]
#### Changed
- Fixed a bug on sending DMs from a server with no additional_message set (d8732aff5cc4823c4423801b8c982686285bb8cb)

### [2020.32.3] - 2020-08-07
#### Security Fix
- Updated to `Red-DiscordBot==3.3.11` (3446144f3b64d52e9a8cb2454f6faa91e2625ea4)

## [2020.31.0] - 2020-07-31 [YANKED]
### Added
- Start of `quickstart` commands (76fed68d9d4e054dc64ce7867e06c3fa01effe66)
- Added `tdx.converters.NicknameConverter` (b7cfeeff5571c7e19ed05a68a221d086b1b73b97)
- Basic leaderboard command (6c7a754b2bbdb4a33ce189227c2ba5bc2d197766, 68b073e6852bcc7458bc11fdbaca666e14b63cd5)
- Show bot version in presence (484cbd1060122e7035854d8dcfcd15d05c84702a)

### Changed
- Moved translations to a sub-module for Crowdin support (369c240aebdb0954120c774b45f0c62f56a52485, eec62e09885caec0b400d200fce95cf71980d006, 7e2538d567f0b150e9bc2bbbba38ccb57a62ada5, bf18a0aaa5fcdbbd53e0b047499af2c3e4528d1d, a092b3aafccb12d1800e86b785b7d36f25a9bf6e)
- Merged `[p]progress` and `[p]profile lookup` commands (e9ec6d34c64c3b1ff2c2733b18bfd8fee854c717)
- Converted `get_trainer` to a `discord.commands.Converter` known as `tdx.converters.TrainerConverter` (2d661ca38db4e2c7e501ab06e43e2b87a1e68305, bccc0db761dc9ba44dcee04993ba2362f0c6bf55)
- Hardened `tdx.converters.TeamConverter` and changed the interface of the return (aa21a6b101edc6412537d7237b04847fc6b90a3f)
- Fixed DivideByZero bug (#11, 923f5ced3264d7848ebdff50a971106e0767f108)
- BaseCard it's descendants are now async - call `await ProfileCard(**kwargs)` instead of `await ProfileCard(**kwargs).build_card(**kwargs)` (923f5ced3264d7848ebdff50a971106e0767f108)
- Fixed `[p]profile create` loop lock issue (#12)
- Handled errors when we're unable to edit a `discord.Member`
- Various bug fixes (8eeb7d40681b8b91c718fec273910a3e25c4b8db, 5722c5529277b0b01b475a8112077274f064909f, 55d3652b37359fc11662c10b96d3d3a6bc7752d0, 68ffc11140fdf36a3bcc32b42057c359c79a4242, 2146eb43a4411ae42e3f91637099235fb6ff569c, 3f13f94b2e82f19c22cdf835dc52fa35d9eaac8a, 5b9eb6e98b92e9af3492a3fc48f3898482467f7e, 2aecebfb5046d533525f1c1fdb9b43aa7d4781cb, 50b3d1b9e9bd7667b3f34128d24fb21c0b6c90a7, 382c0dd33769b600cf1fd5950c481fca4930fbd6, 5aac5b45e6c84cc706eae22f9b4f846e79e64aff, 2f4866fbbdf417f5152ec07386f102d3e4db5137, fed36a9d0de13e7905b4d10bdaf0e25c0c7599b7)

### [2020.31.1] - 2020-07-31 [YANKED]
#### Changed
- Fixed a bug on formatting role names on `[p]approve`

### Meta
- Changed code style to Black w/ Type Hinting (cd24c59597a50587870fa7bf5079a39a3bab5b7e, c2d185fcdd5b754502cbcece30887bea191bc5d2, 744da9163093530f33d0ce69208bd607acf68bb8)

### [2020.31.3] - 2020-07-31
#### Changed
- Fixed a bug where roles weren't changed as `add_roles` wasn't awaited (ac25f9191f33ad5926ca969711f528f033316233, ac25f9191f33ad5926ca969711f528f033316233)

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

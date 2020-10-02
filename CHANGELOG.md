# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [CalVer](https://calver.org/) `YYYY.0W.patch`.

## [Unreleased]

## [2020.40.2] - 2020-10-02
### Dependencies
- Bump [https://github.com/TrainerDex/PogoOCR](PogoOCR) to [https://github.com/TrainerDex/PogoOCR/compare/0.3.2...0.3.4](0.3.4)

## [2020.40.0] - 2020-10-02
### Added
- Added command to add trainer code

### Changed
- Better calculation for gains (#44)
- Refactored Command layout (#51)
- Better pre-flight checks for OCR (#52)

## [2020.38.0] - 2020-09-19
### Added
- Capture Total, PokéStops Visited and Travel KM added to Leaderboards

## [2020.37.1] - 2020-09-13
### Fixed
- Fixed message deletions
- Renamed a couple commands

## [2020.37.0] - 2020-09-11
### Added
- Added Command to debug OCR functions (addeb7a741f8839505d5c410b6f00e0d4bf4f04c)

### Fixed
- Updated to PogoOCR 0.3.2 (20f9c0fc36bd6438141a392891565c1ae99fa922)
- Silently ignore some errors

## [2020.36.1] - 2020-09-04
### Fixed
- Fixed a bug in which two commands shared the same function name (a29319e8fd163f30fc3b4c03f92d7cfab3464148)

## [2020.36.0] - 2020-09-04 [YANKED]
### Changed
- Various bug fixes (23fc68526c20559a32bf0bc7699bbed6b5e3b77c, 48d87d8b439257417ea89072fff69e8a9c9dd9b1)

### i18n
- Add common aliases for commands (b651b4acb41432ba10640d4c3b6ca0aeb66f146d)
- Minor text fixes (fcbaca5a89b2b05e2d8f9efc985ba5db7dfd3bd1, 7c3323df7db300e142666857a43b37c34150ecbe)

### Dev
- Changed how translations are pulled from Crowdin (919048c6e119fce4bfc8f1cc3ea32f1816be433e, 2e58311c4d0fd741991ed2994dae87437ba99451, cc11d86d43705401889d2c9dbbb0b1b4b332b4ea)

## [2020.35.1] - 2020-08-31
### Changed
- Testing [Cog-Creators/Red-DiscordBot#3896](https://github.com/Cog-Creators/Red-DiscordBot/pull/3896)

### Dev
- Changed how translations are stored, no more pesky submodule (22cde76799e52206ef33fcec0c739d94c961ed3c, 2004de048ba31fb5fb62f6e6e989a3cb614f4988)

## [2020.35.0] - 2020-08-28
### Added
- Added End User Data Statement (debb5c42f7fa376b90d77f5860ff9438ee10a2e6, 416acc284a23dbaa57b567f4bce417aef789c2b7)

### Changed
- Alias `guild` to `server` in `[p]leaderboard` command (cf560023d0d87761b99922c10f680994fe396e4b)
- Changes in `[p]leaderboard` output (ccd02e0fd29f82c91b590eeefa25b289b262ac33, aa0f23cf20e1c0c7f15e9fb4f7c587f0830d9fc3)
- Minor fixes (c0bfb7e71fb451d1dff9fc341861936f83b46cac, 0fd1fcb0a831e9bdd6db07e54a544f71842e740c, 2958e3a4f95a13f6add1137ee2871cf7ad450a2d, 95565523e31ad891b5426c33aa93eedf73c8461e, a0a642d9e330682583315058fe8632604b400d6f, 8d432dd1cbf780f5eaf872a3b9d19e81ad49d28d, 116fdd3d3a74de21e64c1adb70667a41ca2a7798, 622df9589857b34316aa2284f0dde48b6d57337c)
- Fixed a bug in interactive input on `[p]approve` / `[p]profile create` (c31ecedfec5814667bd47ccd771074c7e1105a67)

### Dev
- Made use of CompositeMetaClass to spread the cog over mutliple files, for better readability (558ef1618b37b64ce547d72c5017e381dfbffbd3, bb23d4c7490649a7aa8977cc85fe686f3872c8b0, 9c882b3a0c2ed2a1014e4b03936de82232ed1169, 9fc42030c5654349535d21fbe0fa6dceb3bf3db6, #20, 2bd4312c9d2b4638a8c598002cde496eed0f0934)
- Updated to Red 3.4.0 (42901c8521f34454289dbbbb67ba2f979f48779c, #21, dbc1bbfac8a39035ab02906fab6d052b06669466, 8ba8f9378b20cb6a18f41eb96c7426e4cf9bfe18)
- Updated to TrainerDex.py 3.5.0 (9c52b1a5fa8860a15f4255e43a66431134624944)

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

## [2020.32.3] - 2020-08-07
### Security Fix
- Updated to `Red-DiscordBot==3.3.11` (3446144f3b64d52e9a8cb2454f6faa91e2625ea4)

## [2020.32.2] - 2020-08-07 [YANKED]
### Changed
- Fixed a bug on sending DMs from a server with no additional_message set (d8732aff5cc4823c4423801b8c982686285bb8cb)

## [2020.32.1] - 2020-08-07 [YANKED]
### Changed
- Fixed a bug on outputting data on new users (11171f18cddec93d273b3a18ade8db9c17eb9d0a)

## [2020.32.0] - 2020-08-07 [YANKED]
### Added
- New Client library (f9c4453eba52ea011175e90b0ab4072a9d467359, 74f78695dfb23b44a96307453571ac9fb409e3da, 14d6b9ca5baa64878f4511192b3698294e3fca06, d3c4a1bfbac360a04d4a04a581d74a2c41bd1663)
- GDPR settings (dc49e6553a43287c53ec69aa1a9a46a2fee6a9a1, 428eb709a5d93f1513194bf5aedc7b71106d9fb1, d785a995c72b22f11b2c13647af60b51ee83a32e)
- Bot now DMs user on join! (d785a995c72b22f11b2c13647af60b51ee83a32e)

### Changed
- Fixed a bug on generating progress if no data old enough found (ab257d1b7e5e2fe03579ca8a35e49167743d2e6a)
- Added 3 more stats to profile_ocr (aca8ca6f7c286deed8bfe0921314ea5026294015)
- Various bug fixes (e2d9a9231e2eb866a59811ad5987300f24d2b29f, 2ac79c9fcc251149a21898fe669aed931f0d69f4)

## [2020.31.3] - 2020-07-31
### Changed
- Fixed a bug where roles weren't changed as `add_roles` wasn't awaited (ac25f9191f33ad5926ca969711f528f033316233, ac25f9191f33ad5926ca969711f528f033316233)

## [2020.31.1] - 2020-07-31 [YANKED]
### Changed
- Fixed a bug on formatting role names on `[p]approve`

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

### Dev
- Changed code style to Black w/ Type Hinting (cd24c59597a50587870fa7bf5079a39a3bab5b7e, c2d185fcdd5b754502cbcece30887bea191bc5d2, 744da9163093530f33d0ce69208bd607acf68bb8)

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

[Unreleased]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.40.0...HEAD
[2020.48.0]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.38.0...v2020.40.0
[2020.38.0]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.37.1...v2020.38.0
[2020.37.1]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.37.0...v2020.37.1
[2020.37.0]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.36.1...v2020.37.0
[2020.36.1]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.36.0...v2020.36.1
[2020.36.0]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.35.1...v2020.36.0
[2020.35.1]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.35.0...v2020.35.1
[2020.35.0]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.33.0...v2020.35.0
[2020.33.0]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.32.3...v2020.33.0
[2020.32.3]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.32.2...v2020.32.3
[2020.32.2]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.32.1...v2020.32.2
[2020.32.1]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.32.0...v2020.32.1
[2020.32.0]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.31.3...v2020.32.0
[2020.31.3]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.31.2...v2020.31.3
[2020.31.2]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.31.1...v2020.31.2
[2020.31.1]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.31...v2020.31.1
[2020.31.0]: https://github.com/olivierlacan/keep-a-changelog/compare/v2020.30...v2020.31
[2020.30.0]: https://github.com/olivierlacan/keep-a-changelog/releases/tag/v2020.30

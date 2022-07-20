# Getting Started

## Installing the bot on your Discord Server
<!-- To install the bot in your Discord Server, follow this [link](#). -->
This section will be updated when the bot goes public, very soon.

## Configuring the bot
Generally, you will need Manage Server or Admin permissions to use any of the config commands on the bot. These permissions were picked to match the permissions Discord requires to install the bot.

The following commands exist:
- `/server-config mod-roles` - provides functionality to set which roles on your server are considered mods. The bot will consider somebody a mod if they have Manage Server, Admin permissions, or one of the roles in this list.
- `/server-config assign-roles-on-join` - a true (yes) / false (no) toggle to set whether the bot should change a users roles when `/approve` is run against them.
- `/server-config set-nickname-on-join` - a true (yes) / false (no) toggle to set whether the bot should change a users nickname when `/approve` is run against them.

- `/server-config access-roles` - provides functionality to set which roles are added/removed from users when they're granted access to the server via `/approve` if `assign-roles-on-join` is enabled. This takes three params and can be confusing. There are two role lists, a `Grant` list, which is a list of roles the bot will give a user, and a `Revoke` list, which is a list of roles the bot will remove from a user.
  - `action` - options are `Append`, `Unappend` and `View` 
  - `array` - options are `Grant` and `Revoke`
  - `role` - required if `action` is not `View`

- `/server-config mystic-role`, `/server-config valor-role`, and `/server-config instinct-role` - all let you set the respective role in your server for those factions. Will only be given to a user if `assign-roles-on-join` is enabled.

- `/server-config tl40-role` - let you set a role you use to restrict level 40+ players. Currently not used as the levels system is being reworked.

<!-- - `/server-config introduction_note` - this is unused -->

- `/approve` - the command to grant a user access to your server, and creates a TrainerDex profile for them. This takes several params, including team, username and Total XP.
  - Notes on Username: You **must** set this to their In-Game Name. Please ensure `i` is `i`, `L` is `L` etc, although we understand these can get mixed up. When in doubt, ask the user what it is. 
  - Notes on Total XP: This is the users all time Total XP, **not** the XP progress through their current level.  
  [![How to approve a user on TrainerDex, July 2022](http://img.youtube.com/vi/KCxtyukXW7w/0.jpg)](http://www.youtube.com/watch?v=KCxtyukXW7w "How to approve a user on TrainerDex, July 2022")

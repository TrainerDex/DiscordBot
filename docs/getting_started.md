# Getting Started

## Installing the bot on your Discord Server
<!-- To install the bot in your Discord Server, follow this [link](#). -->
This section will be updated when the bot goes public, very soon.

## Configuring the bot

### Setting up the mod roles
First things first, you will want to set which roles the bot should consider a mod. This has two halves to it. The bot, and Discord. First we will configure Discord.

#### Discord Config
 1) Go to the [Integrations](https://user-images.githubusercontent.com/11667059/181601459-d14db6d5-c756-4a47-8448-c34d3d2c988e.png)
tab within your Server Settings.
 2) Scroll down and select the TrainerDex integration. This is where you can control who can see and trigger commands within the Discord UI. 
 3) Select `/approve` and tap the No ❎ option for `@everyone`. Add a role override for the role(s) you assign your mods and slect the green check mark ✔️. ([Example](https://user-images.githubusercontent.com/11667059/181602221-29e17512-4cc8-4019-84bc-599700a97324.png))
 4) Rince and repeat for `/server-config`.

Now we've told Discord to show these commands to the mod roles. By default, it will only show to users with **Administrator** or **Manage Server** permissions otherwise.

#### Bot Config
Unfortunately, Discord has been known to screw up and just show the command to everybody anyway. So I was forced to add in some validation in the actual command. So we're going to have to set that up too:
  - Run the following command: `/server-config mod-roles action: Add role role: x` for each of your mod role(s) ([Example](https://user-images.githubusercontent.com/11667059/181603960-9317fb4b-8688-47fc-8fba-8582171d7c8c.png))
  - If you don't run this command, the bot will most likely ignore calls to priviledged commands (`/approve` and `/server-config`) 

## Command list

The following commands exist:
- `/server-config mod-roles` - Provides functionality to set which roles on your server are considered mods. The bot will consider somebody a mod if they have `Manage Server`, `Administrator` permissions, or one of the roles in this list.
- `/server-config assign-roles-on-join` - A true (yes) / false (no) toggle to set whether the bot should change a users roles when `/approve` is run against them.
- `/server-config set-nickname-on-join` - A true (yes) / false (no) toggle to set whether the bot should change a users nickname when `/approve` is run against them.

- `/server-config access-roles` - Provides functionality to set which roles are added/removed from users when they're granted access to the server via `/approve` if `assign-roles-on-join` is enabled. This takes three parameters and can be confusing. There are two role lists, a `Grant` list, which is a list of roles the bot will give a user, and a `Revoke` list, which is a list of roles the bot will remove from a user.
  - `action` - Options are `Add`, `Remove` and `View` 
  - `array` - Options are `Grant` and `Revoke`
  - `role` - Required if `action` is not `View`

- `/server-config mystic-role`, `/server-config valor-role`, and `/server-config instinct-role` - Set the respective role in your server for those factions. Will only be given to a user if `assign-roles-on-join` is enabled.

- `/server-config tl40-role` - Set a role you use to restrict level 40+ players. Currently not used as the levels system is being reworked.

- `/approve` - the command to grant a user access to your server, and creates a TrainerDex profile for them. This takes several params, including team, username and Total XP.
  - Notes on Username: You **must** set this to their In-Game Trainer Name. Please ensure `i` is `i`, `L` is `L` etc, although we understand these can get mixed up. When in doubt, ask the user what it is. 
  - Notes on Total XP: This is the trainers all time Total XP, **not** the XP progress through their current level.  
  [![How to approve a user on TrainerDex, July 2022](http://img.youtube.com/vi/KCxtyukXW7w/0.jpg)](http://www.youtube.com/watch?v=KCxtyukXW7w "How to approve a user on TrainerDex, July 2022")

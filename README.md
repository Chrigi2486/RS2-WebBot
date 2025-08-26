# RS2-WebBot
A Rising Storm 2 game server management application using Discord slash commands as a front-end. Includes Discord server access restrictions.  
Based on a Quart web framework and a MySQL database.


## Features  
### Application Management
- Show application service information
- Update application while running (eliminates downtime, as functions are decoupled)
- Validate a Discord server for application access
- Upgrade Discord server application access
- Revoke Discord server application access
- File download for maintainence
- File upload for maintainence
- Dump a given config file
- Load a given config file
- Run a given SQL command
- Restart application


### Game Server Management
- List Game servers
- Add Game server
- Remove Game server
- Show live game server information
- Show live game server chat
- Kick player
- Ban player
- Send message to game server chat

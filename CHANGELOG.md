# Changelog
All notable changes to this project will be documented in this file.
###### Note: not all changes may be listed because a lot of times idk what im doing
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## Unreleased Stable (v1.3.4)
### Added
- Version check made own command
### Changed
- Changed how reload command works
- Updated `src/modules/utilities.Logger.log()`
### Removed
- Base module no longer shows on every help command screen

---

## [v1.3-stable] - 2021-04-06
### Added
- Changelogs now change to include minor updates and new builds
### Fixed
- Error relating to the changelog
### Changed
- Logging system updated and now configurable
- Base bot functions now a cog and can be reloaded with the reload command
- `config/extensions.json` moved into `config/config.json`

---

## [v1.2-stable] - 2021-03-30
### Added
- Better help command
- Created `nolog.[sh/bat]`
- Created `items` extension
- Created `admin` extension
- Dev-only `list` command
### Fixed
- `config/secrets.json` wasnt updated after a build number change
### Changed
- Reload command now reloads cogs
- Modules/utilities.Utilities methods changed to decorators to better work with the Discord API
- Debugging and prefix variables moved to `src/modules/utilities.py`
- Safely closes database on exit
- Suggestion messages now send to developers with timestamps
- Moved Extension base class to `src/modules` instead of `src/ext`
- Updated docstrings
- Reassigned logging level values
- Extensions are now completely seperate from the main bot
### Removed
- Twitch chat bot integration
### Various extension updates
- Added transaction history
- `economy`:
  - Fixed `economy.can_pay_amount()`
- `games`:
  - Removed `spawn_airdrop` command
  - Removed temp development code and fixed bug where boost didnt reset after  blackjack finish
  - Blackjack command can now define number of decks, defaults to 4
  - Airdrop now stays claimable until successfully claimed, not until first reaction
- `items`:
  - changed raw db functions to their in-class shorthand
  - `items.get_inventory_from_d_id()` not returning desired value

---

## [v1.1-stable] - 2021-02-14
- ### Added reload command

---

## [v1.0-stable] - 2021-02-06
- ### Added Everything!

[v1.3-stable]: https://github.com/teddybear315/YourLocalChatBot/compare/v1.2.6...v1.3.3
[v1.2-stable]: https://github.com/teddybear315/YourLocalChatBot/compare/v1.1.0...v1.2.6
[v1.1-stable]: https://github.com/teddybear315/YourLocalChatBot/compare/v1.0.0...v1.1.0
[v1.0-stable]: https://github.com/teddybear315/YourLocalChatBot/releases/tag/v1.0.0
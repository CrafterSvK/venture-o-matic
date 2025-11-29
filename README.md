# RPG bez názvu

### Quick doc for developers
YAML is a superior format because you can add comments.
Game is purely declarative and game state is in database.
- `alembic` folder is migration manager folder
- `cogs` commands to play the game
- `data` dataset for the game (items, monsters) (definitions)
- `generated` generated files from schemas
- `schema` validation and generative models for the game to interact with game data
- `locales` localization
- `scripts` development scripts

### Installation
`$ poetry install`
To see typing errors run `$ poetry run mypy .`
To regenerate schemas run `$ poetry run generate-models`
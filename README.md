# Game Theorist (`gmetry`)

Interactive terminal app for learning **probability, statistics, and game theory** through hands-on simulations and visualizations.

Built with [Textual](https://github.com/Textualize/textual).

## Features

- Coin flip simulator (fair + biased coins)
- Monty Hall problem
- Birthday Paradox
- More modules coming soon (Prisoner's Dilemma, Poker, etc.)

## Installation

### From source (recommended while in early development)

```bash
git clone https://github.com/anisches/nash.git
cd nash
pip install -e .
```

Then run:

```bash
gmetry
```

### Using Homebrew (experimental / development)

The formula currently supports **HEAD installs only** (until we cut a real GitHub release + tag):

```bash
# From inside the repo (recommended during development)
brew install --HEAD --formula ./Formula/gametheorist.rb

# After you set up a tap (e.g. anisches/homebrew-gametheorist)
brew tap anisches/gametheorist
brew install --HEAD gametheorist
```

The installed command is `gmetry`.

Stable releases will become available once we publish actual versioned GitHub releases (then the `url` + `sha256` in the formula will be filled in).

## Development

```bash
# Install in editable mode
pip install -e ".[dev]"   # (add dev dependencies later)

# Run directly
python -m gametheorist.app
```

## Build

```bash
pip install build
python -m build
```

## License

MIT

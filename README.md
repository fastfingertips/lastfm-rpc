<div align="center">

# Last.fm Discord Rich Presence (RPC)

[![Build Status](https://github.com/fastfingertips/lastfm-rpc/actions/workflows/build.yml/badge.svg)](https://github.com/fastfingertips/lastfm-rpc/actions/workflows/build.yml)
[![Code Quality](https://github.com/fastfingertips/lastfm-rpc/actions/workflows/quality.yml/badge.svg)](https://github.com/fastfingertips/lastfm-rpc/actions/workflows/quality.yml)
[![GitHub Version](https://img.shields.io/github/v/release/fastfingertips/lastfm-rpc?logo=github&color=blue)](https://github.com/fastfingertips/lastfm-rpc/releases)
[![License](https://img.shields.io/github/license/fastfingertips/lastfm-rpc?logo=github&color=orange)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/fastfingertips/lastfm-rpc?style=social)](https://github.com/fastfingertips/lastfm-rpc/stargazers)

A Discord Rich Presence client for Last.fm that synchronizes listening activity to a Discord profile. Includes a graphical interface for settings and supports multiple languages.

[Usage](#usage) • [Setup](#setup) • [Building](#building-from-source)

---

### Demo
https://github.com/user-attachments/assets/c5bbbdcf-f212-4093-86d7-8bc527cb5eda

</div>

---

### Usage

This project uses [uv](https://astral.sh/uv) for environment management.

1. **Clone the Repository**
   ```bash
   git clone https://github.com/fastfingertips/lastfm-rpc.git
   cd lastfm-rpc
   ```

2. **Run the Application**
   ```bash
   uv run main.py
   ```
   *The application will initialize its environment and prompt for settings if no configuration is found.*

---

### Setup

To use this client, you will need:
- **Last.fm Username**: Your public profile name.
- **Last.fm API Credentials**: You can [create an API account here](https://www.last.fm/api/account/create) or [manage existing ones here](https://www.last.fm/api/accounts).

Configuration is stored locally in `config.yaml`.

---

### Building from Source

To compile a standalone executable for Windows using Nuitka:

1. **Install Development Dependencies**:
   ```bash
   uv sync --dev
   ```

2. **Run the Build Script**:
   ```bash
   uv run python tools/build.py
   ```

---

### License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

### Star History

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=fastfingertips/lastfm-rpc&theme=dark)](https://star-history.com/#fastfingertips/lastfm-rpc&Date)

</div>

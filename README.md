# Last.fm Discord Rich Presence (RPC)

A modern, localized, and lightweight Discord Rich Presence client for Last.fm. Show off what you're listening to with custom statistics and artwork.

### Features
- **Real-time Sync**: Updates your Discord status as soon as you change tracks on Last.fm.
- **Full Localization**: Support for English, Turkish, and Spanish.
- **Dynamic Configuration**: Change settings (Username, API Keys, Language) on the fly without restarting.
- **Smart Tracking**: Displays scrobble counts, artist stats, and "Loved" status.
- **Auto-Update Checker**: Stay notified when a new version is released.
- **Modern Stack**: Managed with `uv` for lightning-fast environment setup.

### Demo
https://github.com/user-attachments/assets/c5bbbdcf-f212-4093-86d7-8bc527cb5eda

---

### Quick Start (Recommended)

This project uses **uv** for the best experience. If you don't have it, install it from [astral.sh/uv](https://astral.sh/uv).

1. **Clone the Repository**
   ```bash
   git clone https://github.com/fastfingertips/lastfm-rpc.git
   cd lastfm-rpc
   ```

2. **Run the Application**
   ```bash
   uv run main.py
   ```
   *The app will automatically create a virtual environment, install dependencies, and prompt you with a Settings GUI if it's your first time.*

---

### Configuration & API Setup

Upon first run, a Modern Settings GUI will appear. You will need:
- **Last.fm API Key/Secret**: [Create them here](https://www.last.fm/api/account/create) or [view existing ones](https://www.last.fm/api/accounts).
- **Last.fm Username**: Your public profile name.

All settings are stored in `config.yaml`.

### Advanced Usage

#### CLI Commands
Since the project uses `uv` entry points, you can also run it as a direct command:
```bash
uv run lastfm-rpc
```

#### Running without UV (Classic way)
If you prefer standard Python:
```bash
pip install .
python main.py
```

### Building from Source (EXE)

This project includes a modern build script using **Nuitka** to compile a standalone executable.

1.  **Install Development Dependencies**:
    ```bash
    uv sync --dev
    ```

2.  **Run the Build Script**:
    ```bash
    python build.py
    ```
    The compiled `.exe` will be located in the `dist/` folder.

### License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

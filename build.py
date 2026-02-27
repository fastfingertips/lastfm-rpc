
import io
import os
import shutil
import subprocess
import sys

# Force utf-8 for Windows console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def build():
    """
    Builds the application into a standalone executable using Nuitka.
    """
    print("=" * 50)
    print("Starting Nuitka build for Last.fm RPC")
    print("=" * 50)

    # 1. Clean previous builds
    output_dir = "dist"
    if os.path.exists(output_dir):
        print("Cleaning old dist directory...")
        shutil.rmtree(output_dir)

    # 2. Prepare paths
    main_script = "main.py"
    icon_path = os.path.join("assets", "last_fm.png")

    # 3. Construct Nuitka command
    version = os.getenv("FILE_VERSION", "0.0.1").lstrip("v")

    # --standalone: All dependencies bundled
    # --onefile: Single executable
    # --windows-console-mode=disable: No CMD window
    # --enable-plugin=tk-inter: Required for the GUI
    # --include-data-dir: Bundle assets and translations
    cmd = [
        "uv",
        "run",
        "python",
        "-m",
        "nuitka",
        "--standalone",
        # "--onefile", # Disabling onefile to avoid memory issues and improve startup speed
        "--enable-plugin=tk-inter",
        "--include-data-dir=assets=assets",
        "--include-data-dir=translations=translations",
        "--windows-console-mode=disable",
        f"--windows-icon-from-ico={icon_path}",
        f"--output-dir={output_dir}",
        "--company-name=FastFingertips",
        "--product-name=Last.fm RPC",
        f"--file-version={version}",
        f"--product-version={version}",
        "--copyright=Copyright (c) 2026 FastFingertips",
        "--assume-yes-for-downloads",  # Auto-download MinGW/Dependency Walker if needed
        main_script,
    ]

    print("\nBuilding with Nuitka...")
    print(f"Executing: {' '.join(cmd)}\n")

    try:
        # We use subprocess.run without catching output to see Nuitka's progress
        subprocess.run(cmd, check=True)
        if os.path.exists("config.yaml"):
            shutil.copy(
                "config.yaml", os.path.join(output_dir, f"{os.path.splitext(main_script)[0]}.dist", "config.yaml")
            )
            print("Copied config.yaml to dist folder")

        print("\nBuild finished successfully!")
        print(f"Location: {os.path.abspath(output_dir)}")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build()

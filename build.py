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
        # Using PowerShell for a more aggressive cleanup to avoid WinError 145/32
        subprocess.run(["powershell", "-Command", f"Remove-Item -Recurse -Force {output_dir}"], check=False)
        if os.path.exists(output_dir):
             shutil.rmtree(output_dir, ignore_errors=True)

    # 2. Prepare paths
    main_script = "main.py"
    app_name = "lastfm-rpc"
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
        f"--output-filename={app_name}",
        f"--output-dir={output_dir}",
        "--company-name=FastFingertips",
        "--product-name=Last.fm RPC",
        f"--file-version={version}",
        f"--product-version={version}",
        "--copyright=Copyright (c) 2026 FastFingertips",
        "--assume-yes-for-downloads",  # Auto-download MinGW/Dependency Walker if needed
        "--include-package=scrapling",  # Ensure the whole scrapling package is included
        "--include-package-data=scrapling", # Include data files for scrapling
        "--include-package-data=browserforge", # Include data files for browserforge (headers/fingerprints)
        "--include-package-data=apify_fingerprint_datapoints", # Include the missing zip/json data files
        "--include-package-data=tld", # Include top-level domain data files
        main_script,
    ]

    print("\nBuilding with Nuitka...")
    print(f"Executing: {' '.join(cmd)}\n")

    try:
        # We use subprocess.run without catching output to see Nuitka's progress
        subprocess.run(cmd, check=True)

        # Nuitka names the dist folder after the script (main.dist), rename to app name
        nuitka_dist = os.path.join(output_dir, f"{os.path.splitext(main_script)[0]}.dist")
        final_dist = os.path.join(output_dir, f"{app_name}.dist")
        if os.path.exists(nuitka_dist) and nuitka_dist != final_dist:
            if os.path.exists(final_dist):
                shutil.rmtree(final_dist)
            os.rename(nuitka_dist, final_dist)
            print(f"Renamed dist folder: {nuitka_dist} -> {final_dist}")

        if os.path.exists("config.yaml"):
            shutil.copy("config.yaml", os.path.join(final_dist, "config.yaml"))
            print("Copied config.yaml to dist folder")

        print("\nBuild finished successfully!")
        print(f"Executable: {os.path.join(final_dist, f'{app_name}.exe')}")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build()

import io
import os
import shutil
import subprocess
import sys

from constants.project import VERSION  # noqa: E402

# Force utf-8 for Windows console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


class AppBuilder:
    """Orchestrates the Nuitka build process for the application."""

    def __init__(self):
        self.app_name = "lastfm-rpc"
        self.main_script = "main.py"
        self.output_dir = "dist"
        self.icon_path = os.path.join("assets", "last_fm.png")
        self.version = VERSION.lstrip("v")

    def clean(self):
        """Cleans previous build artifacts."""
        if not os.path.exists(self.output_dir):
            return

        print(f"Cleaning existing '{self.output_dir}' directory...")
        # PowerShell handles locked files better on Windows
        subprocess.run(
            ["powershell", "-Command", f"Remove-Item -Recurse -Force {self.output_dir}"],
            check=False,
        )
        # Fallback to shutil
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir, ignore_errors=True)

    def get_nuitka_cmd(self) -> list[str]:
        """Constructs the Nuitka build command with all necessary flags."""
        return [
            "uv",
            "run",
            "python",
            "-m",
            "nuitka",
            "--standalone",
            "--enable-plugin=tk-inter",
            "--include-data-dir=assets=assets",
            "--include-data-dir=translations=translations",
            "--windows-console-mode=disable",
            f"--windows-icon-from-ico={self.icon_path}",
            f"--output-filename={self.app_name}",
            f"--output-dir={self.output_dir}",
            "--company-name=FastFingertips",
            "--product-name=Last.fm RPC",
            f"--file-version={self.version}",
            f"--product-version={self.version}",
            "--copyright=Copyright (c) 2026 FastFingertips",
            "--assume-yes-for-downloads",
            # Dependencies requiring explicit data/package inclusion
            "--include-package=scrapling",
            "--include-package-data=scrapling",
            "--include-package-data=browserforge",
            "--include-package-data=apify_fingerprint_datapoints",
            "--include-package-data=tld",
            self.main_script,
        ]

    def post_build(self):
        """Moves and renames files to finalize the distribution."""
        nuitka_dist = os.path.join(self.output_dir, "main.dist")
        final_dist = os.path.join(self.output_dir, f"{self.app_name}.dist")

        # Rename main.dist to more descriptive name
        if os.path.exists(nuitka_dist):
            if os.path.exists(final_dist):
                shutil.rmtree(final_dist)
            os.rename(nuitka_dist, final_dist)
            print(f"Finalized output to: {final_dist}")

        # Copy config.yaml as a default if it exists
        if os.path.exists("config.yaml") and os.path.exists(final_dist):
            shutil.copy("config.yaml", os.path.join(final_dist, "config.yaml"))
            print("Successfully bundled config.yaml")

    def run(self):
        """Executes the full build pipeline."""
        print("=" * 60)
        print(f"BUILDING {self.app_name.upper()} v{VERSION}")
        print("=" * 60)

        self.clean()
        cmd = self.get_nuitka_cmd()

        print("\nExecuting Nuitka build command...")
        try:
            subprocess.run(cmd, check=True)
            self.post_build()
            print("\n" + "!" * 10 + " BUILD SUCCESSFUL " + "!" * 10)
        except subprocess.CalledProcessError as e:
            print(f"\nFATAL: Build failed (exit code {e.returncode})")
            sys.exit(1)


if __name__ == "__main__":
    builder = AppBuilder()
    builder.run()

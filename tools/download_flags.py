import os

from utils.net.http import fetch


def download_flags():
    flag_dir = "assets/flags"
    os.makedirs(flag_dir, exist_ok=True)

    # Mapping our locale to flagcdn codes
    # en-US -> us, tr-TR -> tr, es-ES -> es
    mapping = {"tr-TR": "tr", "en-US": "us", "es-ES": "es"}

    for locale, code in mapping.items():
        url = f"https://flagcdn.com/w80/{code}.png"
        path = os.path.join(flag_dir, f"{locale}.png")

        if not os.path.exists(path):
            print(f"Downloading flag for {locale}...")
            try:
                response = fetch(url, timeout=10)
                if response.status == 200:
                    with open(path, "wb") as f:
                        f.write(response.content)
                else:
                    print(f"Failed to download {locale}: {response.status}")
            except Exception as e:
                print(f"Error downloading {locale}: {e}")


if __name__ == "__main__":
    download_flags()

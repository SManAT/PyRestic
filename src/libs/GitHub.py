import requests
import zipfile
import os
from enum import Enum
from tqdm import tqdm
from typing import Optional


class Platform(Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    DARWIN = "darwin"  # macOS
    BSD = "bsd"


class Architecture(Enum):
    AMD64 = "amd64"
    ARM64 = "arm64"
    ARM = "arm"
    I386 = "386"


class GitHub:

    def __init__(self, repo_owner, repo_name):
        """
        :param repo_owner (str): Owner of the repository
        :param repo_name (str): Name of the repository
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.ReleaseInfo = {}

    def get_latest_release_info(self):
        """
        Get latest release with download URLs for different platforms
        """
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
        headers = {"Accept": "application/vnd.github.v3+json"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            downloads = {}

            # Process assets to get download URLs
            for asset in data["assets"]:
                name = asset["name"]
                download_url = asset["browser_download_url"]
                downloads[name] = download_url

            self.ReleaseInfo = {"version": data["tag_name"], "url": data["html_url"], "published_at": data["published_at"], "downloads": downloads, "release_notes": data["body"]}
            return self.ReleaseInfo

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None

    def get_platform_download(self, platform: Platform, arch: Architecture = Architecture.AMD64) -> str | None:
        """
        Get download URL for specific platform and architecture
        :param platform (Platform): Target platform enum
          :param arch (Architecture): Target architecture enum (default: AMD64)

        Returns:
            str | None: Download URL or None if not found
        """
        if not self.ReleaseInfo or "downloads" not in self.ReleaseInfo:
            return None

        downloads = self.ReleaseInfo["downloads"]

        # Match platform-specific file
        platform_matches = {filename: url for filename, url in downloads.items() if platform.value in filename.lower() and arch.value in filename.lower()}

        return next(iter(platform_matches.values()), None)

    def download_file(self, url: str, output_path: str, display_name: Optional[str] = None) -> bool:
        """
        Download a file from URL with progress bar
        :param url (str): Download URL
        :param output_path (str): Path where to save the file
        :param display_name (str, optional): Name to show in progress bar

        Returns:
            bool: True if download successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

            # Send request with stream enabled
            print(f"\nDownloading from: {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            # Get file size
            total_size = int(response.headers.get("content-length", 0))
            block_size = 1024  # 1 KB

            # Create progress bar
            desc = display_name or os.path.basename(output_path)
            with tqdm(total=total_size, unit="iB", unit_scale=True, unit_divisor=1024, desc=desc, bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
                # Download and write file
                with open(output_path, "wb") as f:
                    for data in response.iter_content(block_size):
                        size = f.write(data)
                        pbar.update(size)

            # Verify download size
            if total_size != 0 and pbar.n != total_size:
                print(f"ERROR: Downloaded size ({pbar.n}) does not match expected size ({total_size})")
                return False

            print(f"\nDownload completed: {output_path}")
            return True

        except requests.exceptions.RequestException as e:
            print(f"\nError downloading file: {e}")
            return False
        except IOError as e:
            print(f"\nError saving file: {e}")
            return False
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            return False

    def unzip_file(self, zip_path: str, extract_path: str, display_name: Optional[str] = None) -> bool:
        """
        Unzip a file with progress bar
        :param zip_path (str): Path to zip file
        :param extract_path (str): Path where to extract files
        :param display_name (str, optional): Name to show in progress bar

        Returns:
            bool: True if extraction successful, False otherwise
        """
        try:
            # Create extract directory if it doesn't exist
            os.makedirs(extract_path, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Get total size for progress bar
                total_size = sum(file.file_size for file in zip_ref.filelist)
                extracted_size = 0

                # Create progress bar
                desc = display_name or os.path.basename(zip_path)
                with tqdm(total=total_size, unit="iB", unit_scale=True, desc=f"Extracting {desc}", bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}") as pbar:
                    # Extract each file
                    for file in zip_ref.filelist:
                        zip_ref.extract(file, extract_path)
                        extracted_size += file.file_size
                        pbar.update(file.file_size)

            print(f"\nExtracted to: {extract_path}")
            return True

        except zipfile.BadZipFile:
            print(f"\nError: File is not a zip file or is corrupted: {zip_path}")
            return False
        except Exception as e:
            print(f"\nError extracting zip: {e}")
            return False


if __name__ == "__main__":
    # Example usage:
    github = GitHub("restic", "restic")
    release_info = github.get_latest_release_info()
    if release_info:
        print(f"Version: {release_info['version']}")
        print(f"URL: {release_info['url']}")
        print(f"Published: {release_info['published_at']}")

    # For Windows
    windows_url = github.get_platform_download(Platform.WINDOWS, Architecture.AMD64)
    print(f"Windows AMD64 URL: {windows_url}")

    # For Linux
    linux_url = github.get_platform_download(Platform.LINUX, Architecture.ARM64)
    print(f"Linux ARM64 URL: {linux_url}")

    filename = os.path.basename(windows_url)

    filename = os.path.basename(windows_url)
    output_path = os.path.normpath(f"C:\\Users\\Stefan\\Desktop\\TestDOWNLOAD\\{filename}")

    if github.download_file(windows_url, output_path):
        print("Download successful!")
    else:
        print("Download failed!")

    zip_path = output_path
    extract_path = os.path.normpath("C:\\Users\\Stefan\\Desktop\\TestDOWNLOAD\\")

    if github.unzip_file(zip_path, extract_path):
        print("Extraction successful!")
    else:
        print("Extraction failed!")

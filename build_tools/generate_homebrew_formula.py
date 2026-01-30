#!/usr/bin/env python3
"""Generate Homebrew formula with correct checksums from GitHub release."""

import json
import subprocess
import sys
from pathlib import Path


def get_release_info(repo: str, version: str) -> dict:
    """Fetch release information from GitHub API."""
    api_url = f"https://api.github.com/repos/{repo}/releases/tags/{version}"

    try:
        result = subprocess.run(
            ["curl", "-s", api_url],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching release info: {e}")
        sys.exit(1)


def get_file_sha256(repo: str, version: str, filename: str) -> str:
    """Get SHA256 checksum from GitHub release."""
    api_url = f"https://api.github.com/repos/{repo}/releases/tags/{version}"

    try:
        result = subprocess.run(
            ["curl", "-s", api_url],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)

        # Look for SHA256SUMS file in release
        for asset in data.get("assets", []):
            if asset["name"] == "SHA256SUMS":
                sha_url = asset["browser_download_url"]
                sha_result = subprocess.run(
                    ["curl", "-s", sha_url],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                # Parse SHA256SUMS file
                for line in sha_result.stdout.split("\n"):
                    parts = line.strip().split()
                    if len(parts) >= 2 and filename in parts[1]:
                        return parts[0]

        print(f"Could not find SHA256 for {filename}")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching checksums: {e}")
        sys.exit(1)


def generate_formula(
    repo: str, version: str, x86_sha: str, arm_sha: str
) -> str:
    """Generate Homebrew formula with proper URLs and checksums."""
    # Clean version (remove 'v' prefix if present)
    clean_version = version.lstrip("v")

    formula = f'''# Homebrew formula for Remind
# Generated for version {clean_version}

class Remind < Formula
  desc "AI-powered CLI reminder and notification engine"
  homepage "https://github.com/{repo}"
  license "MIT"
  version "{clean_version}"

  on_macos do
    on_intel do
      url "https://github.com/{repo}/releases/download/{version}/remind-macos-x86_64"
      sha256 "{x86_sha}"
    end
    on_arm do
      url "https://github.com/{repo}/releases/download/{version}/remind-macos-arm64"
      sha256 "{arm_sha}"
    end
  end

  on_linux do
    url "https://github.com/{repo}/releases/download/{version}/remind-linux-x86_64"
    sha256 "{x86_sha}"
  end

  def install
    bin.install "remind-macos-x86_64" => "remind" if OS.mac? && Hardware::CPU.intel?
    bin.install "remind-macos-arm64" => "remind" if OS.mac? && Hardware::CPU.arm?
    bin.install "remind-linux-x86_64" => "remind" if OS.linux?
  end

  def post_install
    puts "Remind installed successfully!"
    puts "Run 'remind --help' to get started."
  end

  test do
    assert_match(/Usage/, shell_output("{{bin}}/remind --help"))
  end
end
'''
    return formula


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: generate_homebrew_formula.py <repo> <version>")
        print("Example: generate_homebrew_formula.py user/remind v0.1.0")
        sys.exit(1)

    repo = sys.argv[1]
    version = sys.argv[2]

    print(f"Generating Homebrew formula for {repo} {version}...")

    # Get checksums from GitHub release
    x86_sha = get_file_sha256(repo, version, "remind-macos-x86_64")
    arm_sha = get_file_sha256(repo, version, "remind-macos-arm64")

    print(f"x86_64 SHA256: {x86_sha}")
    print(f"arm64  SHA256: {arm_sha}")

    # Generate formula
    formula = generate_formula(repo, version, x86_sha, arm_sha)

    # Write to file
    output_path = Path("build_tools/homebrew_formula.rb")
    output_path.write_text(formula)
    print(f"✓ Formula written to {output_path}")


if __name__ == "__main__":
    main()

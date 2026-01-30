# Homebrew formula for Remind
# Auto-generated during release. Do not edit manually.
# Source: build_tools/generate_homebrew_formula.py

class Remind < Formula
  desc "AI-powered CLI reminder and notification engine"
  homepage "https://github.com/hamzaplojovic/remember"
  license "MIT"
  version "0.1.0"

  on_macos do
    on_intel do
      url "https://github.com/hamzaplojovic/remember/releases/download/v0.1.0/remind-macos-x86_64"
      sha256 "HOMEBREW_BINARY_SHA256_X86_64"
    end
    on_arm do
      url "https://github.com/hamzaplojovic/remember/releases/download/v0.1.0/remind-macos-arm64"
      sha256 "HOMEBREW_BINARY_SHA256_ARM64"
    end
  end

  on_linux do
    url "https://github.com/hamzaplojovic/remember/releases/download/v0.1.0/remind-linux-x86_64"
    sha256 "HOMEBREW_BINARY_SHA256_LINUX_X86_64"
  end

  def install
    if OS.mac? && Hardware::CPU.intel?
      bin.install "remind-macos-x86_64" => "remind"
    elsif OS.mac? && Hardware::CPU.arm?
      bin.install "remind-macos-arm64" => "remind"
    elsif OS.linux?
      bin.install "remind-linux-x86_64" => "remind"
    end
  end

  def post_install
    puts "Remind installed successfully!"
    puts "Run 'remind --help' to get started."
  end

  test do
    assert_match(/Usage/, shell_output("#{bin}/remind --help"))
  end
end

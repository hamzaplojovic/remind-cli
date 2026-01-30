# Homebrew formula for Remind
# Place this in a tap at: homebrew-remind/Formula/remind.rb

class Remind < Formula
  desc "AI-powered CLI reminder and notification engine"
  homepage "https://github.com/yourusername/remind"
  url "https://github.com/yourusername/remind/releases/download/v{VERSION}/remind-macos-x86_64"
  sha256 "{SHA256_CHECKSUM}"
  license "MIT"
  version "{VERSION}"

  def install
    bin.install "remind"
  end

  def post_install
    puts "Remind installed successfully!"
    puts "Run 'remind --help' to get started."
  end

  test do
    system bin/"remind", "--help"
  end
end

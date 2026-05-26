class Gametheorist < Formula
  include Language::Python::Virtualenv

  desc "Interactive TUI for learning probability, statistics & game theory"
  homepage "https://github.com/anisches/nash"
  license "MIT"

  # Stable releases (only works after you actually create a GitHub Release + tag)
  # url "https://github.com/anisches/nash/archive/refs/tags/vX.Y.Z.tar.gz"
  # sha256 "REPLACE_WITH_REAL_SHA256_OF_THE_TARBALL"

  # Development installs (recommended while iterating)
  head "https://github.com/anisches/nash.git", branch: "main"

  depends_on "python@3.12"

  def install
    # Create an isolated venv inside the Homebrew prefix
    venv = virtualenv_create(libexec, "python3.12")

    # Upgrade pip tooling first (helps with numpy wheels etc.)
    venv.pip_install "pip" "setuptools" "wheel"

    # Install the project + all runtime dependencies (textual, numpy, etc.)
    venv.pip_install Pathname.pwd

    # Expose the CLI entry point (defined as "gmetry" in pyproject.toml)
    bin.install_symlink libexec/"bin/gmetry"
  end

  test do
    # The app prints its title/subtitle on startup or --help
    output = shell_output("#{bin}/gmetry --help 2>&1", 0)
    assert_match "Game Theorist", output
  end
end

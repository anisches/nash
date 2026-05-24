class Gametheorist < Formula
  desc "Interactive TUI for probability, statistics & game theory"
  homepage "https://github.com/anisches/nash"
  url "https://github.com/anisches/nash/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "TODO_REPLACE_WITH_REAL_SHA_AFTER_FIRST_RELEASE"
  license "MIT"

  depends_on "python@3.12"

  def install
    venv = virtualenv_create(libexec, "python3.12")
    venv.pip_install_and_link "."
  end

  test do
    system bin/"gmetry", "--help"
  end
end

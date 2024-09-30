{ pkgs ? import <nixpkgs> {} }:

let
  inherit (pkgs) fetchFromGitHub;
  inherit (pkgs.lib) licenses;

  lib = pkgs.lib;

  # Translation Server Package (unchanged)
  translation-server = pkgs.stdenv.mkDerivation rec {
    pname = "translation-server";
    version = "master";

    src = fetchFromGitHub {
      owner = "zotero";
      repo = "translation-server";
      rev = "master";
      sha256 = lib.fakeSha256;  # Replace with the correct hash after building
    };

    nativeBuildInputs = [ pkgs.nodejs ];

    buildPhase = ''
      runHook preBuild
      npm install
      runHook postBuild
    '';

    installPhase = ''
      mkdir -p $out/bin
      cp -r * $out/
      chmod +x $out/translation-server.js
      ln -s $out/translation-server.js $out/bin/translation-server
    '';

    meta = with pkgs.lib; {
      description = "Zotero Translation Server";
      homepage = "https://github.com/zotero/translation-server";
      license = licenses.mit;
      platforms = platforms.unix;
    };
  };

  # Python Script Package with Updated Dependencies
  readwise-to-zotero = pkgs.python3Packages.buildPythonApplication {
    pname = "readwise-to-zotero";
    version = "0.1";

    src = ./.;

    propagatedBuildInputs = with pkgs.python3Packages; [ requests toml ];

    doCheck = false;

    installPhase = ''
      mkdir -p $out/bin
      install -m755 readwise_to_zotero.py $out/bin/readwise_to_zotero.py
    '';

    meta = with pkgs.lib; {
      description = "CLI tool to import Readwise data into Zotero";
      homepage = "https://github.com/yourusername/readwise-to-zotero";
      license = licenses.mit;
      platforms = platforms.unix;
    };
  };

in

# Final Package Combining Both (unchanged)
pkgs.stdenv.mkDerivation {
  name = "readwise-to-zotero-with-translation-server";

  buildInputs = [ translation-server readwise-to-zotero ];

  installPhase = ''
    mkdir -p $out/bin

    # Wrapper script to start the translation server and run the Python script
    cat > $out/bin/readwise-to-zotero <<'EOF'
    #!/usr/bin/env bash

    set -e

    # Start translation server in the background
    translation-server &
    TRANSLATION_SERVER_PID=$!

    # Wait a bit to ensure the server has started
    sleep 5

    # Run the Python script
    readwise_to_zotero.py "$@"

    # Kill the translation server
    kill $TRANSLATION_SERVER_PID
    EOF

    chmod +x $out/bin/readwise-to-zotero
  '';

  meta = with pkgs.lib; {
    description = "CLI tool to import Readwise data into Zotero, includes the translation server";
    homepage = "https://github.com/yourusername/readwise-to-zotero";
    license = licenses.mit;
    platforms = platforms.unix;
  };
}


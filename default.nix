
{ translation-server, pkgs ? import <nixpkgs> {} }:

let
  inherit (pkgs.lib) licenses;

  # Python Script Package (unchanged)
  url-to-bibtex = pkgs.python3Packages.buildPythonApplication {
    pname = "url-to-bibtex";
    version = "0.1.0";

    src = pkgs.lib.cleanSourceWith {
      src = ./.;
      filter = (path: type: true);  # Include all files
    };

    propagatedBuildInputs = with pkgs.python3Packages; [ requests toml ];

    doCheck = false;

    # installPhase = ''
      # mkdir -p $out/bin
      # install -m755 readwise_to_zotero.py $out/bin/readwise-to-zotero
    # '';

    meta = with pkgs.lib; {
      description = "CLI tool to import Readwise data into Zotero";
      homepage = "https://github.com/yourusername/readwise-to-zotero";
      license = licenses.mit;
      platforms = platforms.all;
    };
  };

in

# Final Package Combining Both
pkgs.stdenv.mkDerivation {
  name = "url-to-bibtex";

  # Specify that there is no source
  src = null;

  # Override the unpackPhase to skip it
  unpackPhase = ":";

  buildInputs = [ translation-server url-to-bibtex ];

  installPhase = ''
    mkdir -p $out/bin

    # Wrapper script to start the translation server and run the Python script
    cat > $out/bin/url-to-bibtex <<'EOF'
    #!/usr/bin/env bash

    set -e

    # Start translation server in the background
    ${translation-server}/bin/zotero-translation-server &
    TRANSLATION_SERVER_PID=$!

    # Wait a bit to ensure the server has started
    sleep 5

    # Run the Python script
    ${url-to-bibtex}/bin/url-to-bibtex "$@"

    # Kill the translation server
    kill $TRANSLATION_SERVER_PID
    EOF

    chmod +x $out/bin/url-to-bibtex
  '';

  meta = with pkgs.lib; {
    description = "CLI tool to import Readwise data into Zotero, includes the translation server";
    homepage = "https://github.com/yourusername/readwise-to-zotero";
    license = licenses.mit;
    platforms = platforms.all;
  };
}

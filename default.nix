
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
  };

in pkgs.stdenv.mkDerivation {
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

    # Only print to stderr if the --verbose flag is given.
    verbose=false
    for arg in "$@"; do
      case "$arg" in
        -v|--verbose)
          verbose=true
          ;;
      esac
    done
    if [ "$verbose" = "false" ]; then
      exec 2>/dev/null
    fi

    set -e

    # Start translation server in the background
    export USER_AGENT='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 url-to-bibtex/2.0'
    ${translation-server}/bin/zotero-translation-server >&2 &
    TRANSLATION_SERVER_PID=$!

    # Function to handle cleanup
    cleanup() {
        kill "$TRANSLATION_SERVER_PID" 2>/dev/null
        wait "$TRANSLATION_SERVER_PID" 2>/dev/null
    }

    # Trap EXIT, INT, TERM, and ERR signals to run cleanup
    trap cleanup EXIT INT TERM ERR

    # Wait for the server to be ready.
    is_server_up() {
      # Attempt to connect to the server's port
      ${pkgs.netcat}/bin/nc -z "0.0.0.0" "1969" >/dev/null 2>&1
    }

    tries=0
    until is_server_up; do
      if [ "$tries" -ge 30 ]; then
          echo "maximum tries exceeded, translation server won't respond" >&2
          exit 1
      fi
      sleep 0.5
      tries=$((tries + 1))
    done

    # Run the Python script
    ${url-to-bibtex}/bin/url-to-bibtex "$@"
    EOF

    chmod +x $out/bin/url-to-bibtex
  '';

  meta = {
    description = "A CLI to convert urls to bibtex, powered by Zotero's translation server.";
    homepage = "https://github.com/jjjholscher/url-to-bibtex";
    license = licenses.mit;
    platforms = pkgs.lib.platforms.all;
  };
}

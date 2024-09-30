
{ pkgs ? import <nixpkgs> {} }:

let
  inherit (pkgs) fetchFromGitHub;
  inherit (pkgs.lib) licenses;

  # Node packages
  nodePackages = pkgs.nodePackages;

  # Translation Server Version
  translationServerVersion = "c4f03e78e1c50dc61a2b8e5a452284581d9ad0e3"; # Specific commit for reproducibility

  # Translation Server Package
  translation-server = nodePackages.buildNodePackage rec {
    pname = "translation-server";
    version = translationServerVersion;

    src = fetchFromGitHub {
      owner = "zotero";
      repo = "translation-server";
      rev = translationServerVersion;
      sha256 =  "sha256-w60KHZsrg+0Cm6zd7Z5t+OZy/p+HWvTQokXQEKBXWow="; # Replace with the correct hash
    };

    # Replace SSH URLs with HTTPS in package.json
    postPatch = ''
      substituteInPlace package.json \
        --replace "git+ssh://git@github.com/" "git+https://github.com/"
    '';

    # Fix the shebang line in translation-server.js
    postInstall = ''
      substituteInPlace $out/translation-server.js \
        --replace "#!/usr/bin/env node" "#!${pkgs.nodejs}/bin/node"
    '';

    # Expose the binary
    pkgBin = "translation-server.js";

    meta = with pkgs.lib; {
      description = "Zotero Translation Server";
      homepage = "https://github.com/zotero/translation-server";
      license = licenses.mit;
      platforms = platforms.unix;
    };
  };

  # Python Script Package
  readwise-to-zotero = pkgs.python3Packages.buildPythonApplication {
    pname = "readwise-to-zotero";
    version = "0.1.0";

    src = ./.;

    propagatedBuildInputs = with pkgs.python3Packages; [ requests toml ];

    doCheck = false;

    installPhase = ''
      mkdir -p $out/bin
      install -m755 readwise_to_zotero/main.py $out/bin/readwise-to-zotero
    '';

    meta = with pkgs.lib; {
      description = "CLI tool to import Readwise data into Zotero";
      homepage = "https://github.com/yourusername/readwise-to-zotero";
      license = licenses.mit;
      platforms = platforms.unix;
    };
  };

in

# Final Package Combining Both
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
    readwise-to-zotero "$@"

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

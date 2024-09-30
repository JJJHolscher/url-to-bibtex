{
  description = "Nix flake to set up Zotero Translation Server and provide a CLI tool for importing Readwise data into Zotero";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    translation-server.url = "github:jjjholscher/translation-server";
  };

  outputs = { self, nixpkgs, flake-utils, ... }@inputs:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        translation-server = inputs.translation-server.packages."${pkgs.system}".default;
      in {
        packages.default = pkgs.callPackage ./default.nix { inherit translation-server; };
        apps.default = flake-utils.lib.mkApp {
          drv = self.packages.${system}.default;
          name = "readwise-to-zotero";
        };
      }
    );
}


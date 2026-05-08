{
  description = "Zenodo development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShells.default = pkgs.mkShell {
          name = "zenodo-rdm";

          packages = with pkgs; [
            uv

            nodejs_22
            pnpm
            corepack

            gcc
            gnumake
            pkg-config
            autoconf
            automake
            libtool

            libxcrypt
            libxml2
            libxslt
            xmlsec
            cairo
            openssl
            zlib
            libffi
            readline
            git
          ];

          shellHook = ''
            # Add needed C libraries to path
            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [
              pkgs.libxcrypt
              pkgs.libxml2
              pkgs.libxslt
              pkgs.xmlsec
              pkgs.cairo
              pkgs.openssl
              pkgs.zlib
              pkgs.libffi
              pkgs.readline
              pkgs.stdenv.cc.cc.lib
            ]}''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

            export LIBRARY_PATH="${pkgs.lib.makeLibraryPath [
              pkgs.libxcrypt
              pkgs.libxml2
              pkgs.libxslt
              pkgs.xmlsec
              pkgs.cairo
              pkgs.openssl
              pkgs.zlib
              pkgs.libffi
              pkgs.readline
              pkgs.stdenv.cc.cc.lib
            ]}''${LIBRARY_PATH:+:$LIBRARY_PATH}"

            export C_INCLUDE_PATH="${pkgs.lib.makeSearchPathOutput "dev" "include" [
              pkgs.libxcrypt
              pkgs.libxml2
              pkgs.libxslt
              pkgs.xmlsec
              pkgs.cairo
              pkgs.openssl
              pkgs.zlib
              pkgs.libffi
              pkgs.readline
            ]}''${C_INCLUDE_PATH:+:$C_INCLUDE_PATH}"

            export PKG_CONFIG_PATH="${pkgs.lib.makeSearchPathOutput "dev" "lib/pkgconfig" [
              pkgs.libxcrypt
              pkgs.libxml2
              pkgs.libxslt
              pkgs.xmlsec
              pkgs.cairo
              pkgs.openssl
              pkgs.zlib
              pkgs.libffi
            ]}''${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
          '';
        };
      }
    );
}

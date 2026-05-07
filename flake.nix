{
  description = "dashy -- morning briefing CLI dev environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.python312
            pkgs.uv
            pkgs.ruff
            pkgs.mypy
            pkgs.just
          ];

          shellHook = ''
            echo "dashy dev shell"
            echo "  python: $(python --version)"
            echo "  uv:     $(uv --version)"
            echo
            echo "Run 'uv sync' to install dependencies."
          '';
        };
      }
    );
}

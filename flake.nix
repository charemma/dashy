{
  description = "dashy -- morning briefing CLI development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
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
            echo "dashy dev shell ready"
            echo "Run 'uv sync' to install Python dependencies"
          '';
        };
      }
    );
}

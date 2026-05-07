{
  description = "dashy - Morning briefing CLI";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              python312
              uv
              ruff
              mypy
              just
            ];

            shellHook = ''
              echo "🚀 dashy development environment"
              echo "  Python: $(python --version)"
              echo "  Available commands: uv, ruff, mypy, just"
              echo ""
              echo "Run 'just' to see available tasks"
            '';
          };
        });
    };
}

{
  description = "Click TUI for Timed";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # see https://github.com/nix-community/poetry2nix/tree/master#api for more functions and examples.
        pkgs = nixpkgs.legacyPackages.${system};
        inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication defaultPoetryOverrides;
      in
      { packages = {
          timedctl = mkPoetryApplication {
            projectDir = self;
            python = pkgs.python311;
            # At least libtimed can't be built magically.
            # Using pip for everything is easier anyway :)
            preferWheels = true;
          };
          default = self.packages.${system}.timedctl;
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.timedctl ];
          packages = [ pkgs.poetry ];
        };
      });
}

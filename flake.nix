{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    devenv.url = "github:cachix/devenv";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      nixpkgs,
      flake-parts,
      ...
    }@inputs:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        inputs.devenv.flakeModule
      ];

      systems = nixpkgs.lib.systems.flakeExposed;
      perSystem =
        {
          pkgs,
          ...
        }:
        let
          inherit (inputs) pyproject-nix uv2nix pyproject-build-systems;
          inherit (pkgs) lib callPackage;

          python = pkgs.python310;

          workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
          overlay = workspace.mkPyprojectOverlay {
            sourcePreference = "wheel";
          };

          gopy = callPackage ./nix/gopy.nix { inherit python; };
          maimai-pageparser = callPackage ./nix/pageparser.nix {
            inherit gopy;
            buildPythonPackage = python.pkgs.buildPythonPackage;
          };

          uv-links = pkgs.symlinkJoin {
            name = "uv-links";
            paths = [
              maimai-pageparser.dist
            ];
          };
          pageparserOverlay = final: prev: {
            maimai-pageparser = prev.maimai-pageparser.overrideAttrs (old: {
              buildInputs = (old.buildInputs or [ ]) ++ maimai-pageparser.buildInputs;
              src = maimai-pageparser.dist;
            });
          };

          pythonSet =
            (callPackage pyproject-nix.build.packages {
              inherit python;
            }).overrideScope
              (
                lib.composeManyExtensions [
                  pyproject-build-systems.overlays.default
                  overlay
                  pageparserOverlay
                ]
              );
        in
        {
          _module.args = {
            pkgs = import nixpkgs {
              config.allowUnfree = true;
            };
          };

          packages = {
            inherit gopy maimai-pageparser;

            nonebot-plugin-maimai-updater = pythonSet.nonebot-plugin-maimai-updater.overrideAttrs (old: {
              outputs = [
                "out"
                "dist"
              ];
              postInstall = ''
                mkdir -p $dist
                cp -r dist/* $dist/
              '';
            });
            # nonebot-plugin-maimai-updater = python.pkgs.buildPythonPackage {
            #   inherit (pythonSet.nonebot-plugin-maimai-updater) pname version;

            #   format = "wheel";
            #   src = pythonSet.nonebot-plugin-maimai-updater.override {
            #     pyprojectHook = pythonSet.pyprojectDistHook;
            #   };
            #   preUnpack = "export src=$(echo $src/*.whl)";
            # };
          };

          devenv.shells.default =
            let
              editableOverlay = workspace.mkEditablePyprojectOverlay {
                root = "$REPO_ROOT";
              };
              editablePythonSet = pythonSet.overrideScope (
                pkgs.lib.composeManyExtensions [
                  editableOverlay
                  (final: prev: {
                    nonebot-plugin-maimai-updater = prev.nonebot-plugin-maimai-updater.overrideAttrs (old: {
                      nativeBuildInputs =
                        old.nativeBuildInputs
                        ++ final.resolveBuildSystem {
                          editables = [ ];
                        };
                    });
                  })
                ]
              );
              virtualenv = editablePythonSet.mkVirtualEnv "nonebot-plugin-maimai-updater-dev-env" workspace.deps.all;
            in
            {
              packages = [
                gopy
                virtualenv
                pkgs.uv
              ];
              languages = {
                go.enable = true;
              };

              env = {
                UV_NO_SYNC = "1";
                UV_PYTHON = "${virtualenv}/bin/python";
                UV_PYTHON_DOWNLOADS = "never";
              };

              enterShell = ''
                # Undo dependency propagation by nixpkgs.
                unset PYTHONPATH

                # Get repository root using git. This is expanded at runtime by the editable `.pth` machinery.
                export REPO_ROOT=$(git rev-parse --show-toplevel)

                # Extra dependency
                ln -sfn ${uv-links} .uv-links
                export UV_FIND_LINKS=$(realpath -s .uv-links)
              '';
            };
        };
    };
}

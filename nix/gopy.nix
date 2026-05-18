{
  gotools,
  python,
  lib,
  makeWrapper,
  buildGoModule,
  fetchFromGitHub,
}:
buildGoModule (finalAttrs: {
  pname = "gopy";
  version = "0.4.10-462a29d";

  src = fetchFromGitHub {
    owner = "go-python";
    repo = "gopy";
    rev = "462a29de1a75fbb139d36cd9a86b9418fb4ec4bc";
    hash = "sha256-V63lwckfbHPjFg/weioNPfDtyN/0A/IEFsrAG8JnxjQ=";
  };

  vendorHash = "sha256-J0Xmgk9YGUNkw7q97RgElgAVSZv5HTLDdsPtmaAaXAM=";

  doCheck = false;

  nativeBuildInputs = [ makeWrapper ];
  allowGoReference = true;
  postFixup = ''
    wrapProgram $out/bin/gopy \
      --set PATH $PATH:${
        lib.makeBinPath [
          gotools
          (python.withPackages (
            ps: with ps; [
              pybindgen
              setuptools
              wheel
            ]
          ))
        ]
      }'';
})

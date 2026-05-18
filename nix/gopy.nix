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
    rev = "1d185b810fd5fbcf64e2271bd8331907fd3f30fe";
    hash = "sha256-V63lwckfbHPjFg/weioNPfDtyN/0A/IEFsrAG8JnxjQ=";
  };

  patches = [ ./gopy.patch ];

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

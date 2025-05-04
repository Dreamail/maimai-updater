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
  version = "0.4.10-5f285b8";

  src = fetchFromGitHub {
    owner = "go-python";
    repo = "gopy";
    rev = "5f285b890023153b3a17892ef7f04fe9a654bff2";
    hash = "sha256-agjOzcN+X35A+uw3+RA1m+JbRw0RmtGCJLsBb/KCIS8=";
  };

  vendorHash = "sha256-qdwk6uv+N4CmCMdmdTqmq9K7QihLo9wDb2xbNJ0WWFE=";

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

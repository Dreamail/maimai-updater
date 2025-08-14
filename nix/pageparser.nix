{
  gopy,
  buildGoModule,
  buildPythonPackage,
}:
let
  pname = "maimai-pageparser";
  version = "0.1.1";
  gopy-pkg = buildGoModule (finalAttrs: {
    inherit pname version;

    src = ../maimai-pageparser;

    proxyVendor = true;
    vendorHash = "sha256-74cj0q3MlsbOgW0g0jIpB3dztQ7rLfv1Lmkk6YA4C/0=";

    nativeBuildInputs = [
      gopy
    ];

    buildPhase = ''
      gopy pkg -output=./build -version=${finalAttrs.version} maimai_pageparser
      echo "from .maimai_pageparser import *" > ./build/maimai_pageparser/__init__.py
    '';

    installPhase = ''
      mkdir -p $out
      cp -r build/* $out
    '';

    doCheck = false;
  });
in
buildPythonPackage {
  inherit pname version;
  src = gopy-pkg;
}

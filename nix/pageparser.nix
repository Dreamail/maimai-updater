{
  gopy,
  buildGoModule,
  python
}:
let
  pname = "maimai-pageparser";
  version = "0.1.1";
  gopy-pkg = buildGoModule (finalAttrs: {
    pname = "${pname}-gopy-pkg";
    inherit version;

    src = ../maimai-pageparser;

    proxyVendor = false;
    vendorHash = "sha256-v+WMfnFe38f6WnMk7/IqddOtW01Rfjw8YnKhT7Y0Qyg=";

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

  inherit (python.pkgs) buildPythonPackage setuptools;
in
buildPythonPackage {
  inherit pname version;
  src = gopy-pkg;

  pyproject = true;
  build-system = [ setuptools ];
}

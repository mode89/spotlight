{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    (python3.withPackages (ps: with ps; [
      beautifulsoup4
      requests
      pytest
    ]))
  ];

  shellHook = ''
    export PYTHONPATH=$PWD:$PYTHONPATH
  '';
}

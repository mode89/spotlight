{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    (python3.withPackages (ps: with ps; [
      playwright
      beautifulsoup4
      requests
      pytest
    ]))
  ];

  shellHook = ''
    export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright-driver.browsers}
    export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true
    export PYTHONPATH=$PWD:$PYTHONPATH
  '';
}

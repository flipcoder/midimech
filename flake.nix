{
  description = "Midimech - Isomorphic musical layout engine for LinnStrument and Launchpad X";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      python = pkgs.python312;

      # --- Custom Python packages not in nixpkgs ---

      # rtmidi2: Cython wrapper around RtMidi C++ library.
      # Uses pre-built manylinux wheel + autoPatchelfHook since no sdist is published.
      rtmidi2 = python.pkgs.buildPythonPackage rec {
        pname = "rtmidi2";
        version = "1.4.1";
        format = "wheel";
        src = pkgs.fetchurl {
          url = "https://files.pythonhosted.org/packages/cc/08/e426f1a8dae34acb8a13a0eca47970a78955a0c00395efe89a94ef04ad49/rtmidi2-1.4.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl";
          hash = "sha256:2270b773302806209eb3aec341156ef841e2f5ea7a83f5b242311d0da1df3a76";
        };
        nativeBuildInputs = [ pkgs.autoPatchelfHook ];
        buildInputs = [
          pkgs.alsa-lib
          pkgs.libjack2
          pkgs.stdenv.cc.cc.lib  # libstdc++
        ];
        pythonImportsCheck = [ "rtmidi2" ];
      };

      # launchpad-py: Pure Python Novation Launchpad control suite
      launchpad-py = python.pkgs.buildPythonPackage rec {
        pname = "launchpad-py";
        version = "0.9.1";
        pyproject = true;
        src = python.pkgs.fetchPypi {
          pname = "launchpad_py";
          inherit version;
          hash = "sha256:9c70885a9079d9960a066515f4b83727e7c475543da8ef68786f00a8ef10727c";
        };
        build-system = [ python.pkgs.setuptools ];
        dependencies = [ python.pkgs.pygame-ce ];
        pythonImportsCheck = [ "launchpad_py" ];
        doCheck = false;
      };

      # mido-fix: Fork of mido (MIDI Objects), required by musicpy
      mido-fix = python.pkgs.buildPythonPackage rec {
        pname = "mido-fix";
        version = "1.2.12";
        pyproject = true;
        src = python.pkgs.fetchPypi {
          pname = "mido_fix";
          inherit version;
          hash = "sha256:8ce7ad87f847de36c7dd3048876581113c4d83367d1f392e5a7a9f9562b3374e";
        };
        build-system = [ python.pkgs.setuptools ];
        pythonImportsCheck = [ "mido_fix" ];
        doCheck = false;
      };

      # musicpy: Music programming language / theory library
      # musicpy declares mido-fix + dataclasses as deps; midimech only uses
      # musicpy for chord analysis (not MIDI I/O), so we skip the runtime
      # deps check and provide pygame-ce which musicpy actually imports.
      musicpy = python.pkgs.buildPythonPackage rec {
        pname = "musicpy";
        version = "7.11";
        pyproject = true;
        src = python.pkgs.fetchPypi {
          inherit pname version;
          hash = "sha256:7957971dc1be5b310a83253acd8dd8d3ce803ba47f67d88603904667badde993";
        };
        build-system = [ python.pkgs.setuptools ];
        dependencies = [ python.pkgs.pygame-ce mido-fix ];
        pythonImportsCheck = [ "musicpy" ];
        dontCheckRuntimeDeps = true;
        doCheck = false;
      };

      # --- Python environment with all deps ---

      pythonEnv = python.withPackages (ps: [
        ps.pygame-ce
        ps.pygame-gui
        ps.pyglm
        rtmidi2
        launchpad-py
        musicpy
        ps.pyyaml
        ps.webcolors
      ]);

      runtimeLibs = pkgs.lib.makeLibraryPath [
        pkgs.SDL2
        pkgs.SDL2_image
        pkgs.SDL2_mixer
        pkgs.SDL2_ttf
        pkgs.alsa-lib
        pkgs.libjack2
      ];

    in {
      packages.${system} = {
        midimech = pkgs.stdenv.mkDerivation {
          pname = "midimech";
          version = "0.1.0-chromatic-quantize";
          src = self;

          nativeBuildInputs = [ pkgs.makeWrapper pkgs.pkg-config ];
          buildInputs = [ pythonEnv pkgs.alsa-lib ];

          buildPhase = ''
            # Compile the native MIDI virtual cable (zero-overhead loopMIDI equivalent)
            cc -O2 -Wall $(pkg-config --cflags --libs alsa) \
              midimech-vport.c -o midimech-vport
          '';

          installPhase = ''
            mkdir -p $out/share/midimech $out/bin
            cp -r . $out/share/midimech/

            # Install the native MIDI virtual cable
            install -m755 midimech-vport $out/bin/midimech-vport

            # Main entry point: starts virtual MIDI cable, then midimech
            cat > $out/bin/midimech <<LAUNCHER
            #!/bin/sh
            cleanup() { kill "\$VPORT_PID" 2>/dev/null; wait "\$VPORT_PID" 2>/dev/null; }
            trap cleanup EXIT INT TERM
            $out/bin/midimech-vport &
            VPORT_PID=\$!
            sleep 0.3
            exec ${pythonEnv}/bin/python3 $out/share/midimech/midimech.py "\$@"
            LAUNCHER
            chmod +x $out/bin/midimech
            patchShebangs $out/bin/midimech

            # Wrap to include runtime libraries
            wrapProgram $out/bin/midimech \
              --prefix LD_LIBRARY_PATH : "${runtimeLibs}"

            # Desktop entry for application launchers
            mkdir -p $out/share/applications $out/share/icons/hicolor/256x256/apps
            cp $out/share/midimech/icon.png $out/share/icons/hicolor/256x256/apps/midimech.png
            cat > $out/share/applications/midimech.desktop <<DESKTOP
            [Desktop Entry]
            Name=Midimech
            Comment=Isomorphic musical layout engine for LinnStrument and Launchpad X
            Exec=$out/bin/midimech
            Icon=midimech
            Terminal=false
            Type=Application
            Categories=Audio;Music;Midi;
            DESKTOP

            # Direct entry (no virtual cable, for users who manage MIDI themselves)
            makeWrapper ${pythonEnv}/bin/python3 $out/bin/midimech-raw \
              --add-flags "$out/share/midimech/midimech.py" \
              --prefix LD_LIBRARY_PATH : "${runtimeLibs}"
          '';

          meta = with pkgs.lib; {
            description = "Isomorphic musical layout engine for LinnStrument and Launchpad X";
            homepage = "https://github.com/zitongcharliedeng/midimech";
            license = licenses.mit;
            platforms = [ "x86_64-linux" ];
          };
        };

        default = self.packages.${system}.midimech;
      };

      apps.${system}.default = {
        type = "app";
        program = "${self.packages.${system}.midimech}/bin/midimech";
      };

      # NixOS module: installs midimech system-wide with clean MIDI setup.
      #
      # Usage in your NixOS config:
      #   imports = [ midimech-flake.nixosModules.default ];
      #   services.midimech.enable = true;
      nixosModules.default = { config, lib, ... }:
        let
          cfg = config.services.midimech;
        in {
          options.services.midimech = {
            enable = lib.mkEnableOption "midimech isomorphic MIDI layout engine";
          };

          config = lib.mkIf cfg.enable {
            environment.systemPackages = [
              self.packages.${system}.midimech
            ];

            # Remove the "Midi Through" phantom port that clutters MIDI device lists.
            # midimech provides its own virtual MIDI cable; snd_seq_dummy is redundant.
            boot.blacklistedKernelModules = [ "snd_seq_dummy" ];
          };
        };
    };
}

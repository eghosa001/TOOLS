#!/usr/bin/env bash
# One-time MIT-licensed SPH simulator + surface reconstruction toolchain.
# Run on the render worker, NEVER on the user's phone. Reuse the installed
# binaries/cache across fluid shots; do not download again for each video.
set -euo pipefail

ROOT="${ASMR_PHYSICS_TOOLS_DIR:-$HOME/.cache/satisfying-studio/physics}"
mkdir -p "$ROOT/bin"
SRC="$ROOT/SPlisHSPlasH"
if ! command -v git >/dev/null || ! command -v cmake >/dev/null || ! command -v cargo >/dev/null; then
  echo "BLOCKED: git, CMake and Rust cargo are required for free SPH tools." >&2
  exit 2
fi
if [ ! -d "$SRC/.git" ]; then
  git clone --depth 1 --recurse-submodules https://github.com/InteractiveComputerGraphics/SPlisHSPlasH.git "$SRC"
else
  echo "Reusing installed SPlisHSPlasH source and pinned local checkout."
fi
if [ ! -x "$SRC/bin/SPHSimulator" ]; then
  cmake -S "$SRC" -B "$SRC/build" -DCMAKE_BUILD_TYPE=Release -DUSE_PYTHON_BINDINGS=OFF
  cmake --build "$SRC/build" --target SPHSimulator --parallel "${ASMR_BUILD_JOBS:-4}"
fi
test -x "$SRC/bin/SPHSimulator" || { echo 'BLOCKED: native SPHSimulator did not build' >&2; exit 2; }
if [ ! -x "$ROOT/bin/splashsurf" ]; then
  cargo install --locked splashsurf --root "$ROOT"
fi
test -x "$ROOT/bin/splashsurf" || { echo 'BLOCKED: splashsurf did not install' >&2; exit 2; }
cat > "$ROOT/bin/asmr_sphsimulator" <<EOF
#!/usr/bin/env bash
exec "$SRC/bin/SPHSimulator" "\$@"
EOF
chmod +x "$ROOT/bin/asmr_sphsimulator"
"$SRC/bin/SPHSimulator" --version
"$ROOT/bin/splashsurf" --version
printf 'ASMR_PHYSICS_ROOT=%s\nSPH_SOURCE_SHA=%s\n' "$ROOT" "$(git -C "$SRC" rev-parse HEAD)" > "$ROOT/install_provenance.txt"
echo "READY: use --simulator $ROOT/bin/asmr_sphsimulator --surface $ROOT/bin/splashsurf"

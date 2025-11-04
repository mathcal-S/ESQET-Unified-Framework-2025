#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "🚀 Termux Qiskit Installation Starting..."
PREFIX=${PREFIX:-/data/data/com.termux/files/usr}
export LD_LIBRARY_PATH="$PREFIX/lib"
export CFLAGS="-I$PREFIX/include"
export CXXFLAGS="-I$PREFIX/include"
export LDFLAGS="-L$PREFIX/lib -lomp -lopenblas -landroid-shmem"
export CPPFLAGS="-I$PREFIX/include"
export PATH="$PREFIX/bin:$PATH"

echo "📦 Updating and installing prerequisites..."
pkg update -y && pkg upgrade -y
pkg install -y clang cmake make git libandroid-shmem libllvm libopenblas libomp python numpy scipy

echo "🐍 Upgrading pip & setuptools..."
pip install -U pip setuptools wheel

echo "🔮 Installing Qiskit core modules..."
pip install -U "qiskit==1.1.2" "qiskit-algorithms==0.3.0" "qiskit-ibm-runtime==0.23.0" "qiskit-quantum-info" python-dotenv

echo "⚙️ Attempting qiskit-aer build from source..."
cd ~
pip uninstall -y qiskit-aer || true
git clone --depth 1 https://github.com/Qiskit/qiskit-aer.git
cd qiskit-aer

# Build and install Aer using Termux-friendly flags
mkdir -p build && cd build
cmake .. \
  -DCMAKE_C_COMPILER=clang \
  -DCMAKE_CXX_COMPILER=clang++ \
  -DCMAKE_CXX_FLAGS="-std=c++17 -fPIC -fopenmp -I$PREFIX/include" \
  -DCMAKE_EXE_LINKER_FLAGS="-L$PREFIX/lib -lomp -lopenblas -landroid-shmem -ldl -lc" \
  -DBLA_VENDOR=OpenBLAS \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=$PREFIX

make -j$(nproc) || make
make install

echo "✅ Aer build completed."
cd ../..
rm -rf qiskit-aer

echo "🧪 Verifying Aer installation..."
python - <<'PYCODE'
try:
    import qiskit_aer
    from qiskit_aer import AerSimulator
    print("🎉 Qiskit Aer successfully installed and importable!")
except Exception as e:
    print("⚠️ Aer not importable:", e)
    print("🧩 VQE will use NumPy fallback instead.")
PYCODE

echo "✅ All done!"
echo "Next step: Run your ESQET VQE script: python omni_kernel_qpu_run.py"

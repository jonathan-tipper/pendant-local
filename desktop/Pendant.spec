# Build with .venv/bin/python -m PyInstaller desktop/Pendant.spec --noconfirm
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files, copy_metadata

root = Path(SPECPATH).parent
binaries, datas, hidden = [], [], []
# Include the engines, never model weights. Native libraries need their hooks.
for package in ('faster_whisper', 'sherpa_onnx', 'bleak'):
    d, b, h = collect_all(package)
    datas += d; binaries += b; hidden += h
for package in ('uvicorn', 'pendant_api', 'pendant_client'):
    from PyInstaller.utils.hooks import collect_submodules
    hidden += collect_submodules(package)
datas += collect_data_files('pendant_api')
for distribution in ('faster-whisper', 'sherpa-onnx', 'huggingface-hub', 'tokenizers', 'ctranslate2', 'onnxruntime'):
    datas += copy_metadata(distribution)
datas += [(str(root / 'LICENSES'), 'licences/upstream'), (str(root / 'LICENSE'), 'licences/project'), (str(root / 'THIRD-PARTY-NOTICES.md'), 'licences')]

analysis = Analysis([str(root / 'desktop/service.py')], pathex=[str(root / 'src')], binaries=binaries, datas=datas,
                    hiddenimports=hidden, excludes=['pytest', 'tkinter', 'torch', 'tensorflow', 'IPython', 'matplotlib'])
pyz = PYZ(analysis.pure)
exe = EXE(pyz, analysis.scripts, [], exclude_binaries=True, name='pendant-service', console=True,
          target_arch='arm64', strip=False, upx=False)
collection = COLLECT(exe, analysis.binaries, analysis.datas, name='pendant-service', strip=False, upx=False)
app = BUNDLE(collection, name='Pendant.app', bundle_identifier='local.pendant.workspace',
             info_plist={'NSBluetoothAlwaysUsageDescription': 'Pendant connects to your Limitless Pendant to read device status and download recordings.',
                         'NSBluetoothPeripheralUsageDescription': 'Pendant uses Bluetooth to communicate with your Limitless Pendant.'})

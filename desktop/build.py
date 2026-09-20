"""Build a local Apple Silicon .app, without user data or model downloads."""
from pathlib import Path
import importlib.metadata
import os
import plistlib
import shutil
import subprocess
import sys
import sysconfig

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from pendant_api import __version__


def run(*args):
    subprocess.run(args, cwd=ROOT, check=True, env={**os.environ, 'PYINSTALLER_CONFIG_DIR': str(ROOT / 'build/pyinstaller-cache')})


def main():
    if sys.platform != 'darwin':
        raise SystemExit('Build this app on an Apple Silicon Mac with Xcode command line tools.')
    run(sys.executable, '-m', 'PyInstaller', 'desktop/Pendant.spec', '--noconfirm')
    app = ROOT / 'dist/Pendant.app'
    contents = app / 'Contents'
    run('swiftc', '-module-cache-path', str(ROOT / 'build/swift-cache'), '-swift-version', '5', '-O', '-target', 'arm64-apple-macosx13.0', 'desktop/Pendant.swift', '-o', str(contents / 'MacOS/Pendant'))
    run('swiftc', '-module-cache-path', str(ROOT / 'build/swift-cache'), 'desktop/Icon.swift', '-o', str(ROOT / 'build/pendant-icon'))
    run(str(ROOT / 'build/pendant-icon'), str(ROOT / 'build/Pendant.iconset'))
    run('iconutil', '-c', 'icns', str(ROOT / 'build/Pendant.iconset'), '-o', str(contents / 'Resources/Pendant.icns'))
    info = contents / 'Info.plist'
    data = plistlib.loads(info.read_bytes())
    data.update(CFBundleExecutable='Pendant', CFBundleName='Pendant', CFBundleDisplayName='Pendant',
                CFBundleShortVersionString=__version__, CFBundleVersion=__version__, LSMinimumSystemVersion='13.0',
                NSHighResolutionCapable=True, NSAppTransportSecurity={'NSAllowsLocalNetworking': True},
                CFBundleIconFile='Pendant.icns', NSPrincipalClass='NSApplication', NSHumanReadableCopyright='Independent Pendant Local Workspace. See bundled licences.')
    info.write_bytes(plistlib.dumps(data))
    licences = contents / 'Resources/licences/dependencies'
    licences.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(sysconfig.get_path('stdlib')) / 'LICENSE.txt', licences.parent / 'Python-LICENSE.txt')
    # Retain distribution licence/notice files, with provenance and exact versions.
    inventory = []
    for distribution in importlib.metadata.distributions():
        included = []
        for path in distribution.files or []:
            if any(part.lower() in ('licenses', 'licences') for part in path.parts) or path.name.lower().startswith(('license', 'licence', 'copying', 'notice')):
                source = Path(distribution.locate_file(path))
                if source.is_file():
                    destination = licences / distribution.metadata['Name'] / Path(*[p for p in path.parts if p not in ('..', '/')])
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
                    included.append(str(path))
        inventory.append(f"{distribution.metadata['Name']}=={distribution.version}")
    (licences.parent / 'build-environment.txt').write_text('\n'.join(sorted(inventory)) + '\n')
    run('codesign', '--force', '--deep', '--sign', '-', str(app))
    run('codesign', '--verify', '--deep', '--strict', str(app))
    print(f'Built {app}. No recordings, credentials or downloaded speech/speaker models were bundled.')


if __name__ == '__main__':
    main()

"""Exercise an extracted wheel outside the checkout, using only temporary data."""
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CHECK = r"""
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[1])
from fastapi.testclient import TestClient
import pendant_api
from pendant_api.app import create_app
from pendant_api.config import Settings
assert Path(pendant_api.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve())
data = Path(sys.argv[2])
data.mkdir()
app = create_app(Settings(data, 'synthetic-wheel-smoke-token-only'))
with TestClient(app) as client:
    assert client.get('/health').json()['version'] == pendant_api.__version__
    assert client.get('/v1/recordings').status_code == 401
    assert client.get('/v1/recordings', headers={'Authorization': 'Bearer synthetic-wheel-smoke-token-only'}).status_code == 200
    for path in ['/ui/', '/ui/app.js', '/ui/style.css', '/docs', '/openapi.json', '/assets/swagger-ui-bundle.js', '/assets/swagger-ui.css']:
        assert client.get(path).status_code == 200, path
print('Wheel import, startup, authentication, library and bundled assets passed.')
"""


def main() -> None:
    wheels = sorted((ROOT / 'dist').glob('*.whl'))
    if len(wheels) != 1:
        raise SystemExit('Build exactly one wheel in dist/ before running this check.')
    with tempfile.TemporaryDirectory(prefix='pendant-wheel-') as directory:
        base = Path(directory)
        package = base / 'package'
        with zipfile.ZipFile(wheels[0]) as archive:
            names = archive.namelist()
            assert any(n.endswith('/licenses/LICENSE') for n in names)
            assert any(n.endswith('/licenses/LICENSES/pendant-cli-MIT.txt') for n in names)
            assert any(n.endswith('/licenses/THIRD-PARTY-NOTICES.md') for n in names)
            # The archive is our own local build; reject traversal before extraction.
            assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names)
            archive.extractall(package)
        subprocess.run([sys.executable, '-I', '-c', CHECK, str(package), str(base / 'data')],
                       cwd=base, check=True)


if __name__ == '__main__':
    main()

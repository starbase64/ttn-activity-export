"""Build the download lock from resolved wheels and authoritative PyPI hashes."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request
import zipfile


def wheel_entry(path):
    with zipfile.ZipFile(path) as archive:
        metadata=next(n for n in archive.namelist() if n.endswith('.dist-info/METADATA'))
        fields=BytesParser().parsebytes(archive.read(metadata))
    name,version=fields['Name'],fields['Version']
    url='https://pypi.org/pypi/'+urllib.parse.quote(name)+'/'+urllib.parse.quote(version)+'/json'
    with urllib.request.urlopen(url,timeout=30) as response:data=json.load(response)
    asset=next(a for a in data['urls'] if a['filename']==path.name)
    checksum=hashlib.sha256(path.read_bytes()).hexdigest()
    if asset['digests']['sha256']!=checksum:raise ValueError('PyPI wheel checksum mismatch: '+path.name)
    if urllib.parse.urlsplit(asset['url']).hostname!='files.pythonhosted.org':raise ValueError('Unexpected wheel host')
    return dict(name=name,version=version,filename=path.name,url=asset['url'],sha256=checksum,size=path.stat().st_size)


def generate(wheels):
    with ThreadPoolExecutor(max_workers=4) as pool:entries=list(pool.map(wheel_entry,sorted(Path(wheels).glob('*.whl'))))
    if not entries:raise ValueError('No wheels')
    return {'schema':1,'platform':'win_amd64','python':{
        'version':'3.13.16','url':'https://www.python.org/ftp/python/3.13.16/python-3.13.16-embed-amd64.zip',
        'sha256':'97dae5274cc54867065e8d5a3226e48c35017ed332a0fdb0e27d5b5821961297'},'wheels':entries}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('wheels');args=parser.parse_args()
    output=Path(__file__).with_name('windows-dependencies.lock.json')
    output.write_text(json.dumps(generate(args.wheels),indent=2)+'\n',encoding='utf-8')
    print(output)

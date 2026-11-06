"""Re-hash the outputs manifest of every collected version whose manifest came from a local copy, from the
Kaggle output zip itself (so the manifest lists exactly the files in the zip on Kaggle and Hugging Face).
Run from the folder that holds RAW (raw/<slug>/v<N>/meta.json)."""
import csv, hashlib, io, json, re, sys, time, zipfile
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.kernels.types.kernels_api_service import ApiDownloadKernelOutputZipRequest
KEEP = re.compile(r"^(summary\.txt|benchmark\.json|submission\.json|submission\.parquet|score\.json)$")
api=KaggleApi(); api.authenticate()
with api.build_kaggle_client() as k:
    c=k.kernels.kernels_api_client
    for mf in sorted(Path('raw').glob('*/v*/meta.json')):
        meta=json.loads(mf.read_text())
        if 'hashed from local copy' not in str(meta['files'].get('outputs','')): continue
        d=mf.parent; zr=ApiDownloadKernelOutputZipRequest(); zr.kernel_session_id=int(meta['script_version_id'])
        for w in (0,10,30,60,120):
            time.sleep(w)
            try: data=c.download_kernel_output_zip(zr).content; break
            except Exception as e: err=e
        z=zipfile.ZipFile(io.BytesIO(data)); n=0
        with open(d/'outputs-manifest.csv','w',newline='') as f:
            wr=csv.writer(f); wr.writerow(['path','bytes','sha256'])
            for i in z.infolist():
                if i.is_dir(): continue
                wr.writerow([i.filename,i.file_size,hashlib.sha256(z.read(i)).hexdigest()]); n+=1
                if KEEP.match(i.filename): (d/'keep').mkdir(exist_ok=True); (d/'keep'/i.filename).write_bytes(z.read(i))
        meta['files']['outputs']=f"hashed from the Kaggle output zip ({meta['files']['outputs'].replace('hashed from local copy','earlier: local copy')})"
        meta['output_files']=n; mf.write_text(json.dumps(meta,indent=1))
        print(d, n, flush=True)

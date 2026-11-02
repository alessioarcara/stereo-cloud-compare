# Stereo Cloud Compare

Compare stereo models in the browser.

![Demo](docs/demo.gif)

```bash
git clone git@github.com:alessioarcara/stereo-cloud-compare.git && cd stereo-cloud-compare
python3 scripts/setup.py   # ONNX Runtime Web + FoundationStereo (--no-models to skip)
python3 serve.py           # http://localhost:8000
```

Drop left/right images (and `*_stereo_calibration.yaml`), drop `.onnx` models, run.

Pick a reference model in the table. Other models are compared to it on the disparity
map: 
- **EPE** is the mean error in pixels,
- **Bad-1** / **Bad-3** the share of pixels off by more than 1 / 3 px.

FoundationStereo is the only model in the catalogue; it is fetched by `setup.py`, not stored here.

WebGPU needs chrome and `localhost` or `python3 serve.py --https`; otherwise CPU WASM.

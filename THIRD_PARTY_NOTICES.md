# Third-party notices and acknowledgements

## 1. signBridge reference repository

Repository: https://github.com/Uni-Creator/signBridge  
Creator: Uni-Creator  
License: MIT License  
Usage: inspected as a technical reference for the system architecture and real-time ISL recognition workflow. SanketSetu uses a compatible ISLF binary frame envelope and references the external model integration approach. This delivery is a separate PWA implementation and does not copy the upstream mobile application source files wholesale.

The upstream repository reports a Swin3D-S-based model, a 76-word dataset and benchmark metrics in its README. Those are statements by the upstream project; they have not been independently reproduced for SanketSetu and must not be represented as SanketSetu's results.

The upstream MIT notice is preserved below:

```text
MIT License

Copyright (c) 2024 Uni-Creator

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 2. Indian Sign Language learning resources

- Indian Sign Language Research and Training Centre (ISLRTC): https://islrtc.nic.in/
- Official ISL dictionary: https://divyangjan.depwd.gov.in/islrtc/
- DIKSHA: https://diksha.gov.in/
- ISLRTC YouTube: https://www.youtube.com/@islrtcnewdelhi4069

The app links to these resources. It does not redistribute their videos or claim ownership of ISLRTC content. ISLRTC notes that dictionary data may be used for teaching/research/technology development subject to acknowledgement and non-profiteering conditions; check the current terms directly before copying or redistributing data. See https://islrtc.nic.in/faq/.

## 3. Model and dataset

The upstream repository references a model hosted at https://huggingface.co/Creator-090/isl-swin3d-model and a Kaggle ISL words dataset. SanketSetu does not bundle model weights or redistribute the dataset. Any later download or deployment must follow the current model and dataset terms, retain attribution and document its version.

## 4. Runtime libraries

SanketSetu depends on FastAPI, Uvicorn, python-dotenv, Requests, Pillow and Pydantic. Optional frame-landmark functionality uses MediaPipe, NumPy and OpenCV. Each dependency retains its own licence; refer to the installed package metadata and official project licence before redistributing binaries.

## 5. Original project code

Original SanketSetu code and documentation in this separate project are licensed under the MIT License in `LICENSE`, subject to all third-party notices above.

FROM nvidia/cuda:12.8.1-runtime-ubuntu24.04
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8
ENV PIP_BREAK_SYSTEM_PACKAGES=1
RUN apt-get update && \
    apt-get install -y \
        git \
        git-lfs \
        ca-certificates \
        python3 \
        python3-pip \
      && \
    git lfs install --skip-smudge && \
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128 && \
    pip install git+https://github.com/huggingface/diffusers@main && \
    pip install \
        accelerate \
        huggingface_hub \
        protobuf \
        safetensors \
        sentencepiece \
        transformers \
        pillow \
        numpy \
        boto3 \
      && \
    pip cache purge && \
    mkdir /FLUX2-klein-4B /opt/artifact && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /FLUX2-klein-4B

RUN GIT_LFS_SKIP_SMUDGE=1 git clone https://ユーザー名に置換:アクセストークンに置換@huggingface.co/black-forest-labs/FLUX.2-klein-4B .

RUN git lfs pull --include="model_index.json"  && \
    git lfs pull --include="scheduler/*" && \
    rm -rf .git/lfs/objects && sync
RUN git lfs pull --include="text_encoder/model-00001-of-00002.safetensors" && \
    rm -rf .git/lfs/objects && sync
RUN git lfs pull --include="text_encoder/model-00002-of-00002.safetensors" && \
    git lfs pull --include="text_encoder/*.json" && \
    rm -rf .git/lfs/objects && sync
RUN git lfs pull --include="tokenizer/*" && \
    git lfs pull --include="transformer/*" && \
    git lfs pull --include="vae/*" && \
    rm -rf .git

COPY runner.py /FLUX2-klein-4B/
COPY docker-entrypoint*.sh /
RUN chmod +x /docker-entrypoint*.sh /

WORKDIR /
CMD ["/bin/bash", "/docker-entrypoint.sh"]
FROM nvidia/cuda:12.8.1-runtime-ubuntu24.04
LABEL jp.sakuracr.t-shirotani-airepo.version="1.0.0"
LABEL jp.sakuracr.t-shirotani-airepo.release-date="2026-02-12"
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# 依存関係のインストール。diffusersは最新Pipeline対応版をソースからインストール。
RUN apt-get update && \
    apt-get install -y \
        git \
        git-lfs \
        ca-certificates \
        python3 \
        python3-pip && \
    rm -rf /var/lib/apt/lists/* && \
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128 && \
    pip install git+https://github.com/huggingface/diffusers@main && \
    pip install \
        accelerate \
        boto3 \
        huggingface_hub \
        numpy \
        pillow \
        protobuf \
        safetensors \
        sentencepiece \
        transformers \
      && \
    pip cache purge && \
    mkdir /FLUX2-klein-4B /opt/artifact

# モデルの取得。push時のタイムアウト対策で、必要最低限のファイルをレイヤー分割し取得。
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

# 実行用スクリプト等の配置
COPY runner*.py /FLUX2-klein-4B/
COPY docker-entrypoint*.sh /
RUN chmod +x /docker-entrypoint*.sh

ENTRYPOINT [ "/docker-entrypoint.sh" ]
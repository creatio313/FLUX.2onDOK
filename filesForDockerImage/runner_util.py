import boto3
from botocore.config import Config
from datetime import datetime
from pathlib import Path

def genObjectStorageClient(endpoint: str, token: str, secret: str) -> any:
    """S3互換APIクライアントを生成する。"""
    # S3クライアント作成用の設定
    object_storage_config = Config(
        # 互換性担保のため、設定を入れる。
        # https://cloud.sakura.ad.jp/news/2025/02/04/objectstorage_defectversion/?_gl=1%2Awg387d%2A_gcl_aw%2AR0NMLjE3NjgxMjIxMDEuQ2owS0NRaUFzWTNMQmhDd0FSSXNBRjZPNlhqR2V1aDdSejdHZkVUbS1SbTVKSkRBeE9CUGoxQ2FxUjlRQ3BSbFN5Vlo2M1h4UTlXVnVBa2FBdkxyRUFMd193Y0I.%2A_gcl_au%2ANzM1ODg0ODM0LjE3NjA5NjM5MDYuMTQzMDE2MzgwNS4xNzY4MDU2MzU3LjE3NjgwNjE2NTg.
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    )

    # キー情報を元にS3APIクライアントを作成
    object_storage_client = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=token,
        aws_secret_access_key=secret,
        config=object_storage_config,
    )

    return object_storage_client

def genOutputPath(input_file_path: str, suffix: str | None = None) -> str:
    """
    要件:
      1) input_file_path と suffix を受け取る
      2) 拡張子を .png に変更する
      3) suffix がある場合は拡張子の前に '_{suffix}' を付与、ない場合はそのまま（拡張子変更のみ）
    """
    base_path = Path(input_file_path)

    # ベースのファイル名（拡張子抜き）
    base_file_stem = base_path.stem

    # suffix があれば '_suffix' を付ける。
    if suffix:
        output_file_stem = f"{base_file_stem}_{suffix}"
    else:
        output_file_stem = base_file_stem

    # 新しいファイル名を組み立て、同じディレクトリに配置
    output_name = f"{output_file_stem}.png"
    output_path = base_path.with_name(output_name)

    return str(output_path)

def saveImageLocally(image, local_path: Path) -> None:
    """画像をローカルに保存する"""
    local_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(local_path)
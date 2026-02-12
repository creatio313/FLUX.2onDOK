import runner_util
import argparse
from diffusers import DiffusionPipeline
from io import BytesIO
import json
import logging
from PIL import Image
from pathlib import Path
import random
import sys
import torch

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

# 環境変数からパラメータを取得
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument(
    '--output',
    default='/opt/artifact',
    help='出力先ディレクトリを指定します。',
)
arg_parser.add_argument(
    '--prompt', 
    default='[["input.jpg", "make it a fantasy landscape", "v1"]]', 
    help='[["filepath", "prompt", "suffix"], ...] 形式のJSON文字列を指定します。'
)
arg_parser.add_argument(
    '--steps',
    type=int,
    default=4,
    help='サンプリングステップ数を指定します。',
)
arg_parser.add_argument(
    '--width',
    type=int,
    default=1024,
    help='出力画像の幅を指定します。',
)
arg_parser.add_argument(
    '--height',
    type=int,
    default=1024,
    help='出力画像の高さを指定します。',
)
arg_parser.add_argument('--objst-input-bucket', help='オブジェクトストレージのバケットを指定します。')
arg_parser.add_argument('--objst-output-bucket', help='オブジェクトストレージのバケットを指定します。')
arg_parser.add_argument('--objst-endpoint', help='S3互換エンドポイントのURLを指定します。')
arg_parser.add_argument('--objst-secret', help='オブジェクトストレージのシークレットアクセスキーを指定します。')
arg_parser.add_argument('--objst-token', help='オブジェクトストレージのアクセスキーIDを指定します。')
args = arg_parser.parse_args()

# S3互換APIクライアントの生成
if args.objst_token and args.objst_secret and args.objst_endpoint:
    object_storage_client = runner_util.genObjectStorageClient(endpoint=args.objst_endpoint,
                            token=args.objst_token,
                            secret=args.objst_secret)
else:
    logging.error('S3互換APIクライアントの情報が不足しています。処理を中断します。')
    sys.exit(1)

# FLUX.2 klein 4Bの動作準備
logging.info('FLUX.2-klein-4Bを読み込みます。')
pipe = DiffusionPipeline.from_pretrained(
    "/FLUX2-klein-4B",
    torch_dtype=torch.bfloat16,
).to('cuda')
logging.info('FLUX.2-klein-4Bを読み込みました。')

logging.info('主処理開始')
tasks = json.loads(args.prompt)
for task in tasks:
    # タスク情報を取得し、ファイルパス・プロンプトが存在しない場合はスキップ
    input_file_path, prompt, suffix = task
    if not input_file_path or not prompt:
        logging.warning(f'必須パラメータが不足しているため、処理をスキップしました。: {task}')
        continue

    logging.info(f'画像編集タスク開始 -> ファイルパス: {input_file_path}, プロンプト: {prompt}, 接尾辞: {suffix}')

    # 画像取得
    try:
        logging.info(f'入力画像を取得します。バケット: {args.objst_input_bucket}, ファイルパス: {input_file_path}')
        response = object_storage_client.get_object(
            Bucket=args.objst_input_bucket,
            Key=input_file_path)
        image_data = response["Body"].read()
        init_image = Image.open(BytesIO(image_data)).convert("RGB")
        response["Body"].close()
    except Exception as e:
        logging.error(f'入力画像の取得に失敗しました。: {e}')
        continue
    else:
        logging.info('入力画像の取得に成功しました。')

    # 乱数シードを生成し、生成器にセット
    generator = torch.Generator(device="cuda").manual_seed(random.getrandbits(32))
    
    logging.info('画像編集を実行します。')
    # 出力命令。guidance_scaleは推奨値3.5に固定しているが、変更も可能。
    images = pipe(
        prompt=prompt,
        image=init_image,
        generator=generator,
        num_inference_steps=args.steps,
        guidance_scale=3.5,
        output_type='pil',
        height=args.height,
        width=args.width,
    ).images
    logging.info('画像編集が完了しました。')

    #出力結果を出力フォルダに保存
    output_path = runner_util.genOutputPath(input_file_path, suffix)
    local_output_path = Path(args.output) / output_path

    logging.info(f'画像をローカルに保存します。パス: {local_output_path}')
    runner_util.saveImageLocally(images[0], local_output_path)
    logging.info('画像をローカルに保存しました。')

    # オブジェクトストレージにアップロード
    logging.info(f'画像をオブジェクトストレージにアップロードします。バケット: {args.objst_output_bucket}, ファイルパス: {output_path}')
    object_storage_client.upload_file(
        Filename=str(local_output_path),
        Bucket=args.objst_output_bucket,
        Key=output_path,
        ExtraArgs={
            "ContentType": "image/png",
        },
    )
    logging.info(f'画像をオブジェクトストレージにアップロードしました。バケット: {args.objst_output_bucket}, ファイルパス: {output_path}')

logging.info('主処理終了')
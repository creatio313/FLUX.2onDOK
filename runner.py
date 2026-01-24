from diffusers import DiffusionPipeline
import argparse
import boto3
from botocore.config import Config
import glob
import json
import os
import random
import torch

# 環境変数からパラメータを取得
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('--batch', type=int, default=1, help='生成回数を指定します。')
arg_parser.add_argument('--num', type=int, default=1, help='生成枚数を指定します。')
arg_parser.add_argument(
    '--output',
    default='/opt/artifact',
    help='出力先ディレクトリを指定します。',
)
arg_parser.add_argument(
    '--prompt', 
    default='[["flux2-", "An astronaut riding a green horse"]]', 
    help='[["prefix", "prompt"], ...] 形式のJSON文字列を指定します。'
)
arg_parser.add_argument(
    '--steps',
    type=int,
    default=20,
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
arg_parser.add_argument('--s3-bucket', help='S3のバケットを指定します。')
arg_parser.add_argument('--s3-endpoint', help='S3互換エンドポイントのURLを指定します。')
arg_parser.add_argument('--s3-secret', help='S3のシークレットアクセスキーを指定します。')
arg_parser.add_argument('--s3-token', help='S3のアクセスキーIDを指定します。')

args = arg_parser.parse_args()

tasks = json.loads(args.prompt)

# FLUX 2 devの動作準備
print('Start loading FLUX2-klein-4B')
pipe = DiffusionPipeline.from_pretrained(
    "/FLUX2-klein-4B",
    torch_dtype=torch.float16,
)

pipe.to('cuda')

print('Start generating images')
# 画像生成処理
# seedを乱数生成
base_seed = random.randint(0, 2**32 - 1)
for task in tasks:
    file_counter = 0
    task_prefix, task_prompt = task["value"]
    print(f'Current Task -> Prefix: {task_prefix}, Prompt: {task_prompt}')
    for batch_iteration in range(int(args.batch)):
        current_seed = (base_seed + batch_iteration) % (2**32)
        generator = torch.Generator(device="cuda").manual_seed(current_seed)
        # 出力命令
        images = pipe(
            prompt=task_prompt,
            generator=generator,
            height=int(args.height),
            num_images_per_prompt=int(args.num),
            num_inference_steps=int(args.steps),
            guidance_scale=3.5,
            output_type='pil',
            width=int(args.width),
        ).images

        #出力結果を出力フォルダに保存
        for i in range(len(images)):
            file_counter += 1
            images[i].save(
                os.path.join(
                    args.output,
                    '{}_{}.png'.format(task_prefix, file_counter),
                ),
            )

# さくらのオブジェクトストレージに格納するための情報がある場合、S3互換APIでアップロード
if args.s3_token and args.s3_secret and args.s3_bucket:
    print('Start uploading to S3')

    s3_config = Config(
        # 互換性担保のため、設定を入れる。
        # https://cloud.sakura.ad.jp/news/2025/02/04/objectstorage_defectversion/?_gl=1%2Awg387d%2A_gcl_aw%2AR0NMLjE3NjgxMjIxMDEuQ2owS0NRaUFzWTNMQmhDd0FSSXNBRjZPNlhqR2V1aDdSejdHZkVUbS1SbTVKSkRBeE9CUGoxQ2FxUjlRQ3BSbFN5Vlo2M1h4UTlXVnVBa2FBdkxyRUFMd193Y0I.%2A_gcl_au%2ANzM1ODg0ODM0LjE3NjA5NjM5MDYuMTQzMDE2MzgwNS4xNzY4MDU2MzU3LjE3NjgwNjE2NTg.
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    )

    # キー情報を元にS3APIクライアントを作成
    s3 = boto3.client(
        's3',
        endpoint_url=args.s3_endpoint if args.s3_endpoint else None,
        aws_access_key_id=args.s3_token,
        aws_secret_access_key=args.s3_secret,
        config=s3_config,
    )

    # 出力フォルダ内のpngを順々に同名アップロード
    files = glob.glob(os.path.join(args.output, '*.png'))
    for file in files:
        print(os.path.basename(file))
 
        s3.upload_file(
            Filename=file,
            Bucket=args.s3_bucket,
            Key=os.path.basename(file),
            ExtraArgs={
                "ContentType": "image/png",
            },
        )
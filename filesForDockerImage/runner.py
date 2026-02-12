import runner_util
import argparse
from diffusers import DiffusionPipeline
import json
import logging
from pathlib import Path
import random
import torch

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

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
arg_parser.add_argument('--objst-bucket', help='オブジェクトストレージのバケットを指定します。')
arg_parser.add_argument('--objst-endpoint', help='オブジェクトストレージ互換エンドポイントのURLを指定します。')
arg_parser.add_argument('--objst-secret', help='オブジェクトストレージのシークレットアクセスキーを指定します。')
arg_parser.add_argument('--objst-token', help='オブジェクトストレージのアクセスキーIDを指定します。')
args = arg_parser.parse_args()

# FLUX.2 klein 4Bの動作準備
logging.info('FLUX.2-klein-4Bを読み込みます。')
pipe = DiffusionPipeline.from_pretrained(
    "/FLUX2-klein-4B",
    torch_dtype=torch.float16,
).to('cuda')
logging.info('FLUX.2-klein-4Bを読み込みました。')

logging.info('主処理開始')
# 画像生成処理
tasks = json.loads(args.prompt)
for task in tasks:
    file_counter = 0

    # タスク情報を取得し、接頭辞・プロンプトが存在しない場合はスキップ
    task_prefix, task_prompt = task
    if not task_prefix or not task_prompt:
        logging.warning(f'必須パラメータが不足しているため、処理をスキップしました。: {task}')
        continue

    logging.info(f'画像編集タスク開始 -> 接頭辞: {task_prefix}, プロンプト: {task_prompt}')

    for batch_iteration in range(int(args.batch)):

        generator = torch.Generator(device="cuda").manual_seed(random.getrandbits(32))

        logging.info('画像生成を実行します。')
        # 出力命令。guidance_scaleは推奨値3.5に固定しているが、変更も可能。
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
        logging.info(f'画像をローカルに保存します。')
        for i in range(len(images)):
            file_counter += 1
            output_path = Path(args.output) / '{}_{}.png'.format(task_prefix, file_counter)
            images[i].save(output_path)
        logging.info('画像をローカルに保存しました。')
logging.info('主処理完了')

# さくらのオブジェクトストレージに格納するための情報がある場合、S3互換APIでアップロード
if args.objst_token and args.objst_secret and args.objst_bucket:

    object_storage_client = runner_util.genObjectStorageClient(endpoint=args.objst_endpoint,
                            token=args.objst_token,
                            secret=args.objst_secret)

    # 出力フォルダ内のpngを順々に同名アップロード
    files = Path(args.output).glob('*.png')
    for file in files:
        filename = Path(file).name

        logging.info(f'画像{filename}をオブジェクトストレージにアップロードします。')
 
        object_storage_client.upload_file(
            Filename=str(file),
            Bucket=args.objst_bucket,
            Key=filename,
            ExtraArgs={
                "ContentType": "image/png",
            },
        )
        logging.info(f'画像{filename}をオブジェクトストレージにアップロードしました。')
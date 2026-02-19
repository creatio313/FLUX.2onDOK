# 概要
さくらインターネット株式会社の高火力 DOKでFLUX.2-klein-4Bを動かすにあたって作成したソース群です。
画像生成・編集に対応しています。

# 使い方
## 1.Dockerイメージ生成
FLUX.2-klein-4Bを含んだDockerイメージを生成します。
1. [Hugging Face](https://huggingface.co/)で会員登録を済ませ、アクセストークンを取得してください。
1. さくらのコンテナレジストリにレジストリとユーザーを作成してください。
1. filesForDockerImage内のファイルを同一のディレクトリに配置し、docker buildします。

```sudo docker build --build-arg access_token=アクセストークン -t <作成したレジストリのホスト名>/flux.2-klein-4b:latest .```

50GBほどディスク容量を使用するため、必要に応じてDockerイメージ生成用サーバーをさくらのクラウドで構築します。Terraformで自動構築するコードは[こちら](https://github.com/creatio313/terraform_for_docker_image_gen/tree/main)。

## 2.Dockerイメージのアップロード
さくらのコンテナレジストリにDockerイメージを保存し、高火力 DOKから使えるようにします。
1. 以下のコマンドを入力します。

```
sudo docker login -t  <作成したレジストリのホスト名>.sakuracr.jp -u <作成したユーザー> -p <作成したユーザーのパスワード>
sudo docker image push <作成したレジストリのホスト名>.sakuracr.jp/flux.2-klein-4b:latestcr.jp/flux.2-klein-4b:latest
```

容量が大きいため、１回ではタイムアウトする場合がありますが、複数回実行すれば、アップロード済レイヤー分を省略して進捗するため、確実にアップロードできます。

## 3.環境準備
1. さくらのクラウドホームで、高火力 DOKの作成権限を含むAPIキー（アクセストークン、アクセストークンシークレット）を取得します。
1. 高火力 DOKの画面でレジストリ―認証情報を登録し、IDを取得します。
1. オブジェクトストレージの石狩第1サイトを利用開始し、アクセスキーIDとシークレットアクセスキーを取得します。バケットを作成し、その名前も記録します。
1. genImage.ps1に上記情報を転記します。イメージ名は「<作成したレジストリのホスト名>/flux.2-klein-4b:latest」を記入してください。

## 4.画像生成
1. 生成されるファイルの接頭辞とプロンプトを記載したcsvファイルを準備します。雛形はimagePrompts.csvです。
1. csvファイルのパスを第一引数にしてgenImage.ps1を実行します。
1. オブジェクトストレージに画像が吐き出される他、高火力 DOKのアーティファクトからも出力結果を得ることができます。

## 5.画像編集
画像編集を行う場合は、editImage.ps1を生成時同様に編集し、画像編集用csvファイル（雛形はimg2imgPrompts.csv）のパスを第一引数にして実行します。
promptに応じて画像が編集され、設定した接尾辞がファイル名に付与された状態で出力されます。

# 参考文献
https://knowledge.sakura.ad.jp/38718/
https://knowledge.sakura.ad.jp/39187/

# 概要
さくらインターネット株式会社の高火力DOKでFLUX 2 klein 4Bを動かすにあたって作成したソース群です。

# 使い方
## 1.Dockerイメージ登録
さくらのクラウドのコンテナレジストリに、Dockerイメージをアップロードします。
Dockerfile、docker-entrypoint.sh、runner.pyを同ディレクトリに配置し、Dockerfileには[Hugging face](https://huggingface.co/)のIDとアクセスキーを記載、docker buildしてください。
その後コンテナレジストリにdocker pushします。容量が大きいため、１回では落ちる場合がありますが、複数回実行すれば確実にアップロードできます。

## 2.画像生成
高火力DOKへのアクセスキーやさくらのオブジェクトストレージの認証情報を取得します。
PowerShellに転記し、csvファイルのパスを第一引数にして実行します。
オブジェクトストレージに画像が吐き出される他、高火力DOKのアーティファクトからも出力結果を取ることができます。

# 参考文献
https://knowledge.sakura.ad.jp/38718/
https://knowledge.sakura.ad.jp/39187/

# =====初期設定値=====
$ACCESSTOKEN = "アクセストークンに置換"
$ACCESSTOKENSECRET = "アクセストークンシークレットに置換"

$URI = "https://secure.sakura.ad.jp/cloud/zone/is1a/api/managed-container/1.0/tasks/"

# =====タスク向け設定値=====
$IMAGENAME = "イメージ名に置換"
$REGISTRYID = "レジストリ―認証情報に置換"

$OBJST_ENDPOINT = "https://s3.isk01.sakurastorage.jp"
$OBJST_TOKEN = "アクセスキーIDに置換"
$OBJST_SECRET = "シークレットアクセスキーに置換"
$OBJST_INPUT_BUCKET = "編集元画像を格納するバケット名に置換"
$OBJST_OUTPUT_BUCKET = "出力画像を格納するバケット名に置換"

# =====AI向け設定値=====
$steps = 28

# 入力データの処理

# csvパス、ファイルの検証
if ($Args.Count -lt 1 -or [string]::IsNullOrWhiteSpace($Args[0])) {
    throw "csvファイルのパスを指定してください。"
}
$CsvPath = $Args[0]
if (-not (Test-Path -LiteralPath $CsvPath)) {
    throw "指定されたcsvファイルが見つかりません: $CsvPath"
}

# csvの読み込み
$CsvFile = Get-Item -LiteralPath $CsvPath # ファイル情報を取得
$rows = Import-Csv -LiteralPath $CsvPath
$promptList = @()

# 二次元配列化
foreach ($r in $rows) {
    $promptList += ,@($r.filepath,$r.prompt, $r.suffix)
}
$promptJsonString = ConvertTo-Json @($promptList) -Compress

# Basic認証ヘッダ作成 
$pair = "$ACCESSTOKEN`:$ACCESSTOKENSECRET"
$bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
$encoded = [Convert]::ToBase64String($bytes)

$headers = @{
    "Authorization" = "Basic $encoded"
    "Content-Type"  = "application/json"
    "Accept"        = "application/json"
}

# csvの各行を読み込み、高火力DOKのタスク登録を行う。

# 送信するJSONボディ =====
$bodyObject = @{
    name = $CsvFile.BaseName + "Task"
    containers = @(
        @{
            image    = $IMAGENAME
            registry = $REGISTRYID
            command  = @()
            entrypoint = @("/docker-entrypoint-img2img.sh")
            environment = @{
                OBJST_ENDPOINT = $OBJST_ENDPOINT
                OBJST_TOKEN = $OBJST_TOKEN
                OBJST_SECRET = $OBJST_SECRET
                OBJST_INPUT_BUCKET = $OBJST_INPUT_BUCKET
                OBJST_OUTPUT_BUCKET = $OBJST_OUTPUT_BUCKET
                PROMPT = $promptJsonString
                STEPS = $steps
            }
            plan = "h100-80gb"
        }
    )
    tags = @()
    execution_time_limit_sec = $null
}

# JSON化（ネストが深いのでDepthを上げる）
$bodyJson = $bodyObject | ConvertTo-Json -Depth 20

# ===== POSTリクエスト =====
$response = Invoke-RestMethod `
    -Method Post `
    -Uri $URI `
    -Headers $headers `
    -Body $bodyJson
# ===== タスクURLの表示 =====
$taskURL = "タスクを登録しました：https://secure.sakura.ad.jp/koukaryoku-container/tasks/detail/" + $response.id

$taskURL

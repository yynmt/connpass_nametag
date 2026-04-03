# connpass_nametag

## 概要
connpass_nametag は [connpass](https://tenkey.connpass.com/) から取得できる参加者一覧の CSV ファイルから名札を生成するツールです。
生成される名札ははがきサイズを想定していますが、用途に応じてコードを修正してください。

---

## 解説

### CSV ファイルについて
参加者一覧の CSV ファイルは申込者の管理ページ右上に表示される「CSVダウンロード」ボタンから取得できます。
申込者の管理ページには各イベントページの上部メニューに表示される「申込者を管理する」から遷移できます。
なお、上記の操作はイベントの管理者のみ可能です。

### connpass API について
connpass に設定しているアイコン画像を connpass API から取得するために、 API の利用申請を行い API キーを取得する必要があります。
詳しくは[コチラ](https://connpass.com/about/api/v2/)

### 各コードの役割

#### main.py
main です。
適宜編集して実行してください。

#### user.py
ユーザ管理部分です。
CSV ファイルの読み込みや connpass API への問い合わせを行います。

#### connpass_api.py
connpass API 問い合わせ部分です。
動作には前述の API キーが必要です。
`api_key` ファイル内に API キーを記載してください。

#### nametag.py
名札生成部分です。
user.py に含まれる User を引数に動作します。
`assets` ディレクトリ以下に各種画像やフォントを格納してください。

#### util_pil.py
PIL のユーティリティ関数群です。
nametag.py から利用しています。

---

## 天キーについて
このツールは[天下一キーボードわいわい会](https://tenkey.connpass.com/) (通称: 天キー) での利用を目的に作成されました。
名札が必要なコミュニティイベントで、是非ご利用ください。

# Spotify Dial Volume - StreamController Plugin

Stream Deck+ のダイヤルで Spotify の音量をコントロールするための StreamController プラグインです。

## 機能

- **ダイヤル回転 (時計回り)**: 音量を +5% 上げる
- **ダイヤル回転 (反時計回り)**: 音量を -5% 下げる
- **ダイヤル押下**: ミュート / ミュート解除のトグル

## 必要条件

- **Spotify Premium** アカウント（Web API の音量操作に必須）
- **Elgato Stream Deck+** (ダイヤル付きモデル)
- **StreamController** (Linux 用 Stream Deck アプリ - https://github.com/StreamController/StreamController)
- **Spotify Developer App** (Client ID / Client Secret の取得用)

## セットアップ手順

### 1. Spotify Developer App の作成

1. https://developer.spotify.com/dashboard にアクセス
2. 「Create App」をクリック
3. アプリ名を入力（例: `StreamDeck Volume`）
4. **Redirect URI** に `https://stream-controller/callback` を追加
5. **Client ID** と **Client Secret** をメモしておく

### 2. プラグインのインストール

#### 方法 A: スタンドアロンプラグインとしてインストール

StreamController のプラグインフォルダにコピーします：

```bash
# Flatpak版の場合:
cp -r streamcontroller-spotify-dial/ \
  ~/.var/app/com.core447.StreamController/data/StreamController/plugins/SpotifyDialVolume/

# ネイティブインストールの場合 (Garuda/Arch):
cp -r streamcontroller-spotify-dial/ \
  ~/.local/share/StreamController/plugins/SpotifyDialVolume/
```

#### 方法 B: 既存の Spotify プラグインにパッチ適用

既に `SpotifyForStreamController` プラグインをインストール済みの場合、パッチファイルを使って
ダイヤルサポートを追加できます：

1. パッチファイルをコピー:

```bash
cp patches/add_dial_to_existing_plugin.py \
  ~/.var/app/com.core447.StreamController/data/StreamController/plugins/SpotifyForStreamController/actions/MediaActions/DialVolumeAction.py
```

2. 既存プラグインの `main.py` を編集して、以下を追加:

```python
# imports セクションに追加:
from .actions.MediaActions.DialVolumeAction import DialVolume

# __init__ メソッド内の他の ActionHolder 登録の後に追加:
holder = ActionHolder(
    plugin_base=self,
    action_base=DialVolume,
    action_id="de_outsider_Spotify::DialVolume",
    action_name="Dial Volume Control",
)
self.add_action_holder(holder)
```

### 3. StreamController での設定

1. StreamController を再起動
2. プラグイン設定画面を開く
3. **Client ID** と **Client Secret** を入力
4. **Login with Spotify** ボタンをクリックして認証
5. Stream Deck+ のダイヤルスロットにアクションを割り当て

## ファイル構成

```
streamcontroller-spotify-dial/
├── main.py                          # プラグインエントリポイント
├── manifest.json                    # プラグインメタデータ
├── actions/
│   └── DialVolumeAction/
│       └── DialVolumeAction.py      # ダイヤルアクション本体
├── utils/
│   └── spotify_client.py            # Spotify Web API クライアント
├── patches/
│   └── add_dial_to_existing_plugin.py  # 既存プラグインへのパッチ
└── assets/                          # アイコン等
```

## 仕組み

StreamController の `ActionBase` クラスは、ダイヤル入力に対して以下のイベントを提供しています：

| イベント | 説明 |
|---------|------|
| `Input.Dial.Events.TURN_CW` | 時計回りに回転 |
| `Input.Dial.Events.TURN_CCW` | 反時計回りに回転 |
| `Input.Dial.Events.DOWN` | ダイヤル押下 |
| `Input.Dial.Events.UP` | ダイヤルリリース |
| `Input.Dial.Events.SHORT_UP` | 短押しリリース |
| `Input.Dial.Events.HOLD_START` | 長押し開始 |
| `Input.Dial.Events.HOLD_STOP` | 長押し終了 |

これらのイベントは `event_callback` メソッドをオーバーライドすることでハンドリングできます。
Spotify Web API の `PUT /me/player/volume` エンドポイントを呼び出して音量を変更します。

## 音量ステップのカスタマイズ

`DialVolumeAction.py` 内の `VOLUME_STEP` を変更することで、1回の回転あたりの音量変化量を
調整できます（デフォルト: 5%）。

## トラブルシューティング

- **403 エラー**: Spotify Premium アカウントが必要です
- **ダイヤルが反応しない**: Stream Deck+ のダイヤルスロットにアクションが割り当てられているか確認
- **認証エラー**: Client ID / Secret を再確認し、Redirect URI が正しいか確認
- **StreamController がプラグインを認識しない**: プラグインフォルダのパスを確認し、StreamController を再起動

## ライセンス

MIT License

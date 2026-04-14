# Stream Deck+ ダイヤルで Spotify 音量を操作する方法 - 選択肢ガイド

## 概要

Garuda Linux + StreamController 環境で Stream Deck+ のダイヤルを使って
Spotify の音量を変更する方法は複数あります。

---

## 選択肢 1: StreamController プラグイン（推奨）

**このリポジトリで提供している方法です。**

StreamController はプラグインを **Python** で開発します。
`ActionBase` クラスの `event_callback` をオーバーライドして、
`Input.Dial.Events.TURN_CW` / `TURN_CCW` を処理し、
Spotify Web API で音量を変更します。

### メリット
- StreamController のネイティブ機能として統合
- Python で書けるので簡単
- Spotify Web API を直接叩くのでレスポンスが良い
- Stream Deck+ のタッチスクリーンやラベル表示も活用可能

### デメリット
- Spotify Premium が必要
- Spotify Developer App の登録が必要

---

## 選択肢 2: Elgato Stream Deck SDK (Node.js)

動画で見た「コードと manifest.json」を使う方法です。
これは **Elgato 公式の Stream Deck SDK** を使ったプラグイン開発です。

### 注意点
Elgato の公式 SDK で作ったプラグインは **Windows / macOS の Stream Deck アプリ専用** です。
**StreamController (Linux) では動作しません**。

もし Windows/macOS でも使うなら:

```bash
npm install -g @elgato/cli
streamdeck create
```

manifest.json でダイヤルを有効にする例:

```json
{
  "Actions": [{
    "UUID": "com.example.spotify-volume",
    "Controllers": ["Encoder"],
    "Encoder": {
      "layout": "$B1",
      "TriggerDescription": {
        "Rotate": "Adjust Volume",
        "Push": "Mute"
      }
    }
  }]
}
```

TypeScript でダイヤルイベントを処理:

```typescript
action.onDialRotate(({ payload }) => {
  const { ticks } = payload;
  adjustVolume(ticks > 0 ? 5 : -5);
});
```

### メリット
- Elgato 公式サポート
- Elgato Marketplace で配布可能

### デメリット
- **Linux では使えない**（StreamController と互換性なし）
- Node.js/TypeScript が必要

---

## 選択肢 3: システムレベルの音量操作（PulseAudio/PipeWire）

Spotify のアプリケーション固有の音量を OS レベルで変更する方法。

StreamController の **VolumeMixer** プラグインが既にこの機能を持っています。

```bash
# Spotify のシンクを見つける
pactl list sink-inputs | grep -A 20 "Spotify"

# 音量を変更する
pactl set-sink-input-volume <sink-input-id> +5%
pactl set-sink-input-volume <sink-input-id> -5%
```

### メリット
- Spotify Premium 不要
- API 登録不要
- ローカルで完結

### デメリット
- ローカルの Spotify クライアントのみ（Spotify Connect 非対応）
- StreamController の VolumeMixer プラグインのダイヤル対応状況による

---

## 選択肢 4: D-Bus / MPRIS 経由

Linux の MPRIS (Media Player Remote Interfacing Specification) を使う方法。

```bash
# 音量を取得
dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify \
  /org/mpris/MediaPlayer2 \
  org.freedesktop.DBus.Properties.Get \
  string:'org.mpris.MediaPlayer2.Player' string:'Volume'

# 音量を設定 (0.0 ~ 1.0)
dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify \
  /org/mpris/MediaPlayer2 \
  org.freedesktop.DBus.Properties.Set \
  string:'org.mpris.MediaPlayer2.Player' string:'Volume' \
  variant:double:0.5
```

StreamController の **MediaPlugin** に D-Bus 経由のダイヤル操作を追加することも可能。

### メリット
- Spotify Premium 不要
- ネットワーク不要
- 標準的な Linux API

### デメリット
- ローカルの Spotify クライアントのみ
- 一部の Spotify クライアントで MPRIS の Volume プロパティが未実装の場合がある

---

## 推奨

| 用途 | 推奨方法 |
|------|----------|
| リモートデバイスの音量も変えたい | **選択肢 1** (Spotify Web API) |
| Premium なし・ローカルのみ | **選択肢 3** (PulseAudio) or **選択肢 4** (D-Bus) |
| Windows/macOS で使いたい | **選択肢 2** (Elgato SDK) |
| 最も簡単にやりたい | **選択肢 1** の方法 B（既存プラグインにパッチ） |

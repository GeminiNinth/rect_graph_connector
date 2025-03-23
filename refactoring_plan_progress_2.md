# Refactoring Progress Report 2: イベント処理分離と CanvasView 統合計画

## 概要
このドキュメントは、フェーズ3におけるイベント処理分離の残り作業と、CanvasView への InputHandler 統合のための実装レベルの具体的手順および設計上の留意点（堅牢なコード実現のためのベストプラクティスを含む）を記述する。

## 現在の状況
- InputHandler、ModeController、および各モード固有のコントローラーは実装済み。
- CanvasView は依然として直接イベント処理を行っており、InputHandler との統合が完了していない。

## フェーズ3の残り作業

### 1. CanvasViewへのInputHandler統合
**実装手順:**
1. CanvasView のコンストラクタで InputHandler を初期化し、依存性注入を実施する。
2. 各イベントハンドラ（mousePressEvent, mouseMoveEvent, mouseReleaseEvent, keyPressEvent, wheelEvent）で、直接処理するのではなく、InputHandler の対応メソッドに委譲する。
3. イベント発生時に widget 座標を graph 座標に変換し、InputHandler に渡す。
4. イベント処理後、キャンバスの更新（再描画）を適切に行う。

**設計上の留意点:**
- **依存性注入:** InputHandler を外部から渡すことでテスト容易性を向上させる。
- **単一責任の原則:** CanvasView はレンダリングに専念させ、入力処理は InputHandler に委譲する。
- **エラーハンドリング:** 各イベント処理で例外をキャッチし、システム全体の安定性を確保する。
- **パフォーマンス:** 軽量なイベント処理と不要な再描画の防止を徹底する。
- **拡張性:** 将来的な入力デバイスやイベント処理の追加に柔軟に対応できる設計とする。

### 2. CanvasView 内部のイベントメソッド改修
**具体的な改修例:**
```python
# 変更前
def mousePressEvent(self, event):
    self.handle_direct_mouse_press(event)
    self.update()

# 変更後
def mousePressEvent(self, event):
    graph_point = self.convert_to_graph_point(event.pos())
    self.input_handler.handle_mouse_press(event, graph_point)
    self.update()
```
- 他のイベントメソッドについても同様の改修を行い、冗長なコードを削減する。

### 3. テストとドキュメントの充実
- InputHandler の各メソッドに対し、モックを用いた単体テストケースを作成する。
- CanvasView と InputHandler の統合テストを実施し、イベントの正しい委譲と画面更新を確認する。
- 設計変更点をコードレビューし、SOLID原則やベストプラクティスに則っているかを検証する。

## 設計上のベストプラクティス
1. **分離とモジュール化:** 入力処理とレンダリング処理を明確に分離し、各コンポーネントの責務を明確にする。
2. **依存性注入:** コンポーネント間の依存性を明示的にし、テストや再利用が容易な設計とする。
3. **エラーハンドリング:** 例外発生時に適切な対応を行い、クラッシュを防止する。
4. **コードの簡素化:** 冗長なコードを排除し、読みやすく保守が容易な設計を心掛ける。
5. **ユニットテスト:** 各コンポーネントに対する十分なテストケースを整備し、将来的な変更に備える。

## 今後のステップ
- CanvasView と InputHandler の統合後、全体の動作確認テストを実施する。
- 統合テストの結果に基づき、必要な修正を段階的に行う。
- 全体のコードレビューを実施し、追加のベストプラクティスが適用可能か検討する。

## 結論
フェーズ3の残り作業は、既存のイベント処理システムの改善と CanvasView への InputHandler 統合に焦点を当てる。具体的な実装手順と設計上の留意点を踏まえ、堅牢で保守性の高いコードへと改善することを目指す.
src\rect_graph_connector\gui\canvas.pyがあまりにも肥大化しているため、SOLID原則と高凝集・疎結合の考えに基づきレンダリングシステムをリファクタリングする計画を立てる。
もともとsrc\rect_graph_connector\guiにあった機能を以下のような形で移行したい。
一気にやらず、ステップバイステップで行きましょう。
特に「リファクタリング手順」のステップごとにmain.pyから動作の様子を見たいので報告をお願いします。

# レンダリングシステムリファクタリング計画

## 1. 新規ディレクトリ構造

```
src/rect_graph_connector/
├── models/
│   ├── graph_model.py (既存のgraph.pyを拡張)
│   ├── view_state_model.py (新規: ビュー状態管理)
│   ├── selection_model.py (新規: 選択状態管理)
│   └── hover_state_model.py (新規: ホバー状態管理)
├── rendering/
│   ├── canvas_view.py (リファクタリング後のcanvas.py)
│   └── gui/
│       ├── base_renderer.py (改善)
│       ├── composite_renderer.py (改善)
│       ├── node_renderer.py (改善)
│       ├── group_renderer.py (新規: グループ描画専用)
│       ├── edge_renderer.py (改善)
│       └── styles/
│           ├── base_style.py (新規: スタイル基底クラス)
│           ├── node_style.py (新規)
│           ├── group_style.py (新規)
│           └── edge_style.py (新規)
└── controllers/
    ├── input_handler.py (新規: 入力処理統合)
    ├── mode_controller.py (新規: モード管理)
    └── modes/
        ├── normal_mode_controller.py (新規)
        └── edit_mode_controller.py (新規)

```

## 2. 主要コンポーネントの設計

### ViewStateModel

```python
class ViewStateModel:
    def __init__(self):
        self._zoom = 1.0
        self._pan_offset = QPointF(0, 0)
        self._grid_visible = False
        self._snap_to_grid = False
        self.state_changed = Event()

    @property
    def zoom(self): 
        return self._zoom

    @zoom.setter
    def zoom(self, value):
        self._zoom = value
        self.state_changed.emit()

    @property
    def pan_offset(self):
        return self._pan_offset

    @pan_offset.setter
    def pan_offset(self, value):
        self._pan_offset = value
        self.state_changed.emit()
```

### SelectionModel

```python
class SelectionModel:
    def __init__(self):
        self.selected_nodes = []
        self.selected_groups = []
        self.selected_edges = []
        self.selection_changed = Event()

    def select_node(self, node, add_to_selection=False):
        if not add_to_selection:
            self.selected_nodes.clear()
        if node not in self.selected_nodes:
            self.selected_nodes.append(node)
            self.selection_changed.emit()

    def select_group(self, group, add_to_selection=False):
        if not add_to_selection:
            self.selected_groups.clear()
        if group not in self.selected_groups:
            self.selected_groups.append(group)
            self.selection_changed.emit()
```

### HoverStateModel

```python
class HoverStateModel:
    def __init__(self):
        self.hovered_node = None
        self.hovered_connected_nodes = []
        self.hovered_edges = []
        self.potential_target_node = None
        self.hover_changed = Event()

    def update_hover_state(self, node, connected_nodes=None, edges=None):
        self.hovered_node = node
        self.hovered_connected_nodes = connected_nodes or []
        self.hovered_edges = edges or []
        self.hover_changed.emit()
```

### 改善されたBaseRenderer

```python
class BaseRenderer(ABC):
    def __init__(self, view_state: ViewStateModel, style: BaseStyle):
        self.view_state = view_state
        self.style = style
        
    @abstractmethod
    def draw(self, painter: QPainter, **kwargs):
        pass

    def apply_transform(self, painter: QPainter):
        painter.translate(self.view_state.pan_offset)
        painter.scale(self.view_state.zoom, self.view_state.zoom)
```

### InputHandler

```python
class InputHandler:
    def __init__(self, view_state: ViewStateModel, selection_model: SelectionModel):
        self.view_state = view_state
        self.selection_model = selection_model
        self.current_mode = None

    def handle_mouse_press(self, event, graph_point):
        if self.current_mode:
            return self.current_mode.handle_mouse_press(event, graph_point)
        return False

    def handle_mouse_move(self, event, graph_point):
        if self.current_mode:
            return self.current_mode.handle_mouse_move(event, graph_point)
        return False

    def handle_mouse_release(self, event, graph_point):
        if self.current_mode:
            return self.current_mode.handle_mouse_release(event, graph_point)
        return False
```

## 3. リファクタリング手順

### フェーズ1: モデル層の実装（高優先度）
1. ViewStateModel の実装
   - zoom, pan_offset などの状態管理
   - グリッド表示状態の管理
   - 状態変更通知の実装

2. SelectionModel の実装
   - 選択状態の一元管理
   - 選択変更通知の実装

3. HoverStateModel の実装
   - ホバー状態の一元管理
   - ホバー状態変更通知の実装

### フェーズ2: レンダリングシステムの改善（高優先度）
1. BaseRenderer の改善
   - Canvas依存の除去
   - ViewStateModelの導入
   - スタイル管理の導入

2. スタイルシステムの実装
   - BaseStyle の実装
   - 各コンポーネント用スタイルクラスの実装

3. レンダラーの分割と改善
   - NodeRenderer と GroupRenderer の分離
   - 各レンダラーのViewStateModel対応
   - スタイル適用の実装

### フェーズ3: イベント処理の分離（中優先度）
1. InputHandler の実装
   - マウス/キーボードイベントの一次処理
   - モードコントローラーへの委譲

2. モードコントローラーの実装
   - NormalModeController の実装
   - EditModeController の実装

### フェーズ4: CanvasView のリファクタリング（中優先度）
1. 状態管理の移行
   - ViewStateModel への移行
   - SelectionModel への移行
   - HoverStateModel への移行

2. イベント処理の移行
   - InputHandler への移行
   - モードコントローラーの統合

### フェーズ5: テストとドキュメント（低優先度）
1. 単体テストの作成
   - 各モデルのテスト
   - レンダラーのテスト
   - イベント処理のテスト

2. ドキュメントの更新
   - クラス図の作成
   - シーケンス図の作成
   - README の更新

## 4. 期待される効果

1. **保守性の向上**
   - 責務の明確な分離
   - コンポーネント間の疎結合化
   - テスト容易性の向上

2. **拡張性の向上**
   - 新規モードの追加が容易に
   - スタイルのカスタマイズが容易に
   - レンダリング機能の拡張が容易に

3. **パフォーマンスの向上**
   - 状態管理の最適化
   - 再描画の最適化
   - メモリ使用の効率化

## 5. リスクと対策

1. **既存機能への影響**
   - 段階的なリファクタリングの実施
   - 各フェーズでのテスト実施
   - 既存テストの維持

2. **パフォーマンスへの影響**
   - プロファイリングの実施
   - ボトルネックの特定と対策
   - キャッシュの活用

3. **開発工数**
   - フェーズごとの優先度設定
   - 必要に応じたスコープ調整
   - 継続的なレビューと調整
"""
This module contains the import mode dialog for selecting and explaining import modes.
"""

from typing import Dict, Optional, Any, Union
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QGroupBox,
    QToolTip,
    QScrollArea,
    QWidget,
)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QFont
from dataclasses import dataclass


@dataclass
class ModeDetails:
    """
    Data class for import mode
    """

    title: str
    description: str
    example: str
    guidance: str


class ImportModeDialog(QDialog):
    """
    Custom dialog class that provides import mode selection and detailed explanations.

    This dialog displays detailed explanations and visual examples for each import mode,
    supporting users in selecting the appropriate mode.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the import mode dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("インポートモードの選択")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self.selected_mode = "overwrite"  # Default mode

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Description label
        description = QLabel(
            "インポートするファイルの処理方法を選択してください。各モードの違いは以下の通りです："
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # Mode selection group box
        mode_group = QGroupBox("インポートモード")
        mode_layout = QVBoxLayout(mode_group)

        # Radio button group
        self.button_group = QButtonGroup(self)

        # Radio buttons and descriptions for each mode
        self._add_mode_option(
            mode_layout,
            "overwrite",
            "上書き",
            "既存のデータを保持したまま、新しいデータを追加します。\n"
            "同じIDのノードが存在する場合でも、両方を保持します。\n"
            "新旧のデータを最大限残したい場合に使用します。",
        )

        self._add_mode_option(
            mode_layout,
            "insert_before",
            "前に挿入",
            "新しいグループを既存のグループの前に挿入します。\n"
            "ノードIDは再割り当てされ、新しいグループのノードが先に来るようになります。\n"
            "処理の順序で新しいグループを先に配置したい場合に使用します。",
        )

        self._add_mode_option(
            mode_layout,
            "insert_after",
            "後に挿入",
            "新しいグループを既存のグループの後に挿入します。\n"
            "ノードIDは再割り当てされ、既存のグループのノードが先に来るようになります。\n"
            "処理の順序で新しいグループを後に配置したい場合に使用します。",
        )

        self._add_mode_option(
            mode_layout,
            "force",
            "完全置換",
            "既存のグラフを完全にリセットし、新しいデータだけを読み込みます。\n"
            "現在の作業内容はすべて失われます。\n"
            "新しいプロジェクトを開始する場合や、完全に置き換えたい場合に使用します。",
        )

        layout.addWidget(mode_group)

        # Detail explanation area
        self.detail_area = QScrollArea()
        self.detail_area.setWidgetResizable(True)
        self.detail_widget = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_widget)

        # Detail explanation title
        detail_title = QLabel("詳細説明")
        detail_title.setFont(QFont("", 12, QFont.Bold))
        self.detail_layout.addWidget(detail_title)

        # Detail explanation content
        self.detail_content = QLabel()
        self.detail_content.setWordWrap(True)
        self.detail_content.setMinimumHeight(200)
        self.detail_layout.addWidget(self.detail_content)

        # Visual example description
        self.visual_example = QLabel()
        self.visual_example.setWordWrap(True)
        self.detail_layout.addWidget(self.visual_example)

        # Usage guidance
        self.usage_guidance = QLabel()
        self.usage_guidance.setWordWrap(True)
        self.detail_layout.addWidget(self.usage_guidance)

        self.detail_layout.addStretch()
        self.detail_area.setWidget(self.detail_widget)
        layout.addWidget(self.detail_area)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Display default mode details
        self._update_detail_area("soft")

    def _add_mode_option(
        self, layout: QVBoxLayout, mode_id: str, mode_name: str, tooltip: str
    ) -> None:
        """
        Add a mode selection option.

        Args:
            layout: Target layout to add the option to
            mode_id: Mode identifier
            mode_name: Display name for the mode
            tooltip: Tooltip text
        """
        radio = QRadioButton(mode_name)
        radio.setToolTip(tooltip)
        radio.setProperty("mode_id", mode_id)

        # Show details on hover
        radio.enterEvent = lambda event, r=radio, m=mode_id: self._on_radio_hover(
            event, r, m
        )

        # Show details on click
        radio.toggled.connect(
            lambda checked, m=mode_id: self._on_radio_toggled(checked, m)
        )

        self.button_group.addButton(radio)
        layout.addWidget(radio)

        # Select default mode
        if mode_id == self.selected_mode:
            radio.setChecked(True)

    def _on_radio_hover(self, event: QEvent, radio: QRadioButton, mode_id: str) -> None:
        """
        Handle radio button hover event.

        Args:
            event: Event object
            radio: Radio button being hovered
            mode_id: Mode identifier
        """
        QToolTip.showText(event.globalPos(), radio.toolTip())

    def _on_radio_toggled(self, checked: bool, mode_id: str) -> None:
        """
        Handle radio button toggle event.

        Args:
            checked: Check state
            mode_id: Mode identifier
        """
        if checked:
            self.selected_mode = mode_id
            self._update_detail_area(mode_id)

    def _update_detail_area(self, mode_id: str) -> None:
        """
        Update the detail area.

        Args:
            mode_id: Mode identifier
        """
        # Detailed explanations for each mode
        details: ModeDetails = {
            "insert_before": {
                "title": "前に挿入モード",
                "description": "このモードでは、新しいグループを既存のグループの前に挿入します。"
                "すべてのノードIDは再割り当てされ、新しいグループのノードが先に来るようになります。"
                "これにより、処理の順序で新しいグループを先に配置することができます。",
                "example": "例：既存のグラフに「グループA」と「グループB」があり、インポートするファイルに"
                "「グループC」と「グループD」がある場合、結果として「グループC」「グループD」「グループA」「グループB」"
                "という順序になります。ノードIDは0から順に振り直されます。",
                "guidance": "このモードは以下の場合に適しています：\n"
                "・処理パイプラインの前段階にグループを追加したい場合\n"
                "・新しいグループを優先順位が高いものとして扱いたい場合\n"
                "・ノードIDの順序が重要で、新しいノードを先に配置したい場合",
            },
            "insert_after": {
                "title": "後に挿入モード",
                "description": "このモードでは、新しいグループを既存のグループの後に挿入します。"
                "すべてのノードIDは再割り当てされ、既存のグループのノードが先に来るようになります。"
                "これにより、処理の順序で新しいグループを後に配置することができます。",
                "example": "例：既存のグラフに「グループA」と「グループB」があり、インポートするファイルに"
                "「グループC」と「グループD」がある場合、結果として「グループA」「グループB」「グループC」「グループD」"
                "という順序になります。ノードIDは0から順に振り直されます。",
                "guidance": "このモードは以下の場合に適しています：\n"
                "・処理パイプラインの後段階にグループを追加したい場合\n"
                "・既存のグループを優先順位が高いものとして扱いたい場合\n"
                "・ノードIDの順序が重要で、既存のノードを先に配置したい場合",
            },
            "overwrite": {
                "title": "上書きモード",
                "description": "このモードでは、既存のデータと競合する部分（同じIDのノード/同じ名前のグループ）は"
                "新しいデータで上書きされます。競合しない部分は両方保持されます。"
                "これにより、特定のグループやノードを更新しながら、他の部分は保持することができます。",
                "example": "例：既存のグラフに「グループA」と「グループB」があり、インポートするファイルに"
                "「グループB」と「グループC」がある場合、結果として「グループA」「グループB（更新済）」「グループC」"
                "という3つのグループが存在することになります。「グループB」は既存のエッジ接続に新たなエッジ接続が追加されます。",
                "guidance": "このモードは以下の場合に適しています：\n"
                "・特定のグループやノードを更新したい場合\n"
                "・部分的な変更を加えたい場合\n"
                "・既存のプロジェクトに新しいコンポーネントを追加したい場合",
            },
            "force": {
                "title": "完全置換モード",
                "description": "このモードでは、既存のグラフを完全にリセットし、新しいデータだけを読み込みます。"
                "現在の作業内容はすべて失われます。"
                "これは新しいプロジェクトを開始する場合や、完全に置き換えたい場合に使用します。",
                "example": "例：既存のグラフに「グループA」と「グループB」があり、インポートするファイルに"
                "「グループC」と「グループD」がある場合、結果として「グループC」「グループD」"
                "のみが存在することになります。「グループA」と「グループB」は完全に削除されます。",
                "guidance": "このモードは以下の場合に適しています：\n"
                "・新しいプロジェクトを開始する場合\n"
                "・現在の作業内容を破棄して新しいデータに置き換えたい場合\n"
                "・クリーンな状態から始めたい場合\n"
                "※注意：このモードは現在の作業内容をすべて削除します。必要に応じて事前にエクスポートしてください。",
            },
        }

        # Update details
        mode_details = details.get(mode_id, {})
        # Check if attributes exist before updating
        if hasattr(self, "detail_content"):
            self.detail_content.setText(mode_details.get("description", ""))
        if hasattr(self, "visual_example"):
            self.visual_example.setText(mode_details.get("example", ""))
        if hasattr(self, "usage_guidance"):
            self.usage_guidance.setText(mode_details.get("guidance", ""))

    def get_selected_mode(self) -> str:
        """
        Return the selected mode.

        Returns:
            str: The ID of the selected mode
        """
        return self.selected_mode

"""
This module contains the import mode dialog for selecting and explaining import modes.
"""

from typing import Dict, Optional, Any, Union, cast
from ..config import config
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
        self.setWindowTitle(config.get_text("import_dialog.window_title"))
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self.selected_mode = "overwrite"  # Default mode

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Description label
        description = QLabel(config.get_text("import_dialog.description"))
        description.setWordWrap(True)
        layout.addWidget(description)

        # Mode selection group box
        mode_group = QGroupBox(config.get_text("import_dialog.group_title"))
        mode_layout = QVBoxLayout(mode_group)

        # Radio button group
        self.button_group = QButtonGroup(self)

        # Radio buttons and descriptions for each mode
        modes = ["overwrite", "insert_before", "insert_after", "force"]
        for mode in modes:
            self._add_mode_option(
                mode_layout,
                mode,
                config.get_text(f"import_dialog.modes.{mode}.name"),
                config.get_text(f"import_dialog.modes.{mode}.tooltip"),
            )

        layout.addWidget(mode_group)

        # Detail explanation area
        self.detail_area = QScrollArea()
        self.detail_area.setWidgetResizable(True)
        self.detail_widget = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_widget)

        # Detail explanation title
        detail_title = QLabel(config.get_text("import_dialog.detail_title"))
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
        ok_button = QPushButton(config.get_text("import_dialog.buttons.ok"))
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton(config.get_text("import_dialog.buttons.cancel"))
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Display default mode details
        self._update_detail_area(self.selected_mode)

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
        # Update details using translations
        if hasattr(self, "detail_content"):
            self.detail_content.setText(
                config.get_text(f"import_dialog.modes.{mode_id}.description")
            )
        if hasattr(self, "visual_example"):
            self.visual_example.setText(
                config.get_text(f"import_dialog.modes.{mode_id}.example")
            )
        if hasattr(self, "usage_guidance"):
            self.usage_guidance.setText(
                config.get_text(f"import_dialog.modes.{mode_id}.guidance")
            )

    def get_selected_mode(self) -> str:
        """
        Return the selected mode.

        Returns:
            str: The ID of the selected mode
        """
        return self.selected_mode

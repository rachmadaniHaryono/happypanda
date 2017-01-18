"""custom table item."""
from PyQt5.QtWidgets import QTableWidgetItem


class CustomTableItem(QTableWidgetItem):
    """CustomTableItem.

    Args:
        item: Item for table.
        txt: Text for item.
        type: Type for parent class.

    Attributes:
        item: Item.
    """

    def __init__(self, item=None, txt='', type=QTableWidgetItem.Type):
        """__init__."""
        super().__init__(txt, type)
        self.item = item

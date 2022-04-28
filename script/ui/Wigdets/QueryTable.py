from PyQt5 import QtCore, QtGui, QtWidgets
from ... import S1Product
from ... import Inferno
from .. import Common
from typing import List

class SearchResultTableWidget(Common.TableWidget):
    list_attribut = [
            "Selection",
            "Name",
            "Date",
            'Orbit Numer',
            'Orbit Type',
            'Satellite',
            "Polarization",
            'Quicklook',
            'Provider',
            "Available"
        ]

    class Item():
        pixelMapScale = (200,200)

        def __init__(self,product:S1Product.S1Product) -> None:
            self.product = product
            self.pixelMap = self._initPixelMap()
            self.checkBox = self._initCheckBox()

        def _initCheckBox(self,State = QtCore.Qt.Unchecked)-> QtWidgets.QCheckBox: 
            checkBox = QtWidgets.QCheckBox()
            checkBox.setCheckState(QtCore.Qt.Checked)
            return checkBox
        
        def get_CheckBoxWidget(self,parent:QtWidgets.QWidget)-> QtWidgets.QWidget:
            cell_widget = QtWidgets.QWidget(parent)
            lay_out = QtWidgets.QHBoxLayout(cell_widget)
            lay_out.setAlignment(QtCore.Qt.AlignCenter)
            cell_widget.setLayout(lay_out)
            lay_out.addWidget(self.checkBox)
            return cell_widget

        def _initPixelMap(self):
            image_path = self.product.quicklook
            pixmap = QtGui.QPixmap()
            pixmap.load(image_path)
            pixmap = pixmap.scaled(*(self.pixelMapScale), QtCore.Qt.KeepAspectRatio) 

            return pixmap

        def get_status(self):
            return self.checkBox.checkState()

    def __init__(self, parent: QtWidgets):
        super().__init__(parent, self.list_attribut)

    @staticmethod
    def get_attribut_index(attribut):
        return SearchResultTableWidget.list_attribut.index(attribut)

    def add_item(self,product:S1Product.S1Product):
        def _setItem( attr,product_attr,):

            _Qitem = None
            if isinstance(product_attr,int):
                _Qitem = QtWidgets.QTableWidgetItem()
                _Qitem.setData(QtCore.Qt.EditRole,new_item.product.revisit)
            else:
                _Qitem = QtWidgets.QTableWidgetItem(product_attr)
            
            if not product.available:
                _brush = QtGui.QBrush(QtCore.Qt.red)
                _Qitem.setForeground(_brush)
                self.setItem(current_row,self.get_attribut_index(attr),_Qitem)
            else:
                self.setItem(current_row,self.get_attribut_index(attr),_Qitem)

        self.setSortingEnabled(False)

        new_item = self.Item(product)      
        self.list_item.append(new_item)

        current_row = self.rowCount()
        self.insertRow(current_row)

        # define some helper functions
        
        ## set item ui
        _setItem("Name"         ,str(new_item.product.name ))
        _setItem("Date"         ,str(new_item.product.date ))
        _setItem("Orbit Type"   ,str(new_item.product.orbitType ))
        _setItem("Satellite"    ,str(new_item.product.satellite ))
        _setItem("Satellite"    ,str(new_item.product.satellite ))
        _setItem("Polarization" ,str(new_item.product.polarization ))
        _setItem("Provider"     ,str(new_item.product.provider ))
        _setItem("Available"    ,str(new_item.product.available ))
        _setItem("Orbit Numer"  ,new_item.product.orbitNumber)

            # Quicklook
        self.setCellWidget(
            current_row,
            self.list_attribut.index("Quicklook"),
            self.get_quicklookLabel(new_item)
            )
            # fixe scale of row and colums
        self.horizontalHeader().setSectionResizeMode(
            self.list_attribut.index("Quicklook"),
            QtWidgets.QHeaderView.ResizeToContents
            )
        self.verticalHeader().setSectionResizeMode(
            current_row,
            QtWidgets.QHeaderView.ResizeToContents
            )

            # Checkbox
        self.setCellWidget(
            current_row,
            self.list_attribut.index("Selection") ,
            new_item.get_CheckBoxWidget(self))
        self.setSortingEnabled(True)
        
    def get_quicklookLabel(self,item:Item):
        pixelmap = item.pixelMap
        imageLabel = Common.quicklookLabel(self,item.product)
        imageLabel.setText("")
        imageLabel.setPixmap(pixelmap)
        imageLabel.setScaledContents(True)
        imageLabel.setScaledContents(True)
        return imageLabel

    def get_selected_element(self) -> List[S1Product.S1Product]:
        output = []
        for ele in self.list_item:
            if ele.get_status():
                output.append(ele.product)
        return output
import sys
import csv
import mysql.connector
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, \
    QMessageBox, QTableWidgetItem, QFileDialog, QHeaderView, QInputDialog
from PyQt5.QtCore import Qt
from RigTracker_ui import Ui_MainWindow

# --- CLEAN ACOUSTIC STUDIO STYLESHEET ---
ACOUSTIC_THEME = """
QMainWindow { background-color: #FAF8F5; }
QLabel { color: #4A443F; font-weight: bold; }
QLineEdit, QComboBox, QDoubleSpinBox { background-color: #FFFFFF; color: #4A443F; border: 1px solid #E3DDD5; border-radius: 4px; padding: 6px; }
QTableWidget { background-color: #FFFFFF; color: #4A443F; gridline-color: #E3DDD5; border: 1px solid #E3DDD5; border-radius: 4px; selection-background-color: #E3DDD5; selection-color: #4A443F; }
QHeaderView::section { background-color: #F0EBE1; color: #4A443F; padding: 4px; border: 1px solid #E3DDD5; font-weight: bold; }
QPushButton { color: #FFFFFF; border-radius: 4px; font-weight: bold; padding: 8px; }
QPushButton#saveButton, QPushButton#loginBtn, QPushButton#newBuildButton { background-color: #8C9B86; border: 1px solid #7D8C77; }
QPushButton#saveButton:hover, QPushButton#loginBtn:hover, QPushButton#newBuildButton:hover { background-color: #7D8C77; }
QPushButton#clearButton, QPushButton#deleteButton { background-color: #C2847A; border: 1px solid #B3756B; }
QPushButton#clearButton:hover, QPushButton#deleteButton:hover { background-color: #B3756B; }
QPushButton#exportButton, QPushButton#logoutButton { background-color: #9CA3A8; border: 1px solid #8D9499; }
QPushButton#exportButton:hover, QPushButton#logoutButton:hover { background-color: #8D9499; }
"""


class LoginApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RigTracker - System Login")
        self.setFixedSize(350, 400)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)

        title_label = QLabel("Welcome to RigTracker")
        title_label.setStyleSheet("font-size: 20px; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username (admin)")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password (password)")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.login_btn = QPushButton("Authenticate")
        self.login_btn.setObjectName("loginBtn")
        self.login_btn.clicked.connect(self.process_login)
        layout.addWidget(self.login_btn)
        central_widget.setLayout(layout)

    def process_login(self):
        user = self.username_input.text()
        pwd = self.password_input.text()
        if user == "admin" and pwd == "password":
            self.main_app = RigTrackerApp()
            self.main_app.show()
            self.close()
        else:
            QMessageBox.critical(self, "Error", "Invalid credentials. Please try again.")


class RigTrackerApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.db = self.connect_db()

        self.partsTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.partsTable.setSortingEnabled(True)

        # Connect all buttons
        self.saveButton.clicked.connect(self.add_component)
        self.clearButton.clicked.connect(self.nuke_database)
        self.exportButton.clicked.connect(self.export_csv)
        self.deleteButton.clicked.connect(self.delete_selected)
        self.searchInput.textChanged.connect(self.search_filter)
        self.logoutButton.clicked.connect(self.logout)

        # New Build Architecture Connections
        self.newBuildButton.clicked.connect(self.create_new_build)
        self.buildSelector.currentIndexChanged.connect(self.load_data)

        if self.db:
            self.load_builds_dropdown()  # Load the builds first!

    def connect_db(self):
        try:
            return mysql.connector.connect(host="localhost", user="root", password="", database="rigtracker_db")
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Connection Error", f"Cannot connect to XAMPP:\n{err}")
            return None

    # --- NEW: Fetch builds from the database and put them in the dropdown ---
    def load_builds_dropdown(self):
        self.buildSelector.blockSignals(True)  # Stop it from glitching while loading
        self.buildSelector.clear()
        cursor = self.db.cursor()
        cursor.execute("SELECT Build_ID, Build_Name FROM builds")
        builds = cursor.fetchall()

        for build in builds:
            # We save the ID inside the dropdown data so Python knows exactly which one is selected
            self.buildSelector.addItem(build[1], userData=build[0])

        self.buildSelector.blockSignals(False)
        self.load_data()  # Now load the parts for whatever build is currently showing

    # --- NEW: Create a new build workspace ---
    def create_new_build(self):
        name, ok = QInputDialog.getText(self, 'New Build', 'Enter a name for your new PC build:')
        if ok and name:
            try:
                cursor = self.db.cursor()
                cursor.execute("INSERT INTO builds (Build_Name) VALUES (%s)", (name,))
                self.db.commit()
                self.load_builds_dropdown()  # Refresh the dropdown menu

                # Automatically select the new build we just made
                index = self.buildSelector.findText(name)
                if index >= 0:
                    self.buildSelector.setCurrentIndex(index)

            except mysql.connector.Error as err:
                QMessageBox.critical(self, "Error", f"Could not create build:\n{err}")

    def load_data(self):
        if not self.db or self.buildSelector.count() == 0: return

        # Get the currently selected Build_ID
        active_build_id = self.buildSelector.currentData()

        self.partsTable.setRowCount(0)
        cursor = self.db.cursor()

        try:
            # ONLY grab parts that belong to the active Build_ID!
            cursor.execute(
                "SELECT Model, Category, ItemCondition, BasePrice, Date_Added FROM components WHERE Build_ID = %s",
                (active_build_id,))
            rows = cursor.fetchall()

            total_price = 0.00
            self.partsTable.setSortingEnabled(False)

            for row_data in rows:
                row_pos = self.partsTable.rowCount()
                self.partsTable.insertRow(row_pos)
                self.partsTable.setItem(row_pos, 0, QTableWidgetItem(row_data[0]))
                self.partsTable.setItem(row_pos, 1, QTableWidgetItem(row_data[1]))
                self.partsTable.setItem(row_pos, 2, QTableWidgetItem(row_data[2]))
                self.partsTable.setItem(row_pos, 3, QTableWidgetItem(f"₱ {float(row_data[3]):,.2f}"))

                date_str = row_data[4].strftime("%b %d, %Y") if row_data[4] else "Just Now"
                self.partsTable.setItem(row_pos, 4, QTableWidgetItem(date_str))

                total_price += float(row_data[3])

            self.partsTable.setSortingEnabled(True)
            self.totalLabel.setText(f"Grand Total: ₱ {total_price:,.2f}")

        except mysql.connector.Error as err:
            print(f"Load Error: {err}")

    def add_component(self):
        if self.buildSelector.count() == 0:
            QMessageBox.warning(self, "Wait!", "Please create a build first!")
            return

        model = self.modelInput.text()
        category = self.categoryInput.currentText().replace("Category: ", "")
        condition = self.conditionInput.currentText().replace("Condition: ", "")
        price = self.basePriceInput.value()
        active_build_id = self.buildSelector.currentData()  # Which build are we saving to?

        if not model:
            QMessageBox.warning(self, "Error", "Model name cannot be empty!")
            return

        try:
            cursor = self.db.cursor()
            # Save the new part AND attach it to the active Build_ID
            cursor.execute(
                "INSERT INTO components (Model, Category, ItemCondition, BasePrice, Build_ID) VALUES (%s, %s, %s, %s, %s)",
                (model, category, condition, price, active_build_id))
            self.db.commit()
            self.modelInput.clear()
            self.load_data()
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Database Error", f"Save failed:\n{err}")

    def delete_selected(self):
        current_row = self.partsTable.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Selection Error", "Please click on a part in the table to delete it.")
            return

        model_to_delete = self.partsTable.item(current_row, 0).text()
        active_build_id = self.buildSelector.currentData()

        msg = QMessageBox(self)
        msg.setWindowTitle('Confirm Delete')
        msg.setText(f"Are you sure you want to delete '{model_to_delete}' from this build?")
        msg.setIcon(QMessageBox.Question)
        yes_btn = msg.addButton("Yes", QMessageBox.YesRole)
        yes_btn.setStyleSheet("background-color: #C2847A; color: white;")
        no_btn = msg.addButton("No", QMessageBox.NoRole)
        no_btn.setStyleSheet("background-color: #8C9B86; color: white;")
        msg.exec_()

        if msg.clickedButton() == yes_btn:
            try:
                cursor = self.db.cursor()
                # Ensure we only delete from the current build!
                cursor.execute("DELETE FROM components WHERE Model = %s AND Build_ID = %s LIMIT 1",
                               (model_to_delete, active_build_id))
                self.db.commit()
                self.load_data()
            except mysql.connector.Error as err:
                QMessageBox.critical(self, "Error", f"Could not delete:\n{err}")

    def search_filter(self):
        search_text = self.searchInput.text().lower()
        for row in range(self.partsTable.rowCount()):
            model_text = self.partsTable.item(row, 0).text().lower()
            cat_text = self.partsTable.item(row, 1).text().lower()
            if search_text in model_text or search_text in cat_text:
                self.partsTable.setRowHidden(row, False)
            else:
                self.partsTable.setRowHidden(row, True)

    def export_csv(self):
        active_build_name = self.buildSelector.currentText()
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Database", f"{active_build_name}_Export.csv",
                                                  "CSV Files (*.csv)")
        if filepath:
            try:
                with open(filepath, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Model", "Category", "Condition", "Price (PHP)", "Date Added"])
                    for row in range(self.partsTable.rowCount()):
                        row_data = [self.partsTable.item(row, col).text() for col in range(5)]
                        writer.writerow(row_data)
                QMessageBox.information(self, "Success", "Database exported successfully to CSV!")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def nuke_database(self):
        active_build_id = self.buildSelector.currentData()
        msg = QMessageBox(self)
        msg.setWindowTitle('WARNING')
        msg.setText('This will clear all components from the CURRENT build. Proceed?')
        msg.setIcon(QMessageBox.Critical)
        yes_btn = msg.addButton("Yes (Clear Build)", QMessageBox.YesRole)
        yes_btn.setStyleSheet("background-color: #C2847A; color: white;")
        no_btn = msg.addButton("No (Cancel)", QMessageBox.NoRole)
        no_btn.setStyleSheet("background-color: #8C9B86; color: white;")
        msg.exec_()

        if msg.clickedButton() == yes_btn:
            cursor = self.db.cursor()
            cursor.execute("DELETE FROM components WHERE Build_ID = %s", (active_build_id,))
            self.db.commit()
            self.load_data()

    def logout(self):
        msg = QMessageBox(self)
        msg.setWindowTitle('Logout')
        msg.setText('Are you sure you want to securely log out?')
        msg.setIcon(QMessageBox.Question)
        yes_btn = msg.addButton("Yes", QMessageBox.YesRole)
        yes_btn.setStyleSheet("background-color: #C2847A; color: white;")
        no_btn = msg.addButton("Cancel", QMessageBox.NoRole)
        no_btn.setStyleSheet("background-color: #8C9B86; color: white;")
        msg.exec_()

        if msg.clickedButton() == yes_btn:
            self.login_window = LoginApp()
            self.login_window.show()
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(ACOUSTIC_THEME)
    window = LoginApp()
    window.show()
    sys.exit(app.exec_())
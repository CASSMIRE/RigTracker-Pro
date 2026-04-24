# 🖥️ RigTracker Pro

RigTracker Pro is a powerful, Object-Oriented desktop application designed for PC builders, enthusiasts, and students. It replaces messy spreadsheets by providing a clean, multi-workspace dashboard to track hardware components, monitor budgets, and plan multiple PC builds simultaneously. 

Built with **Python (PyQt5)** and powered by a relational **MySQL database**, this application serves as a comprehensive portfolio piece demonstrating GUI development, secure authentication, file handling, and relational data management.

## ✨ Features
* **Multi-Build Workspaces:** Plan a "Budget 1080p Rig" and a "Dream 4K Build" at the same time. Parts are saved to specific workspaces using MySQL Foreign Keys.
* **Clean Studio Interface:** Features a minimalist, highly readable "Acoustic Studio" aesthetic built with custom Qt Style Sheets (QSS).
* **Secure Authentication:** Built-in login screen to keep your hardware budgets private.
* **Automated Time-Tracking:** Database-side timestamps automatically log exactly when parts were added to the build.
* **CSV Data Export:** Instantly export any build's data to a `.csv` file for external analysis in Excel or Google Sheets.
* **Live Search & Filter:** Instantly find specific components in massive build lists.

## 🛠️ Prerequisites
Before running RigTracker Pro, ensure you have the following installed on your machine:
* **Python 3.8+**
* **XAMPP** (or any local MySQL server)

You will also need to install the required Python libraries. Open your terminal and run:
`pip install PyQt5 mysql-connector-python`

## 🚀 Installation & Database Setup
Because this app relies on a relational database, you must configure your local MySQL server before running the Python script.

**1. Set up the Database**
1. Open XAMPP and start the **Apache** and **MySQL** modules.
2. Click **Admin** next to MySQL to open phpMyAdmin.
3. Create a new database named `rigtracker_db`.
4. Click the **SQL** tab and run the following master setup script to create the relational tables:

```sql
-- Create the Builds table
CREATE TABLE builds (
    Build_ID INT AUTO_INCREMENT PRIMARY KEY,
    Build_Name VARCHAR(255) NOT NULL,
    Date_Created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the Components table
CREATE TABLE components (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    Model VARCHAR(255) NOT NULL,
    Category VARCHAR(100) NOT NULL,
    ItemCondition VARCHAR(50) NOT NULL,
    BasePrice DECIMAL(10, 2) NOT NULL,
    Build_ID INT,
    Date_Added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_build FOREIGN KEY (Build_ID) REFERENCES builds(Build_ID) ON DELETE CASCADE
);

-- Create the default startup workspace
INSERT INTO builds (Build_Name) VALUES ('My First Rig');

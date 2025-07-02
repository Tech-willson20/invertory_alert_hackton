# Citsa Inventory Management System

A Django-based inventory management system for supermarkets and retail stores.  
This project tracks products, manages sales, monitors stock levels, and provides restock alerts with predictive analytics.

---

## Features

- **Product Management:**  
  Add, update, and track products with unique SKUs and categories.

- **Sales Tracking:**  
  Record sales transactions and automatically update product stock.

- **Inventory Alerts:**  
  Receive alerts when product stock falls below a configurable threshold.

- **Restock Prediction:**  
  Estimate when a product will need restocking based on average sales rates.

---

## Getting Started

### Prerequisites

- Python 3.10+
- Django 4.x+
- SQLite (default, or configure your own database)

### Installation

1. **Clone the repository:**
    ```sh
    git clone https://github.com/NharnahQwami/citsa_inventory.git
    cd citsa_inventory
    ```

2. **Create and activate a virtual environment:**
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4. **Apply migrations:**
    ```sh
    python manage.py migrate
    ```

5. **(Optional) Load sample data:**
    ```sh
    python add_sample_data.py
    ```

6. **Run the development server:**
    ```sh
    python manage.py runserver
    ```

---

## Usage

- Access the admin panel at `http://localhost:8000/admin` to manage products and sales.
- The system will automatically update stock and trigger alerts when stock is low.
- Restock predictions are available in the dashboard or via API (if implemented).

---

## Project Structure

- `inventory/` — Django app with models, views, and business logic
- `add_sample_data.py` — Script to populate the database with sample products and sales
- `requirements.txt` — Python dependencies

---

## License

[MIT](LICENSE)
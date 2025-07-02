import os
import django
from django.db import transaction
from datetime import date, timedelta
import random

# Set up Django environment
# IMPORTANT: Replace 'inventory_project.settings' with your actual project's settings path if different.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_project.settings')
django.setup()

# Import your models from your Django app
# IMPORTANT: Replace 'inventory' with your actual app name if different.
from inventory.models import Product, Sale

# --- Extended List of Diverse Supermarket Items (Approx. 100 items) ---
# This list combines previous Ghanaian supermarket items with additional diverse products
# to reach approximately 100 unique items.
all_supermarket_items = [
    # Food & Beverages (Staples & Groceries)
    'Perfumed Rice 5kg', 'Local Rice 5kg', 'Palm Oil 2L', 'Vegetable Oil 2L',
    'Sugar 1kg', 'Salt 500g', 'Wheat Flour 1kg', 'Bread (Sliced, Wholemeal)', 'Fresh Eggs (Crate)',
    'Powdered Milk 400g', 'Evaporated Milk 170g', 'Canned Sardines', 'Canned Mackerel',
    'Tomato Paste 70g (Sachet)', 'Maggi Cubes (Pack)', 'Curry Powder', 'Ground Pepper (Shito)',
    'Tea Bags (Box)', 'Coffee Sachets', 'Milo Powder 400g', 'Ovaltine Powder 400g',
    'Cornflakes 500g', 'Oats 500g', 'Indomie Noodles (Pack)', 'Gari (Cassava Flour) 1kg',
    'Banku Mix 1kg', 'Kenkey Flour 1kg', 'Groundnuts 200g', 'Plantain Chips (Pack)',
    'Biscuits (Assorted Pack)', 'Custard Powder', 'Semolina Flour 500g', 'Spaghetti 500g',
    'Baked Beans (Canned)', 'Tin Tomatoes (Large)', 'Bottled Water 1.5L', 'Coca-Cola 500ml',
    'Fanta 500ml', 'Sprite 500ml', 'Maltina 330ml', 'Club Beer 330ml', 'Star Beer 330ml',
    'Pineapple Juice 1L', 'Mango Juice 1L', 'Ketchup 500ml', 'Mayonnaise 400g',
    'Honey 250g', 'Jam (Strawberry)', 'Peanut Butter 300g', 'Breakfast Cereal (Choco-pops)',
    'Frozen Chicken Parts 1kg', 'Fresh Fish (Tilapia)', 'Yoghurt (Mixed Berry)', 'Cheese Slices',
    'Butter 250g', 'Fresh Apples (Bag)', 'Oranges (Net)', 'Bananas (Bunch)', 'Onions 1kg',
    'Garlic (Head)', 'Ginger 200g', 'Tomatoes 1kg', 'Hot Pepper 100g', 'Garden Eggs (Pack)',
    'Okra (Pack)', 'Cabbage (Whole)', 'Carrots 500g', 'Potatoes 1kg', 'Sweet Potatoes 1kg',
    'Canned Sweet Corn', 'Dried Mushrooms 100g', 'Soy Sauce 250ml', 'Vinegar 500ml',
    'Olive Oil 500ml', 'Aglio e Olio Pasta Sauce',

    # Household & Cleaning
    'Toilet Soap (Bar, Large)', 'Laundry Bar Soap (Ariel)', 'Washing Powder 1kg (Omo)',
    'Dishwashing Liquid 500ml (Joy)', 'Disinfectant 1L (Dettol)', 'Bleach 1L (Parazone)',
    'Toilet Roll (4-Pack, Soft)', 'Paper Towels (Large Roll)', 'Kitchen Sponge (3-Pack)',
    'Scourer Pad (Metal)', 'Insecticide Spray (Raid)', 'Air Freshener (Lavender)', 'Matches (Box)',
    'Candles (Pack, White)', 'Dustbin Bags (Roll, Large)', 'Mop Head (Cotton)',
    'Bucket (Plastic, 10L)', 'Broom (Local)', 'Brush & Dustpan Set', 'Clothes Pegs (Pack, 20)',
    'Aluminum Foil (Large Roll)', 'Cling Film (Standard)', 'Food Storage Containers (Set of 3)',
    'Floor Cleaner 1L', 'Glass Cleaner 500ml', 'Washing Machine Cleaner', 'Pest Trap (Sticky)',

    # Personal Care & Toiletries
    'Toothpaste 100ml (Close-Up)', 'Toothbrush (Adult, Medium)', 'Body Lotion 200ml (Nivea)',
    'Hair Cream (Shea Butter)', 'Shampoo 200ml (Sunsilk)', 'Conditioner 200ml (Sunsilk)',
    'Sanitary Pads (Pack, Maxi)', 'Baby Diapers (Small Pack, Size 3)', 'Baby Powder 200g',
    'Petroleum Jelly 100g', 'Deodorant Spray (Rexona)', 'Roll-On Deodorant (Dove)',
    'Hand Sanitizer 100ml', 'Cotton Buds (Box)', 'Face Wash 150ml', 'Lip Balm',

    # Miscellaneous
    'AA Batteries (4-Pack)', 'AAA Batteries (4-Pack)', 'Light Bulb (LED, 9W)', 'Extension Cable (5m)',
    'Super Glue (Small Tube)', 'Notebook (A4, 100 pages)', 'Pen (Blue/Black, Pack)', 'Pencil (HB, Pack)',
    'Eraser (Large)', 'Tape Measure (3m)', 'Scissors (Small)', 'Flashlight (Mini)',
    'Phone Charger (Universal)', 'Headphones (Earbuds)', 'Disposable Razors (Pack)',
    'Rubbing Alcohol 100ml', 'First Aid Box (Basic)', 'Hand Soap (Liquid, Refill)'
]

def generate_sku(product_name):
    """
    Generates a simple SKU from the product name.
    It takes the first 3 letters of the first two words, plus a random 3-digit number.
    Ensures SKUs are reasonably unique for a large set.
    """
    words = product_name.replace('-', ' ').split(' ') # Replace hyphens for better word splitting
    sku_prefix_parts = []
    # Take up to 3 characters from each of the first two words
    if len(words) >= 1:
        sku_prefix_parts.append(words[0][:3].upper())
    if len(words) >= 2:
        sku_prefix_parts.append(words[1][:3].upper())
    elif len(words) == 1: # If only one word, just use that word's prefix
         sku_prefix_parts.append(words[0][-3:].upper()) # Last 3 chars if only one word

    sku_prefix = ''.join(sku_prefix_parts).ljust(6, 'X') # Pad to at least 6 chars with 'X'
    return f"{sku_prefix}_{random.randint(100, 999)}_{random.randint(10, 99)}" # Add more randomness

def create_sample_supermarket_data():
    """
    Generates and populates the database with 100 unique product items
    and associated sales data. Clears existing data first.
    """
    print("--- Starting data generation for 100 supermarket items ---")

    # Clear existing products and sales to avoid duplicates on rerun
    # Use transaction.atomic() for data integrity to ensure all deletions/creations
    # happen as a single, atomic operation.
    with transaction.atomic():
        Sale.objects.all().delete()
        Product.objects.all().delete()
        print("Cleared existing sales and products from the database.")

        # Create sample products from the extended supermarket items list
        created_products = []
        # We need exactly 100 items. If the list is shorter, repeat or extend.
        # Here, we ensure we use up to the length of the list, assuming it's around 100.
        items_to_create = all_supermarket_items[:100] # Cap at 100 items if list is longer, or use all if shorter

        for i, item_name in enumerate(items_to_create):
            # Ensure unique SKU
            unique_sku = generate_sku(item_name)
            # Add a counter to the SKU to make it highly unique, especially if product names repeat slightly
            unique_sku = f"{unique_sku}_{i:03d}"

            # Set random initial stock and low stock threshold
            initial_stock = random.randint(20, 300) # Supermarket items can have higher stock
            low_threshold = random.randint(5, 50)
            if low_threshold >= initial_stock: # Ensure threshold is always less than initial stock
                low_threshold = initial_stock // 2 if initial_stock > 1 else 1

            product, created = Product.objects.get_or_create(
                name=item_name, # Use name for get_or_create to avoid creating duplicates by name
                defaults={
                    'sku': unique_sku,
                    'current_stock': initial_stock,
                    'low_stock_threshold': low_threshold
                }
            )
            if created:
                print(f"Created product: {product.name} (SKU: {product.sku}, Stock: {product.current_stock})")
            else:
                # If product already exists by name (shouldn't happen after clearing, but good practice)
                # update its details or skip. Here, we update.
                print(f"Product '{product.name}' already exists, updating details.")
                product.sku = unique_sku
                product.current_stock = initial_stock
                product.low_stock_threshold = low_threshold
                product.save()
            created_products.append(product)

        print(f"\n--- Created {len(created_products)} unique products. Now generating sales. ---")

        # Create sample sales for the newly created products
        for product in created_products:
            # Create some random sales over the last 90 days for more varied data
            num_sales_per_product = random.randint(5, 20) # Vary the number of sales per product

            for _ in range(num_sales_per_product):
                sale_date = date.today() - timedelta(days=random.randint(1, 90)) # Sales over last 3 months
                quantity = random.randint(1, 15) # Vary sale quantities, up to 15 units per sale

                # Only create sale if we have enough stock. This simulates real sales.
                if product.current_stock >= quantity:
                    Sale.objects.create(
                        product=product,
                        quantity=quantity,
                        date=sale_date
                    )
                    if product.current_stock < 0:
                        product.current_stock = 0  # Prevent negative stock
                        product.save()
                else:
                    # print(f"  - Skipped sale for {product.name} due to insufficient stock ({product.current_stock} available, tried to sell {quantity}).")
                    pass # Keep print messages minimal for large loops

    print("\n--- Sample data generation completed successfully! ---")
    print(f"Total products created: {Product.objects.count()}")
    print(f"Total sales created: {Sale.objects.count()}")

# Execute the function when the script is run directly
if __name__ == '__main__':
    create_sample_supermarket_data()

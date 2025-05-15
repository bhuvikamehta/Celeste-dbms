from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'imaokayy1'

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Mangaf1617",
    database="CELESTE"
)
cursor = db.cursor(dictionary=True)

# @app.route('/')
# def index():
#     return redirect(url_for('login'))

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route('/homepage')
def homepage():
    cursor.execute("""SELECT 
    p.Product_ID, 
    p.Product_Name, 
    COUNT(o.Product_ID) AS Order_Count, 
    SUM(o.Quantity) AS Total_Quantity_Sold
FROM All_Orders o
JOIN Order_History oh ON o.Order_ID = oh.Order_ID
JOIN Product p ON o.Product_ID = p.Product_ID
WHERE DATE(oh.Date_of_Ordering) BETWEEN DATE_SUB('2024-12-15', INTERVAL 7 DAY) AND '2024-12-15'
GROUP BY p.Product_ID, p.Product_Name
ORDER BY Total_Quantity_Sold DESC
LIMIT 5;
""")
    best_selling=cursor.fetchall()
    print(best_selling)

    return render_template('homepage.html', best_selling=best_selling)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']  # ✅ using email
        password = request.form['password']

        cursor.execute("SELECT * FROM Customer WHERE Email_ID = %s AND Password = %s", (email, password))
        user = cursor.fetchone()
        if user:
            session['user_id'] = user['Customer_ID']
            session['user_name'] = user['Name']
            flash("Logged in successfully!", "success")
            return redirect(url_for('homepage'))  
        else:
            flash("Invalid email or password", "danger")
            return redirect(url_for('login'))

    return render_template('login_signup.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['username']
        email = request.form['email']
        password = request.form['password']
        gender = request.form.get('gender')
        phone = request.form['mobile']
        address = request.form.get('address')
        dob = request.form.get('dob')

        try:
            cursor.execute("""
                INSERT INTO Customer (Name, Email_ID, Password, Gender, Phone_Number, Address, Date_of_Birth)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name, email, password, gender, phone, address, dob))
            db.commit()
            flash("Signup successful! Please log in.", "success")
            return redirect(url_for('login'))
        except mysql.connector.Error as e:
            flash(f"Error: {e.msg}", "danger")
            return redirect(url_for('login'))
    return render_template('login_signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/homepage/cart")
def cart():
    cursor.execute("SELECT * FROM Cart WHERE Customer_ID = %s", (session.get("user_id"),))
    cart_items = cursor.fetchall()
    return render_template('cart.html', cart_items=cart_items)

@app.route("/homepage/cart/pay")
def pay():
    return render_template('pay.html')

@app.route("/homepage/past-orders")
def past_orders():
    return render_template('past_orders.html')

@app.route("/homepage/profile")
def profile():
    return render_template('profile.html')

# @app.route("/homepage/category<string:category>")
# def show_prod(category):
#     cursor.execute("SELECT * FROM Product WHERE Category = %s", (category,))
#     data = cursor.fetchall()
#     return render_template('show_prod.html',data=data)
# @app.route("/homepage/category<string:category>")
# def show_prod(category):
#     sort_option = request.args.get('sort', None)

#     base_query = "SELECT * FROM Product WHERE Category = %s"
#     params = [category]

#     if sort_option == "Price - Low to High":
#         base_query += " ORDER BY Price ASC"
#     elif sort_option == "Price - High to Low":
#         base_query += " ORDER BY Price DESC"
#     elif sort_option == "Gender - Male":
#         base_query += " AND Gender = 'Male'"
#     elif sort_option == "Gender - Female":
#         base_query += " AND Gender = 'Female'"
#     # Add more conditions for Color or Promotion if those fields exist in your Product table

#     cursor.execute(base_query, params)
#     data = cursor.fetchall()
    
#     print(data)
#     print(data[0]['Product_ID'])
#     return render_template('show_prod.html', data=data)

@app.route("/homepage/category/<string:category>")
def show_prod(category):
    sort_option = request.args.get("sort")
    base_query = "SELECT * FROM Product WHERE stock_quantity>0 and Category = %s"
    params = [category]

    if sort_option == "Price - Low to High":
        base_query += " ORDER BY Price ASC"
    elif sort_option == "Price - High to Low":
        base_query += " ORDER BY Price DESC"
    elif sort_option == "Gender - Male":
        base_query += " AND Gender = 'Male'"
    elif sort_option == "Gender - Female":
        base_query += " AND Gender = 'Female'"

    cursor.execute(base_query, params)
    data = cursor.fetchall()
    

    return render_template('show_prod.html', data=data, category=category)

@app.route("/homepage/products/info/<int:product_id>")
def product_info(product_id):
    cursor.execute("SELECT * FROM product WHERE product_id = %s", (product_id,))
    data=cursor.fetchone()
    cursor.execute("SELECT * FROM REVIEW WHERE PRODUCT_ID =%s", (product_id,))
    reviews=cursor.fetchall()
    return render_template('product_info.html', data=data, reviews=reviews)

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    product_id = request.form["product_id"]
    # Example hard-coded user ID & quantity
    user_id = session.get("user_id")  # Assuming user is logged in, replace with actual user ID  
    quantity = 1

    query = """
    INSERT INTO Cart (Product_ID, Customer_ID, Quantity, Price)
    SELECT %s, %s, %s,
           P.Price * (1 - IFNULL(PR.Discount_Percentage, 0) / 100) AS Discounted_Price
    FROM Product P
    LEFT JOIN Promotion PR ON P.Product_ID = PR.Product_ID
         AND CURRENT_DATE BETWEEN PR.Start_Date AND PR.End_Date
    WHERE P.Product_ID = %s
    """
    cursor.execute(query, (product_id, user_id, quantity, product_id))
    db.commit()

    flash("Product added to cart!")
    return redirect(url_for("product_info", product_id=product_id))

#  Dummy Home Page Route
# @app.route('/home')
# def home():
#     if 'user_id' in session:
#         return f"Welcome, {session['user_name']}! <br><a href='/logout'>Logout</a>"
#     return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
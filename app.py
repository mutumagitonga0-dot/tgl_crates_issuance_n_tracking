from flask import Flask, request, render_template_string
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import create_engine, text
#import pyodbc
from datetime import datetime,timezone
from flask import redirect, url_for, flash
import os


#conn = pyodbc.connect(
#    "DRIVER={ODBC Driver 17 for SQL Server};"
#    "SERVER=TOSHIBA\\SQLEXP2014;"
#    "DATABASE=CrateTrackerDB;"
#    "UID=sa;"
#    "PWD=CMos@2019"
#)
#print("Connected!")


app = Flask(__name__)
app.secret_key = "super_secret_key"  # required for flash/session


# Prefer DATABASE_URL if set (Render/Postgres)
db_url = os.environ.get("DATABASE_URL")

if db_url:
    # Render/Postgres connection
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    # Local fallback (SQL Server via pyodbc)
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        "mssql+pyodbc:///?odbc_connect="
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=TOSHIBA\\SQLEXP2014;"
        "DATABASE=CrateTrackerDB;"
        "UID=sa;"
        "PWD=CMos@2019"
    )

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Optional external DB connection (use env var EXTERNAL_DB_URL on Render)
external_db_url = os.environ.get("EXTERNAL_DB_URL")
if external_db_url:
    external_engine = create_engine(external_db_url)
else:
    # Local fallback external SQL Server
    external_engine = create_engine(
        "mssql+pyodbc:///?odbc_connect="
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=tundagreen.aceplasticsafrica.com;"
        "DATABASE=ACELIVEDATA;"
        "UID=Usertunda;"
        "PWD=Tunda@2024"
    )



#app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crates.db'

#app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc://sa:CMos@2019@CrateTrackerDSN"

#app.config['SQLALCHEMY_DATABASE_URI'] = (
#    "mssql+pyodbc://sa:CMos@2019@TOSHIBA,49723/CrateTrackerDB"
#    "?driver=ODBC Driver 17 for SQL Server"
#)

#external_engine = create_engine(os.environ.get('DATABASE_URL'))

#app.config['SQLALCHEMY_DATABASE_URI'] =(
#    "mssql+pyodbc:///?odbc_connect="
#    "DRIVER={ODBC Driver 17 for SQL Server};"
#    "SERVER=TOSHIBA\\SQLEXP2014;"
#    "DATABASE=CrateTrackerDB;"
#    "UID=sa;"
#    "PWD=CMos@2019")

# External DB connection (adjust credentials)
#external_engine = create_engine(
#    "mssql+pyodbc:///?odbc_connect="
#    "DRIVER={ODBC Driver 17 for SQL Server};"
#    "SERVER=tundagreen.aceplasticsafrica.com;"
#    "DATABASE=ACELIVEDATA;"
#    "UID=Usertunda;"
#    "PWD=Tunda@2024"
#)


#app.config['SQLALCHEMY_DATABASE_URI'] = (
#  "mssql+pyodbc://sa:CMos@2019@TOSHIBA\\SQLEXP2014/CrateTrackerDB"
#  "?driver=ODBC+Driver+17+for+SQL+Server")

#print("SQLAlchemy URI:", app.config['SQLALCHEMY_DATABASE_URI'])

#app.config['SQLALCHEMY_DATABASE_URI'] = (
#    "mssql+pyodbc://sa:CMos@2019@TOSHIBA\\SQLEXP2014/CrateTrackerDB"
#    "?driver=ODBC Driver 17 for SQL Server"
#)

#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#db = SQLAlchemy(app)

# --- Models ---
class Outlet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    #location = db.Column(db.String(200))

class Dispatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    #outlet_id = db.Column(db.Integer, db.ForeignKey('outlet.id'), nullable=False)
    outlet_name = db.Column(db.String(100), nullable=False)
    crates_sent = db.Column(db.Integer, nullable=False)
    #staff_id = db.Column(db.String(50), nullable=False)
    staff_name = db.Column(db.String(100), nullable=False)
    #dispatch_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    dispatch_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class Collection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    #outlet_id = db.Column(db.Integer, db.ForeignKey('outlet.id'), nullable=False)
    outlet_name = db.Column(db.String(100), nullable=False)
    crates_collected = db.Column(db.Integer, nullable=False)
    #staff_id = db.Column(db.String(50), nullable=False)
    staff_name = db.Column(db.String(100), nullable=False)
    #collection_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    collection_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    

class Warehouse(db.Model):
    __tablename__ = "warehouse"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    total_crates = db.Column(db.Integer, nullable=False, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WarehouseTransaction(db.Model):
    __tablename__ = "warehouse_transactions"
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouse.id"), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)  # purchase, loss, adjustment, audit
    crates = db.Column(db.Integer, nullable=False)  # positive or negative
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    warehouse = db.relationship("Warehouse", backref=db.backref("transactions", lazy=True))

    
# --- Layout Template with Navbar ---
layout = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Crate Tracker</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="container mt-4">

  <!-- Flash messages -->
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      {% for category, message in messages %}
        <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
          {{ message }}
          <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
      {% endfor %}
    {% endif %}
  {% endwith %}

  <!-- Navigation Bar -->
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
    <div class="container-fluid">
      <a class="navbar-brand" href="/">📦 Crate Tracker</a>
      <div class="collapse navbar-collapse">
        <ul class="navbar-nav me-auto">
          <li class="nav-item"><a class="nav-link" href="/">Home</a></li>
          <li class="nav-item"><a class="nav-link" href="/dashboard">Dashboard</a></li>
          <li class="nav-item"><a class="nav-link" href="/dispatch">Dispatch</a></li>
          <li class="nav-item"><a class="nav-link" href="/collect">Collection</a></li>
          <li class="nav-item"><a class="nav-link" href="/manage_users">Manage Users</a></li>
        </ul>
      </div>
    </div>
  </nav>

  {{ content|safe }}
</body>
</html>
"""

# --- Reusable Home Button ---
home_button = "<a href='/' class='btn btn-secondary mt-3'>⬅️ Return to Home</a>"

# --- Forms ---
dispatch_form = f"""
<form method="post" class="card p-3">
  <h2>Record Dispatch</h2>
  <div class="mb-3">
    <label class="form-label">Outlet ID</label>
    <input type="number" name="outlet_id" class="form-control" required>
  </div>
  <div class="mb-3">
    <label class="form-label">Crates Sent</label>
    <input type="number" name="crates_sent" class="form-control" required>
  </div>
  <div class="mb-3">
    <label class="form-label">Staff ID</label>
    <input type="text" name="staff_id" class="form-control" required>
  </div>
  <button type="submit" class="btn btn-success">Submit</button>
</form>
{home_button}
"""

collection_form = f"""
<form method="post" class="card p-3">
  <h2>Record Collection</h2>
  <div class="mb-3">
    <label class="form-label">Outlet ID</label>
    <input type="number" name="outlet_id" class="form-control" required>
  </div>
  <div class="mb-3">
    <label class="form-label">Crates Collected</label>
    <input type="number" name="crates_collected" class="form-control" required>
  </div>
  <div class="mb-3">
    <label class="form-label">Staff ID</label>
    <input type="text" name="staff_id" class="form-control" required>
  </div>
  <button type="submit" class="btn btn-warning">Submit</button>
</form>
{home_button}
"""

add_user_form = f"""
<form method="post" class="card p-3">
  <h2>Add New Staff</h2>
  <div class="mb-3">
    <label class="form-label">User Name</label>
    <input type="text" name="name" class="form-control" required>
  </div>
  <div class="mb-3">
    <label class="form-label">Location</label>
    <input type="text" name="location" class="form-control">
  </div>
  <button type="submit" class="btn btn-primary">Add User</button>
</form>
{home_button}
"""


# --- Routes ---
@app.route("/")
def home():
    # Step 1: Get distinct outlet names from Dispatch table
    distinct_outlets = db.session.query(Dispatch.outlet_name).distinct().all()

    # Step 2: Insert them into Outlet table if not already present
    for (outlet_name,) in distinct_outlets:
        if outlet_name:  # skip nulls
            existing = Outlet.query.filter_by(name=outlet_name).first()
            if not existing:
                new_outlet = Outlet(name=outlet_name)
                db.session.add(new_outlet)

    db.session.commit()

    outlets = Outlet.query.all()
    rows = ""

    for o in outlets:
  
      #dispatched = db.session.query(db.func.sum(Dispatch.crates_sent)).filter_by(outlet_id=o.id).scalar() or 0
      dispatched = db.session.query(db.func.sum(Dispatch.crates_sent)).filter_by(outlet_name=o.name).scalar() or 0
      #collected = db.session.query(db.func.sum(Collection.crates_collected)).filter_by(outlet_id=o.id).scalar() or 0
      collected = db.session.query(db.func.sum(Collection.crates_collected)).filter_by(outlet_name=o.name).scalar() or 0
      variance = dispatched - collected
      color = "table-danger" if variance > 0 else "table-success"
      rows += f"<tr><td>{o.name}</td><td>{dispatched}</td><td>{collected}</td><td class='{color}'>{variance}</td></tr>"

    #summary_table = f"""
    ##<h2>Outlet Summary</h2>
    #<table class="table table-bordered">
    #  <thead><tr><th>Outlet</th><th>Dispatched</th><th>Collected</th><th>Variance</th></tr></thead>
    #  <tbody>{rows}</tbody>
    #</table>
    #"""

    # Warehouse total crates (assuming you track in Warehouse table)
      #warehouse_total = db.session.query(db.func.sum(Warehouse.crates)).scalar() or 0
      warehouse_total = db.session.query(db.func.sum(Warehouse.total_crates)).scalar() or 0



      # Total dispatched to outlets
      total_sent = db.session.query(db.func.sum(Dispatch.crates_sent)).scalar() or 0

      # Total collected back from outlets
      total_received = db.session.query(db.func.sum(Collection.crates_collected)).scalar() or 0

      # Variance between sent and received
      variance = total_sent - total_received

      # Current warehouse balance (original stock - sent + received)
      current_balance = warehouse_total - total_sent + total_received
    summary_table = f"""
    <div class="border p-3 mb-3 rounded bg-info bg-opacity-25">
      <h4 class="text-center">📊 Main Warehouse Summary</h4>
      <table class="table table-bordered table-striped">
        <thead class="table-light">
          <tr>
            <th>Metric</th>
            <th>Crates</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Total Crates in Warehouse</td>
            <td>{warehouse_total}</td>
          </tr>
          <tr>
            <td>Total Issued to Outlets</td>
            <td>{total_sent}</td>
          </tr>
          <tr>
            <td>Total Received Back</td>
            <td>{total_received}</td>
          </tr>
          <tr class="table-warning">
            <td>Variance (Issued - Received)</td>
            <td>{variance}</td>
          </tr>
          <tr class="table-success">
            <td>Current Warehouse Balance</td>
            <td>{current_balance}</td>
          </tr>
        </tbody>
      </table>
    </div>
    """


    shortcuts = """
    <div class="d-grid gap-3 mb-4">
      <a href="/dispatch" class="btn btn-success btn-lg">➕ Record Dispatch</a>
      <a href="/collect" class="btn btn-warning btn-lg">📥 Record Collection</a>
      <a href="/dashboard" class="btn btn-primary btn-lg">📋 View All Outlets Dashboard</a>
      <a href="/reconcile/1" class="btn btn-info btn-lg">📊 Reconcile Outlet 1</a>
      <a href="/manage_users" class="btn btn-dark btn-lg">🏬 Manage Users</a>
    </div>
    """

    content = shortcuts + summary_table
    return render_template_string(layout, content=content)

def retrieve_outlets():
  # Step 1: Fetch branch names from external DB
  with external_engine.connect() as conn:
    result = conn.execute(text("select [BranchName] from [Tunda Green Limited$Dimension2$69b6b001-139b-4a64-a385-4bc69d6bb6a5]"))
    outlets = [row.BranchName for row in result]
  return outlets

def retrieve_users_external():
  with db.engine.connect() as conn:
    result = conn.execute(text("SELECT username FROM users"))
    users = [row.username for row in result]
  return users

def retrieve_offline_users():
  users = Users.query.all()  # returns list of User objects
  usernames = [u.username for u in users]  # extract usernames
  print("DEBUG: usernames =", usernames)
  return usernames

def add_purchase(warehouse_id, crates, description=""):
    txn = WarehouseTransaction(
        warehouse_id=warehouse_id,
        transaction_type="purchase",
        crates=crates,
        description=description
    )
    warehouse = Warehouse.query.get(warehouse_id)
    if warehouse:
        warehouse.total_crates += crates
    db.session.add(txn)
    db.session.commit()

def record_loss(warehouse_id, crates, description="Damaged crates"):
    txn = WarehouseTransaction(
        warehouse_id=warehouse_id,
        transaction_type="loss",
        crates=-crates,
        description=description
    )
    warehouse = Warehouse.query.get(warehouse_id)
    if warehouse:
        warehouse.total_crates -= crates
    db.session.add(txn)
    db.session.commit()

@app.route("/dispatch", methods=["GET", "POST"])
def record_dispatch():
    # Step 1: Fetch branch names from external DB or helper
    outlets = retrieve_outlets()
    Users = retrieve_offline_users()

    # Step 2: Build the form HTML dynamically
    options_html = "".join([f'<option value="{o}">{o}</option>' for o in outlets])
    users_html = "".join([f'<option value="{o}">{o}</option>' for o in Users])

    dispatch_form = f"""
    <form method="post" class="card p-3"
          onsubmit="if (!confirm('Do you want to proceed dispatching ' 
          + document.querySelector('[name=crates_sent]').value 
          + ' crates to outlet ' 
          + document.querySelector('[name=outlet_name]').value 
          + ' by staff ' 
          + document.querySelector('[name=staff_name]').value + '?')) {{
              document.querySelector('[name=cancelled]').value = 'true';
          }}
          return true;">
      <input type="hidden" name="cancelled" value="false">

      <h2>Record Dispatch</h2>
      <div class="mb-3">
        <label class="form-label">Outlet</label>
        <select name="outlet_name" class="form-select" required>
          {options_html}
        </select>
      </div>
      <div class="mb-3">
        <label class="form-label">Crates Left here</label>
        <input type="number" name="crates_sent" class="form-control" required>
      </div>
      <div class="mb-3">
        <label class="form-label">Incharge (Staff Name)</label>
        <select name="staff_name" class="form-select" required>
          {users_html}
        </select>
      </div>
      <button type="submit" class="btn btn-primary">Submit Dispatch</button>
    </form>
    {home_button}
    """

    # Step 3: Handle submission
    if request.method == "POST":
        # Cancelled by user
        if request.form.get("cancelled") == "true":
            flash("Submission cancelled by user.", "warning")
            return redirect(request.url)

        branchname = request.form.get("outlet_name")
        crates_sent = request.form.get("crates_sent")
        staff_name = request.form.get("staff_name")

        # Convert crates_sent safely
        try:
            crates_sent = int(crates_sent)
        except (TypeError, ValueError):
            crates_sent = 0

        # Ensure staff_name is a string
        staff_name = str(staff_name or "")

        # Validation: if crates = 0 or staff is missing, stop
        if crates_sent <= 0 or not staff_name:
            flash("Invalid submission: crates must be > 0 and staff name required.", "danger")
            return redirect(request.url)

        # Record dispatch
        new_dispatch = Dispatch(outlet_name=branchname,
                                crates_sent=crates_sent,
                                staff_name=staff_name,dispatch_date=datetime.now(timezone.utc))
        db.session.add(new_dispatch)
        db.session.commit()

        flash(f"Dispatch recorded: {crates_sent} crates sent to {branchname} by {staff_name}.", "success")
        return redirect(url_for("dashboard"))

    # Step 4: Render with your existing layout
    return render_template_string(layout, content=dispatch_form)

@app.route("/collect", methods=["GET", "POST"])
def record_collection():
    # Step 1: Fetch branch names from external DB or helper
    outlets = retrieve_outlets()
    Users = retrieve_offline_users()

    # Step 2: Build the form HTML dynamically
    options_html = "".join([f'<option value="{o}">{o}</option>' for o in outlets])
    users_html = "".join([f'<option value="{o}">{o}</option>' for o in Users])

    dispatch_form = f"""
    <form method="post" class="card p-3"
          onsubmit="if (!confirm('Do you want to proceed collecting ' 
          + document.querySelector('[name=crates_collected]').value 
          + ' crates from outlet ' 
          + document.querySelector('[name=outlet_name]').value 
          + ' by staff ' 
          + document.querySelector('[name=staff_name]').value + '?')) {{
              document.querySelector('[name=cancelled]').value = 'true';
          }}
          return true;">
      <input type="hidden" name="cancelled" value="false">

      <h2>Record Collection</h2>
      <div class="mb-3">
        <label class="form-label">Outlet</label>
        <select name="outlet_name" class="form-select" required>
          {options_html}
        </select>
      </div>
      <div class="mb-3">
        <label class="form-label">Crates Collected Here</label>
        <input type="number" name="crates_collected" class="form-control" required>
      </div>
      <div class="mb-3">
        <label class="form-label">Collected By(Staff Name)</label>
        <select name="staff_name" class="form-select" required>
          {users_html}
        </select>
      </div>
      <button type="submit" class="btn btn-primary">Submit Dispatch</button>
    </form>
    {home_button}
    """

    # Step 3: Handle submission
    if request.method == "POST":
        # Cancelled by user
        if request.form.get("cancelled") == "true":
            flash("Submission cancelled by user.", "warning")
            return redirect(request.url)

        branchname = request.form.get("outlet_name")
        crates_collected = request.form.get("crates_collected")
        staff_name = request.form.get("staff_name")

        # Convert crates_sent safely
        try:
            crates_collected = int(crates_collected)
        except (TypeError, ValueError):
            crates_collected = 0

        # Ensure staff_name is a string
        staff_name = str(staff_name or "")

        # Validation: if crates = 0 or staff is missing, stop
        if crates_collected <= 0 or not staff_name:
            flash("Invalid submission: crates must be > 0 and staff name required.", "danger")
            return redirect(request.url)

        # Record collection
        new_collection = Collection(outlet_name=branchname,
                                crates_collected=crates_collected,
                                staff_name=staff_name,collection_date=datetime.now(timezone.utc))
        db.session.add(new_collection)
        db.session.commit()

        flash(f"Collection recorded: {crates_collected} crates returned from {branchname} by {staff_name}.", "success")
        return redirect(url_for("dashboard"))

    # Step 4: Render with your existing layout
    return render_template_string(layout, content=dispatch_form)

#@app.route("/reconcile/<int:outlet_id>")
@app.route("/reconcile/<outlet_name>")
def reconcile_outlet(outlet_name):
    #dispatched = db.session.query(db.func.sum(Dispatch.crates_sent)).filter_by(outlet_id=outlet_id).scalar() or 0
    #collected = db.session.query(db.func.sum(Collection.crates_collected)).filter_by(outlet_id=outlet_id).scalar() or 0
    
    dispatched = db.session.query(db.func.sum(Dispatch.crates_sent)).filter_by(outlet_name=outlet_name).scalar() or 0
    collected = db.session.query(db.func.sum(Collection.crates_collected)).filter_by(outlet_name=outlet_name).scalar() or 0

    
    variance = dispatched - collected
    content = f"""
    <h2>Reconciliation for Outlet {outlet_name}</h2>
    <table class="table table-bordered">
      <tr><th>Dispatched</th><td>{dispatched}</td></tr>
      <tr><th>Collected</th><td>{collected}</td></tr>
      <tr class="table-{ 'danger' if variance>0 else 'success' }">
        <th>Variance</th><td>{variance}</td>
      </tr>
    </table>
    {home_button}
    """
    return render_template_string(layout, content=content)


@app.route("/dashboard")
def dashboard():
    # Get all outlet names from Dispatch and Collection
    dispatch_outlets = db.session.query(Dispatch.outlet_name).distinct()
    collection_outlets = db.session.query(Collection.outlet_name).distinct()

    # Union them together
    all_outlets = set([o[0] for o in dispatch_outlets] + [o[0] for o in collection_outlets])

    rows = ""
    for outlet_name in all_outlets:
        dispatched = db.session.query(db.func.sum(Dispatch.crates_sent))\
                               .filter_by(outlet_name=outlet_name).scalar() or 0
        collected = db.session.query(db.func.sum(Collection.crates_collected))\
                               .filter_by(outlet_name=outlet_name).scalar() or 0
        variance = dispatched - collected
        color = "table-danger" if variance > 0 else "table-success"
        rows += f"<tr><td>{outlet_name}</td><td>{dispatched}</td><td>{collected}</td><td class='{color}'>{variance}</td></tr>"

    content = f"""
    <h2>Outlet Dashboard</h2>
    <table class="table table-bordered">
      <thead><tr><th>Outlet</th><th>Dispatched</th><th>Collected</th><th>Variance</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    <a href="/" class="btn btn-secondary">Back to Home</a>
    """
    return render_template_string(layout, content=content)

@app.route("/dashboard")
def dashboard_out():
    outlets = Outlet.query.all()
    rows = ""
    for o in outlets:
        #dispatched = db.session.query(db.func.sum(Dispatch.crates_sent)).filter_by(outlet_id=o.id).scalar() or 0
        dispatched = db.session.query(db.func.sum(Dispatch.crates_sent)).filter_by(outlet_name=o.name).scalar() or 0
        #collected = db.session.query(db.func.sum(Collection.crates_collected)).filter_by(outlet_id=o.id).scalar() or 0
        collected = db.session.query(db.func.sum(Collection.crates_collected)).filter_by(outlet_name=o.name).scalar() or 0
        variance = dispatched - collected
        color = "table-danger" if variance > 0 else "table-success"
        rows += f"<tr><td>{o.name}</td><td>{dispatched}</td><td>{collected}</td><td class='{color}'>{variance}</td></tr>"

    content = f"""
    <h2>Outlet Dashboard</h2>
    <table class="table table-bordered">
      <thead><tr><th>Outlet</th><th>Dispatched</th><th>Collected</th><th>Variance</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    <a href="/" class="btn btn-secondary">Back to Home</a>
    """
    return render_template_string(layout, content=content)


@app.route("/manage_users", methods=["GET", "POST"])
def manage_users():
    #message = ""

    create_message = ""
    update_message = ""
    delete_message = ""

    if request.method == "POST":
        action = request.form.get("action")

        if action == "create":
          name = request.form.get("name")

          # Check if user already exists
          existing_user = Users.query.filter_by(username=name).first()
          if existing_user:
              create_message = f"User '{name}' already exists!"
          else:
              new_user = Users(username=name)
              db.session.add(new_user)
              db.session.commit()
              create_message = f"User '{name}' added successfully!"

        elif action == "update":
          existing_userid = request.form.get("username")
          print("DEBUG: existing_name =", existing_userid)
          new_name = request.form.get("new_name")
          print("DEBUG: new_name =", new_name)

          if not new_name:
            update_message = "New name is required."
          else:
            user = Users.query.get(existing_userid)
            #user = Users.query.filter_by(username=existing_name).first()
            print("DEBUG: user object =", user)
            if user:
                oldname=user.username
                user.username = new_name   # update the field directly
                db.session.commit()
                update_message = f"User '{oldname}' updated to '{new_name}' successfully!"
            else:
                update_message = "User not found."


        elif action == "delete":
            # Delete staff
            user_id = request.form.get("del_username")
            if not user_id:
              return
            user = Users.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
                delete_message = f"User '{user.username}' deleted successfully!"
            else:
                delete_message = "User not found."

    # Build forms dynamically
    #users = Users.query.all()
    #users=retrieve_users()
    #user_options = "".join([f"<option value='{u.id}'>{u.name}</option>" for u in users])
    users = Users.query.all()   # returns list of Users objects
    user_options = "".join([f"<option value='{u.id}'>{u.username}</option>" for u in users])


    manage_users_form = f"""
    <div class="card p-3">

      <!-- Create new staff -->
      <div class="border p-3 mb-3 rounded bg-light">
        <h5 class="text-center">➕ Add Staff</h5>
        <form method="post" 
              onsubmit="return confirm('Do you want to proceed creating user ' + document.querySelector('[name=name]').value + '?');">
          <input type="hidden" name="action" value="create">
          <div class="mb-3">
            <label class="form-label">User Name</label>
            <input type="text" name="name" class="form-control" required>
          </div>
          <div class="text-center">
            <button type="submit" class="btn btn-primary">Add User</button>
          </div>
          <p class="mt-2 text-success">{create_message}</p>
        </form>
      </div>

      <!-- Update staff -->
      <div class="border p-3 mb-3 rounded bg-warning bg-opacity-25">
        <h5 class="text-center">✏️ Update Staff</h5>
        <form method="post" 
          onsubmit="return confirm('Do you want to update user ' + document.querySelector('[name=username]').options[document.querySelector('[name=username]').selectedIndex].text + ' to ' + document.querySelector('[name=new_name]').value + '?');">
          <input type="hidden" name="action" value="update">
          <div class="mb-3">
            <label class="form-label">Select User</label>
            <select name="username" class="form-select">{user_options}</select>
          </div>
          <div class="mb-3">
            <label class="form-label">New Name</label>
            <input type="text" name="new_name" class="form-control" required>
          </div>
          <div class="text-center">
            <button type="submit" class="btn btn-warning">Update User</button>
          </div>
          <p class="mt-2 text-success">{update_message}</p>
        </form>
      </div>

      <!-- Delete staff -->
      <div class="border p-3 mb-3 rounded bg-danger bg-opacity-25">
        <h5 class="text-center">🗑️ Delete Staff</h5>
        <form method="post" 
              onsubmit="return confirm('Are you sure you want to delete user ' + document.querySelector('[name=del_username]').options[document.querySelector('[name=del_username]').selectedIndex].text + '?');">
          <input type="hidden" name="action" value="delete">
          <div class="mb-3">
            <label class="form-label">Select User</label>
            <select name="del_username" class="form-select">{user_options}</select>
          </div>
          <div class="text-center">
            <button type="submit" class="btn btn-danger">Delete User</button>
          </div>
          <p class="mt-2 text-success">{delete_message}</p>
        </form>
      </div>

    </div>
    {home_button}
    """
    return render_template_string(layout, content=manage_users_form)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)